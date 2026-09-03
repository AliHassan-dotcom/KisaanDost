import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Robust Native Voice Assistant Engine managing:
/// 1. Real-time Speech-to-Text (STT) via device microphone
/// 2. Real-time Text-to-Speech (TTS) audio response playback
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
      await _tts.setSpeechRate(0.5);
      await _tts.setVolume(1.0);
      await _tts.setPitch(1.0);

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

  /// Speak the response out loud in voice audio
  Future<void> speak(String text, {String language = 'ur'}) async {
    if (text.isEmpty) return;

    // Clean markdown symbols (like **, ##, etc.) for clear natural pronunciation
    final cleanText = text
        .replaceAll(RegExp(r'[*#_`•\-\[\]\(\)]'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();

    try {
      _isSpeaking = true;
      _onTtsStart?.call();

      final langCode = language == 'ur' ? 'ur-PK' : 'en-US';
      await _tts.setLanguage(langCode);
      await _tts.speak(cleanText);
    } catch (e) {
      debugPrint('TTS Speak error: $e');
      _isSpeaking = false;
      _onTtsEnd?.call();
    }
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
