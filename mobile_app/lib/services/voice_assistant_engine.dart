import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Robust Native Voice Assistant Engine managing:
/// 1. Real-time Speech-to-Text (STT) via device microphone
/// 2. Natural Text-to-Speech (TTS) audio response playback with calm, human cadence
/// 3. Instant Barge-in / Interruption handling
class VoiceAssistantEngine {
  VoiceAssistantEngine() {
    _initTts();
  }

  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();

  bool _isSpeechInitialized = false;
  bool _isListening = false;
  bool _isSpeaking = false;

  // Callbacks
  Function(String text, bool isFinal)? _onSpeechRecognized;
  Function(double level)? _onSoundLevelChange;
  VoidCallback? _onSpeechStart;
  VoidCallback? _onSpeechEnd;
  VoidCallback? _onTtsStart;
  VoidCallback? _onTtsEnd;
  Function(String error)? _onError;

  bool get isListening => _isListening;
  bool get isSpeaking => _isSpeaking;

  Future<void> _initTts() async {
    try {
      await _tts.setLanguage('ur-PK');
      // 0.45 is slow, clear, natural human pace
      await _tts.setSpeechRate(0.45);
      await _tts.setVolume(1.0);
      await _tts.setPitch(0.9);

      // Attempt to pick optimal Urdu voice if available on Android
      try {
        final voices = await _tts.getVoices;
        if (voices is List) {
          for (final voice in voices) {
            if (voice is Map) {
              final name = (voice['name'] ?? '').toString().toLowerCase();
              final locale = (voice['locale'] ?? '').toString().toLowerCase();
              if (locale.contains('ur') || name.contains('ur-pk')) {
                await _tts.setVoice(<String, String>{
                  'name': voice['name'].toString(),
                  'locale': voice['locale'].toString(),
                });
                break;
              }
            }
          }
        }
      } catch (_) {}

      _tts.setStartHandler(() {
        _isSpeaking = true;
        _onTtsStart?.call();
      });

      _tts.setCompletionHandler(() {
        _isSpeaking = false;
        _onTtsEnd?.call();
      });

      _tts.setErrorHandler((msg) {
        _isSpeaking = false;
        _onTtsEnd?.call();
      });
    } catch (e) {
      debugPrint('TTS Init error: $e');
    }
  }

  Future<bool> initializeSpeech() async {
    if (_isSpeechInitialized) return true;
    try {
      _isSpeechInitialized = await _speech.initialize(
        onError: (err) {
          debugPrint('STT Error: ${err.errorMsg}');
          _isListening = false;
          _onSpeechEnd?.call();
        },
        onStatus: (status) {
          debugPrint('STT Status: $status');
          if (status == 'done' || status == 'notListening') {
            _isListening = false;
            _onSpeechEnd?.call();
          }
        },
      );
      return _isSpeechInitialized;
    } catch (e) {
      debugPrint('Speech init failed: $e');
      return false;
    }
  }

  /// Start active voice listening from the farmer
  Future<void> startListening({
    required Function(String text, bool isFinal) onResult,
    Function(double level)? onSoundLevel,
    VoidCallback? onSpeechStart,
    VoidCallback? onSpeechEnd,
    VoidCallback? onTtsStart,
    VoidCallback? onTtsEnd,
    Function(String error)? onError,
    String languageCode = 'ur_PK',
  }) async {
    _onSpeechRecognized = onResult;
    _onSoundLevelChange = onSoundLevel;
    _onSpeechStart = onSpeechStart;
    _onSpeechEnd = onSpeechEnd;
    _onTtsStart = onTtsStart;
    _onTtsEnd = onTtsEnd;
    _onError = onError;

    // Stop TTS if speaking (Barge-in)
    await stopSpeaking();

    final available = await initializeSpeech();
    if (!available) {
      _onError?.call('Microphone speech recognition not available or permission denied.');
      return;
    }

    try {
      _isListening = true;
      _onSpeechStart?.call();

      await _speech.listen(
        onResult: (result) {
          final recognized = result.recognizedWords;
          final isFinal = result.finalResult;
          if (recognized.isNotEmpty) {
            _onSpeechRecognized?.call(recognized, isFinal);
          }
        },
        onSoundLevelChange: (level) {
          _onSoundLevelChange?.call(level.clamp(0.0, 1.0));
        },
        listenOptions: stt.SpeechListenOptions(
          listenMode: stt.ListenMode.dictation,
          cancelOnError: false,
          partialResults: true,
          localeId: languageCode,
        ),
      );
    } catch (e) {
      _isListening = false;
      _onError?.call('Error listening to microphone: $e');
    }
  }

