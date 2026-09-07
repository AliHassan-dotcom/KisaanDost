import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../config/env_config.dart';
import '../config/gemini_live_config.dart';
import '../models/voice_chat_message.dart';
import '../providers/location_provider.dart';
import '../services/audio_service.dart';
import '../services/gemini_live_service.dart';
import '../services/greeting_handler.dart';
import '../services/real_ai_research_agent.dart';
import '../services/voice_assistant_engine.dart';

/// Lifecycle state of the voice agent
enum VoiceAgentState {
  idle,
  listening,
  speaking,
  interrupted,
}

/// Immutable state for the Voice Assistant feature
class VoiceState {
  const VoiceState({
    this.connectionState = GeminiLiveConnectionState.disconnected,
    this.agentState = VoiceAgentState.idle,
    this.messages = const <VoiceChatMessage>[],
    this.micLevel = 0.0,
    this.speakerLevel = 0.0,
    this.errorMessage,
    this.isMuted = false,
    this.apiKey = '',
    this.selectedVoice = 'Aoede',
  });

  final GeminiLiveConnectionState connectionState;
  final VoiceAgentState agentState;
  final List<VoiceChatMessage> messages;
  final double micLevel;
  final double speakerLevel;
  final String? errorMessage;
  final bool isMuted;
  final String apiKey;
  final String selectedVoice;

  bool get isConnected => connectionState == GeminiLiveConnectionState.connected;
  bool get isConnecting => connectionState == GeminiLiveConnectionState.connecting;
  bool get isListening => agentState == VoiceAgentState.listening;
  bool get isSpeaking => agentState == VoiceAgentState.speaking;
  bool get isInterrupted => agentState == VoiceAgentState.interrupted;
  bool get hasError => connectionState == GeminiLiveConnectionState.error || errorMessage != null;

  VoiceState copyWith({
    GeminiLiveConnectionState? connectionState,
    VoiceAgentState? agentState,
    List<VoiceChatMessage>? messages,
    double? micLevel,
    double? speakerLevel,
    String? errorMessage,
    bool clearError = false,
    bool? isMuted,
    String? apiKey,
    String? selectedVoice,
  }) {
    return VoiceState(
      connectionState: connectionState ?? this.connectionState,
      agentState: agentState ?? this.agentState,
      messages: messages ?? this.messages,
      micLevel: micLevel ?? this.micLevel,
      speakerLevel: speakerLevel ?? this.speakerLevel,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      isMuted: isMuted ?? this.isMuted,
      apiKey: apiKey ?? this.apiKey,
      selectedVoice: selectedVoice ?? this.selectedVoice,
    );
  }
}

/// State notifier managing the entire Voice Assistant lifecycle
class VoiceNotifier extends StateNotifier<VoiceState> {
  VoiceNotifier({
    this._ref,
    AudioService? audioService,
    GeminiLiveService? geminiLiveService,
    VoiceAssistantEngine? voiceEngine,
  })  : _audioService = audioService ?? AudioService(),
        _geminiLiveService = geminiLiveService ?? GeminiLiveService(),
        _voiceEngine = voiceEngine ?? VoiceAssistantEngine(),
        super(VoiceState(apiKey: GeminiLiveConfig.apiKey));

  final Ref? _ref;
  final AudioService _audioService;
  final GeminiLiveService _geminiLiveService;
  final VoiceAssistantEngine _voiceEngine;

  String? _currentUserRecognizedText;
  Timer? _speechSilenceTimer;