  /// Stop microphone listening
  Future<void> stopListening() async {
    if (_isListening) {
      _isListening = false;
      await _speech.stop();
      _onSpeechEnd?.call();
    }
  }

  /// Speaks the response out loud in natural voice audio
  Future<void> speak(String text, {String language = 'ur'}) async {
    if (text.isEmpty) return;

    final cleanText = humanizeForSpeech(text);

    try {
      _isSpeaking = true;
      _onTtsStart?.call();

      if (language == 'ur' || RegExp(r'[\u0600-\u06FF]').hasMatch(cleanText)) {
        try {
          await _tts.setLanguage('ur-PK');
        } catch (_) {
          try {
            await _tts.setLanguage('ur');
          } catch (_) {}
        }
      } else {
        await _tts.setLanguage('en-US');
      }
      await _tts.setSpeechRate(0.48); // Natural, clear conversational cadence
      await _tts.setPitch(1.0); // Warm, authentic tone
      await _tts.speak(cleanText);
    } catch (e) {
      debugPrint('TTS Speak error: $e');
      _isSpeaking = false;
      _onTtsEnd?.call();
    }
  }

  static const Map<int, String> _urduDigits = <int, String>{
    0: 'صفر', 1: 'ایک', 2: 'دو', 3: 'تین', 4: 'چار', 5: 'پانچ',
    6: 'چھ', 7: 'سات', 8: 'آٹھ', 9: 'نو', 10: 'دس',
    11: 'گیارہ', 12: 'بارہ', 13: 'تیرہ', 14: 'چودہ', 15: 'پندرہ',
    16: 'سولہ', 17: 'سترہ', 18: 'اٹھارہ', 19: 'انیس', 20: 'بیس',
    21: 'اکیس', 22: 'بائیس', 23: 'تئیس', 24: 'چوبیس', 25: 'پچیس',
    26: 'چھبیس', 27: 'ستائیس', 28: 'اٹھائیس', 29: 'انتیس', 30: 'تیس',
    31: 'اکتیس', 32: 'بتیس', 33: 'تینتیس', 34: 'چونتیس', 35: 'پینتیس',
    36: 'چھتیس', 37: 'سینتیس', 38: 'اڑتیس', 39: 'انتالیس', 40: 'چالیس',
    41: 'اکتالیس', 42: 'بیالیس', 43: 'تینتالیس', 44: 'چوالیس', 45: 'پینتالیس',
    46: 'چھیاستھ', 47: 'سینتالیس', 48: 'اڑتالیس', 49: 'انچاس', 50: 'پچاس',
    51: 'اکیاون', 52: 'باون', 53: 'ترپن', 54: 'چون', 55: 'پچپن',
    56: 'چھپن', 57: 'ستاون', 58: 'اٹھاون', 59: 'انسٹھ', 60: 'ساٹھ',
    61: 'اکسٹھ', 62: 'باسٹھ', 63: 'تریسٹھ', 64: 'چونسٹھ', 65: 'پینسٹھ',
    66: 'چھیاسٹھ', 67: 'سڑسٹھ', 68: 'اڑسٹھ', 69: 'انہتر', 70: 'ستر',
    71: 'اکہتر', 72: 'بہتر', 73: 'تہتر', 74: 'چوہتر', 75: 'پچہتر',
    76: 'چھہتر', 77: 'ستتر', 78: 'اٹھہتر', 79: 'اناسی', 80: 'اسی',
    81: 'اکیاسی', 82: 'بیاسی', 83: 'تراسی', 84: 'چوراسی', 85: 'پچاسی',
    86: 'چھیاسی', 87: 'ستاسی', 88: 'اٹھاسی', 89: 'نواسی', 90: 'نوے',
    91: 'اکانوے', 92: 'بانوے', 93: 'ترانوے', 94: 'چورانوے', 95: 'پچانوے',
    96: 'سیانوے', 97: 'ستانوے', 98: 'اٹھانوے', 99: 'ننانوے'
  };