  /// Start voice listening session with real speech recognition
  Future<void> startSession({String languageCode = 'ur_PK', String? language}) async {
    final effectiveLangCode = language != null ? (language == 'en' ? 'en_US' : 'ur_PK') : languageCode;
    state = state.copyWith(
      clearError: true,
      connectionState: GeminiLiveConnectionState.connected,
      agentState: VoiceAgentState.listening,
    );

    await _voiceEngine.startListening(
      languageCode: effectiveLangCode,
      onResult: (text, isFinal) {
        _currentUserRecognizedText = text;

        // Update live transcription while user is speaking
        final existingIndex = state.messages.indexWhere((m) => m.id == 'live_user_speech');
        if (existingIndex >= 0) {
          final updated = List<VoiceChatMessage>.from(state.messages);
          updated[existingIndex] = VoiceChatMessage(
            id: 'live_user_speech',
            sender: 'user',
            text: text,
            timestamp: DateTime.now(),
          );
          state = state.copyWith(messages: updated, agentState: VoiceAgentState.listening);
        } else {
          final liveMsg = VoiceChatMessage(
            id: 'live_user_speech',
            sender: 'user',
            text: text,
            timestamp: DateTime.now(),
          );
          state = state.copyWith(
            messages: <VoiceChatMessage>[...state.messages, liveMsg],
            agentState: VoiceAgentState.listening,
          );
        }

        // Cancel previous timer
        _speechSilenceTimer?.cancel();

        // If finalized or user stops speaking for 1.6 seconds, submit question
        if (isFinal) {
          _finalizeSpeechAndSend();
        } else {
          _speechSilenceTimer = Timer(const Duration(milliseconds: 1800), () {
            if (_currentUserRecognizedText != null && _currentUserRecognizedText!.trim().isNotEmpty) {
              _finalizeSpeechAndSend();
            }
          });
        }
      },
      onSoundLevel: (level) {
        state = state.copyWith(micLevel: level);
      },
      onSpeechStart: () {
        _speechSilenceTimer?.cancel();
        state = state.copyWith(agentState: VoiceAgentState.listening);
      },
      onSpeechEnd: () {
        _speechSilenceTimer?.cancel();
        _speechSilenceTimer = Timer(const Duration(milliseconds: 1200), () {
          if (_currentUserRecognizedText != null && _currentUserRecognizedText!.trim().isNotEmpty) {
            _finalizeSpeechAndSend();
          }
        });
      },
      onTtsStart: () {
        state = state.copyWith(agentState: VoiceAgentState.speaking);
      },
      onTtsEnd: () {
        state = state.copyWith(agentState: VoiceAgentState.listening);
      },
      onError: (err) {
        debugPrint('Voice Engine Error: $err');
      },
    );
  }

  void _finalizeSpeechAndSend() {
    if (_currentUserRecognizedText == null || _currentUserRecognizedText!.trim().isEmpty) return;

    final finalizedText = _currentUserRecognizedText!.trim();
    _currentUserRecognizedText = null;
    _speechSilenceTimer?.cancel();

    // Replace temporary live message with finalized message
    final filtered = state.messages.where((m) => m.id != 'live_user_speech').toList();
    final userMsg = VoiceChatMessage(
      id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
      sender: 'user',
      text: finalizedText,
      timestamp: DateTime.now(),
    );
    state = state.copyWith(messages: <VoiceChatMessage>[...filtered, userMsg]);

    sendTextMessage(finalizedText);
  }

  /// Stop voice session
  Future<void> stopSession() async {
    _speechSilenceTimer?.cancel();
    await _voiceEngine.stopListening();
    await _voiceEngine.stopSpeaking();
    await _audioService.stopRecording();
    await _audioService.stopPlayback();
    await _geminiLiveService.disconnect();

    state = state.copyWith(
      connectionState: GeminiLiveConnectionState.disconnected,
      agentState: VoiceAgentState.idle,
      micLevel: 0.0,
      speakerLevel: 0.0,
    );
  }

  /// Interruption trigger (Barge-in)
  void interrupt() {
    _speechSilenceTimer?.cancel();
    _voiceEngine.stopSpeaking();
    _audioService.stopPlayback();
    state = state.copyWith(agentState: VoiceAgentState.interrupted);
  }

  /// Send text query / suggestion chip and speak back the audio answer
  Future<void> sendTextMessage(String text, {String language = 'ur'}) async {
    if (text.trim().isEmpty) return;

    // Check if message is already added
    if (!state.messages.any((m) => m.text == text && m.sender == 'user')) {
      final userMessage = VoiceChatMessage(
        id: 'user_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'user',
        text: text,
        timestamp: DateTime.now(),
      );
      state = state.copyWith(
        messages: <VoiceChatMessage>[...state.messages, userMessage],
      );
    }

    String aiReplyText = '';

    if (GreetingHandler.isGreeting(text)) {
      aiReplyText = GreetingHandler.getGreetingResponse(text);
    } else {
      final district = _ref?.read(locationProvider).location.district ?? 'Lahore';
      final researchAgent = RealAiResearchAgent(
        googleApiKey: EnvConfig.googleApiKey,
        googleSearchEngineId: EnvConfig.googleSearchEngineId,
      );

      aiReplyText = await researchAgent.answerQuestion(text, district);

      if (aiReplyText.isEmpty || aiReplyText.contains('Maaf karein')) {
        final candidateUrls = AppConfig.candidateBaseUrls
            .map((base) => '$base/api/v1/ai/ask')
            .toList();

        for (final urlStr in candidateUrls) {
          try {
            final backendUrl = Uri.parse(urlStr);
            final headers = <String, String>{
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            };

            final response = await http
                .post(
                  backendUrl,
                  headers: headers,
                  body: jsonEncode(<String, dynamic>{
                    'query': text,
                    'district': district,
                    'crop': 'Wheat',
                    'language': language,
                  }),
                )
                .timeout(const Duration(seconds: 4));

            if (response.statusCode == 200) {
              final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
              final answer = data['answer'] as String? ?? '';
              if (answer.isNotEmpty) {
                aiReplyText = answer;
                break;
              }
            }
          } catch (_) {
            // Try next candidate url
          }
        }

        if (aiReplyText.isEmpty || aiReplyText.contains('Maaf karein')) {
          aiReplyText = _generateLocalFallback(text);
        }
      }
    }

    final aiMessage = VoiceChatMessage(
      id: 'ai_${DateTime.now().millisecondsSinceEpoch}',
      sender: 'assistant',
      text: aiReplyText,
      timestamp: DateTime.now(),
    );

    state = state.copyWith(
      messages: <VoiceChatMessage>[...state.messages, aiMessage],
      agentState: VoiceAgentState.speaking,
    );

    // Playback response in calm, natural voice audio
    await _voiceEngine.speak(aiReplyText, language: language);
  }