  /// Converts any integer into natural Urdu words
  static String numberToUrduWords(int n) {
    if (n < 0) return 'منفی ${numberToUrduWords(-n)}';
    if (n < 100) return _urduDigits[n] ?? '$n';
    if (n < 1000) {
      final h = n ~/ 100;
      final rem = n % 100;
      final hText = (h == 1 ? 'ایک سو' : '${_urduDigits[h] ?? '$h'} سو');
      return rem == 0 ? hText : '$hText ${numberToUrduWords(rem)}';
    }
    if (n < 100000) {
      final th = n ~/ 1000;
      final rem = n % 1000;
      final thText = '${numberToUrduWords(th)} ہزار';
      return rem == 0 ? thText : '$thText ${numberToUrduWords(rem)}';
    }
    if (n < 10000000) {
      final lk = n ~/ 100000;
      final rem = n % 100000;
      final lkText = '${numberToUrduWords(lk)} لاکھ';
      return rem == 0 ? lkText : '$lkText ${numberToUrduWords(rem)}';
    }
    final cr = n ~/ 10000000;
    final rem = n % 10000000;
    final crText = '${numberToUrduWords(cr)} کروڑ';
    return rem == 0 ? crText : '$crText ${numberToUrduWords(rem)}';
  }

  static final Map<String, String> _urduPhoneticMap = <String, String>{
    'tilt': 'ٹلٹ',
    'folicur': 'فولیکر',
    'nativo': 'نیٹیوو',
    'score': 'اسکور',
    'polo': 'پولو',
    'belt': 'بیلٹ',
    'proclaim': 'پروکلیم',
    'propiconazole': 'پروپیکونازول',
    'tebuconazole': 'ٹیبوکونازول',
    'chlorpyrifos': 'کلورپائریفوس',
    'lambda-cyhalothrin': 'لیمبڈا سائی ہیلوتھرین',
    'lambda': 'لیمبڈا',
    'cyhalothrin': 'سائی ہیلوتھرین',
    'emamectin benzoate': 'ایمامیکٹن بینزوئیٹ',
    'emamectin': 'ایمامیکٹن',
    'diafenthiuron': 'ڈائیفینتھیوران',
    'pyriproxyfen': 'پائری پروکسی فن',
    'flubendiamide': 'فلو بینڈیامائیڈ',
    'wheat': 'گندم',
    'cotton': 'کپاس',
    'rice': 'دھان',
    'sugarcane': 'کماد',
    'maize': 'مکئی',
    'potato': 'آلو',
    'tomato': 'ٹماٹر',
    'yellow rust': 'پیلی کنگی',
    'brown rust': 'بھوری کنگی',
    'rust': 'کنگی',
    'armyworm': 'لشکری سنڈی',
    'bollworm': 'گلابی سنڈی',
    'whitefly': 'سفید مکھی',
    'aphid': 'تیلا',
    'jassid': 'چست تیلا',
    'thrips': 'تھرپس',
    'borer': 'بورر',
    'top borer': 'ٹاپ بورر',
    'stem borer': 'تنے کا بورر',
    'pyrilla': 'پائریلا',
    'dap': 'ڈی اے پی',
    'sop': 'ایس او پی',
    'mop': 'ایم او پی',
    'npk': 'این پی کے',
    'urea': 'یوریا',
    'zinc': 'زنک',
    'boron': 'بوران',
    'amis': 'پنجاب زرعی مارکیٹ',
    'sentinel': 'سیٹلائٹ',
    'moisture': 'نمی',
    'ec': 'ای سی',
    'sc': 'ایس سی',
    'wg': 'ڈبلیو جی',
    'wp': 'ڈبلیو پی',
    'sl': 'ایس ایل',
    'ml': 'ملی لیٹر',
    'kg': 'کلوگرام',
    'liters': 'لیٹر',
    'liter': 'لیٹر',
    'acre': 'ایکڑ',
    'lahore': 'لاہور',
    'faisalabad': 'فیصل آباد',
    'multan': 'ملتان',
    'sahiwal': 'ساہیوال',
    'gujranwala': 'گوجرانوالہ',
    'rawalpindi': 'راولپنڈی',
    'bahawalpur': 'بہاولپور',
    'sargodha': 'سرگودھا',
    'rahim yar khan': 'رحیم یار خان',
  };

  /// Converts formatted texts, numbers, and symbols into fluent natural spoken Urdu
  static String humanizeForSpeech(String input) {
    var s = input;

    // 1. Remove commas inside numbers (e.g. 11,200 -> 11200)
    s = s.replaceAllMapped(RegExp(r'(\d+),(\d+)'), (m) => '${m[1]}${m[2]}');

    // 2. Separate attached digits and units/letters (e.g. 200ml -> 200 ml, 40kg -> 40 kg, 28°C -> 28 °C, 49% -> 49 %)
    s = s.replaceAllMapped(RegExp(r'(\d+)([a-zA-Z°%]+)'), (m) => '${m[1]} ${m[2]}');
    s = s.replaceAllMapped(RegExp(r'([a-zA-Z]+)(\d+)'), (m) => '${m[1]} ${m[2]}');

    // 3. Normalize currency & unit symbols
    s = s.replaceAll(RegExp(r'(\$|USD|dollar|dollars)', caseSensitive: false), ' روپے ')
        .replaceAll(RegExp(r'(PKR|Rs\.?|₨)', caseSensitive: false), ' روپے ')
        .replaceAll('°C', ' ڈگری سینٹی گریڈ ')
        .replaceAll('°', ' ڈگری ')
        .replaceAll('%', ' فیصد ');

    // 3. Transliterate English chemical, crop, and agricultural terms to pure Urdu
    for (final entry in _urduPhoneticMap.entries) {
      s = s.replaceAll(
        RegExp(r'\b' + RegExp.escape(entry.key) + r'\b', caseSensitive: false),
        ' ${entry.value} ',
      );
    }

    // 4. Convert ranges like 100-120 -> 100 سے 120
    s = s.replaceAllMapped(RegExp(r'(\d+)\s*-\s*(\d+)'), (m) => '${m[1]} سے ${m[2]}');

    // 5. Convert decimals like 16.9 or 1.5 -> 16 اعشاریہ 9
    s = s.replaceAllMapped(RegExp(r'(\d+)\.(\d+)'), (m) {
      final whole = int.tryParse(m[1]!) ?? 0;
      final dec = int.tryParse(m[2]!) ?? 0;
      return '${numberToUrduWords(whole)} اعشاریہ ${numberToUrduWords(dec)}';
    });

    // 6. Convert all standalone integers to Urdu words
    s = s.replaceAllMapped(RegExp(r'\b\d+\b'), (m) {
      final val = int.tryParse(m[0]!);
      if (val != null) {
        return numberToUrduWords(val);
      }
      return m[0]!;
    });

    // 7. Clean markdown characters, leftover English letters, and extra punctuation
    s = s.replaceAll(RegExp(r'[a-zA-Z]'), ' ')
        .replaceAll(RegExp(r'[*#_`•\-\[\]\(\)/:;،]'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();

    return s;
  }

  /// Stop speaking audio immediately (Instant Barge-in)
  Future<void> stopSpeaking() async {
    if (_isSpeaking) {
      _isSpeaking = false;
      await _tts.stop();
      _onTtsEnd?.call();
    }
  }

  void dispose() {
    _speech.stop();
    _tts.stop();
  }
}