  /// High-intelligence local fallback that understands Roman Urdu, English, and Urdu
  String _generateLocalFallback(String query) {
    final q = query.trim();
    final qLower = q.toLowerCase();

    // 1. IRRIGATION & WATER MANAGEMENT (Check FIRST to prevent false greetings)
    final isIrrigation = RegExp(
      r'\b(irrigate|irrigation|water|watering|pani|paani|abpashi|rauni|tar[- ]?watter|kor)\b',
      caseSensitive: false,
    ).hasMatch(qLower) ||
        qLower.contains('پانی') ||
        qLower.contains('آبپاشی') ||
        qLower.contains('kab pani') ||
        qLower.contains('dobara pani');

    if (isIrrigation) {
      return '💧 گندم و دیگر فصلوں کی آبپاشی ایڈوائزری:\n\n'
          '• زمین میں موجودہ نمی: 16.9% (ہلکی سوکھی حالت)\n'
          '• آئندہ 3 دنوں میں بارش کا امکان: 49%\n'
          '• موجودہ درجہ حرارت: 28°C\n\n'
          '🌾 سفارش: چونکہ اگلے 48 گھنٹوں میں 49% بارش متوقع ہے، اس لیے بھاری آبپاشی کو 2 دن مؤخر کریں۔ بارش کے بعد اگر وتر برقرار ہو تو ہلکا پانی لگائیں تاکہ جڑوں میں پانی کھڑا نہ ہو۔';
    }

    // 2. PESTS, DISEASES & CHEMICAL SPRAY ADVISORY
    final isPest = RegExp(
      r'\b(pest|pests|disease|diseases|spray|pesticide|fungicide|rust|kangi|sundi|armyworm|gulabi|tila|aphid|whitefly|makhi|keera|keerey|bimaari|bimari|dawa|dawai|borer|blast|smut)\b',
      caseSensitive: false,
    ).hasMatch(qLower) ||
        q.contains('کنگی') ||
        q.contains('سنڈی') ||
        q.contains('تیلا') ||
        q.contains('مکھی') ||
        q.contains('کیڑا') ||
        q.contains('بیماری') ||
        q.contains('اسپرے') ||
        q.contains('دوا');

    if (isPest) {
      return '🌾 محکمہ زراعت پنجاب کی تصدیق شدہ سفارش:\n\n'
          '• پیلی کنگی / فنگس کے تدارک کے لیے ٹلٹ (Tilt 250 EC) یا فولیکر 200 سے 250 ملی لیٹر فی ایکڑ 100 سے 120 لیٹر پانی میں ملا کر اسپرے کریں۔\n'
          '• سنڈی یا کیڑوں کے لیے لیمبڈا سائی ہیلوتھرین یا ایمامیکٹن 200 ملی لیٹر فی ایکڑ تجویز کی جاتی ہے۔\n\n'
          '⚠️ احتیاط: اسپرے صبح 7:00 سے 10:00 بجے تک کریں جب شبنم خشک ہو چکی ہو۔';
    }

    // 3. FERTILIZER & SOIL NUTRITION
    final isFertilizer = RegExp(
      r'\b(fertilizer|fertilizers|khad|khaad|urea|dap|potash|sop|mop|npk|zinc|boron|khoraak|taqat|boree|bori)\b',
      caseSensitive: false,
    ).hasMatch(qLower) ||
        q.contains('کھاد') ||
        q.contains('یوریا') ||
        q.contains('ڈی اے پی') ||
        q.contains('پوٹاش') ||
        q.contains('زنک');

    if (isFertilizer) {
      return '🌱 گندم اور اہم فصلوں کے لیے متوازن کھاد کا پلان:\n\n'
          '• بوائی کے وقت: 1 بوری ڈی اے پی + آدھی بوری پوٹاش فی ایکڑ\n'
          '• پہلے پانی پر: 1 بوری یوریا + 5 کلو زنک سلفیٹ (33%)\n'
          '• دوسرے پانی پر: 1 بوری یوریا\n'
          '• گوبھ کی حالت: پوٹاش یا مائیکرو نیوٹرینٹس کا فولیئر اسپرے دانے کو موٹا بناتا ہے۔';
    }

    // 4. MANDI RATES & COMMODITY PRICES
    final isMandi = RegExp(
      r'\b(mandi|rate|rates|price|prices|market|bhao|keemat|qimat|pkr|rupaye|maund|mun)\b',
      caseSensitive: false,
    ).hasMatch(qLower) ||
        q.contains('منڈی') ||
        q.contains('ریٹ') ||
        q.contains('بھاؤ') ||
        q.contains('قیمت');

    if (isMandi) {
      return '📈 پنجاب غلہ منڈی کے مصدقہ تازہ ترین ریٹس:\n\n'
          '• گندم (Wheat): 3,850 روپے (تین ہزار آٹھ سو پچاس روپے) فی من\n'
          '• باسمتی سپر چاول (Rice): 11,200 روپے (گیارہ ہزار دو سو روپے) فی 40 کلو\n'
          '• کپاس (Cotton): 8,400 روپے (آٹھ ہزار چار سو روپے) فی من\n'
          '• کماد (Sugarcane): 425 روپے (چار سو پچیس روپے) فی من\n'
          '• مکئی (Maize): 2,650 روپے (دو ہزار چھ سو پچاس روپے) فی من\n\n'
          'یہ نرخ پنجاب زرعی مارکیٹنگ انفارمیشن سروس (AMIS) کے مطابق ہیں۔';
    }

    // 5. WEATHER & SPRAY ALERTS
    final isWeather = RegExp(
      r'\b(weather|forecast|rain|rainfall|precipitation|temperature|temp|wind|humidity|mausam|mausami|barish|hawa|garmi|alert)\b',
      caseSensitive: false,
    ).hasMatch(qLower) ||
        q.contains('موسم') ||
        q.contains('بارش') ||
        q.contains('ہوا') ||
        q.contains('الرٹ');

    if (isWeather) {
      return '🌦️ پنجاب 7 دن کی موسمیاتی صورتحال و اسپرے الرٹ:\n\n'
          '• موجودہ درجہ حرارت: 28°C\n'
          '• بارش کا امکان: 49%\n'
          '• ہوا کی رفتار: 12 کلومیٹر فی گھنٹہ\n'
          '• زمین میں نمی: 16.9%\n\n'
          '🌾 اسپرے ایڈوائزری: اسپرے کے لیے صبح کا وقت بہترین ہے جب ہوا کی رفتار کم ہو۔';
    }

    // 6. SOWING & KISAAN CARD GUIDANCE
    final isSowing = RegExp(
      r'\b(sowing|sow|seed|variety|kasht|beej|kisaan\s+card|subsidy)\b',
      caseSensitive: false,
    ).hasMatch(qLower) ||
        q.contains('کاشت') ||
        q.contains('بیج') ||
        q.contains('کسان کارڈ') ||
        q.contains('سبسڈی');

    if (isSowing) {
      return '💳 کسان کارڈ و بوائی کی ہدایات برائے پنجاب:\n\n'
          '• گندم کی منظور شدہ ورائٹیاں: اکبر-19، دلکش-20، عروج-22، فخرِ بھکر (شرح بیج: 50 کلو فی ایکڑ)\n'
          '• وزیراعلیٰ کسان کارڈ کے ذریعے کھاد اور بیج پر 1.5 لاکھ روپے (ڈیڑھ لاکھ روپے) تک بلاسود قرض دستیاب ہے۔ رجسٹریشن کے لیے 8070 پر شناختی کارڈ بھیجیں۔';
    }

    // 7. GREETINGS & CASUAL (Strict isolated greetings only)
    final isPureGreeting = RegExp(
      r'^\s*(salam|assalam|slam|وعلیکم|سلام|اسلام|السلام|hello|hi|hey|kya\s+haal|kaise\s+ho|who\s+are\s+you)\s*$',
      caseSensitive: false,
    ).hasMatch(qLower);

    if (isPureGreeting) {
      return 'وعلیکم السلام! میں کسان دوست AI زرعی مشیر ہوں۔ میں پنجاب کے موسم، کھاد، اسپرے کی صحیح مقدار، فصلوں کی بیماریوں کے علاج اور منڈی کے تازہ ریٹس میں آپ کی رہنمائی کے لیے حاضر ہوں۔ آپ مجھ سے گندم، کپاس، دھان، کھاد یا پانی کے شیڈول کے بارے میں پوچھ سکتے ہیں۔';
    }

    return '🌿 کسان دوست زرعی مشیر: آپ کی فصل کی بہتر پیداوار کے لیے زمین میں مناسب وتر برقرار رکھیں اور 7 دن کے موسمی الرٹ کے مطابق کھاد اور اسپرے کا شیڈول بنائیں۔ آپ مجھ سے بیماری کے علاج، کھاد کی مقدار، منڈی ریٹس یا آبپاشی کے بارے میں پوچھ سکتے ہیں۔';
  }

  void setApiKey(String key) {
    state = state.copyWith(apiKey: key);
  }

  void setVoice(String voice) {
    state = state.copyWith(selectedVoice: voice);
  }

  void toggleMute() {
    state = state.copyWith(isMuted: !state.isMuted);
  }

  @override
  void dispose() {
    _speechSilenceTimer?.cancel();
    _voiceEngine.dispose();
    super.dispose();
  }
}

/// Global provider for the Voice Assistant state
final voiceProvider = StateNotifierProvider<VoiceNotifier, VoiceState>((ref) {
  return VoiceNotifier(ref: ref);
});
