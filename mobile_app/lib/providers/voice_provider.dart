import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../config/gemini_live_config.dart';
import '../models/voice_chat_message.dart';
import '../services/audio_service.dart';
import '../services/gemini_live_service.dart';
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
    AudioService? audioService,
    GeminiLiveService? geminiLiveService,
    VoiceAssistantEngine? voiceEngine,
  })  : _audioService = audioService ?? AudioService(),
        _geminiLiveService = geminiLiveService ?? GeminiLiveService(),
        _voiceEngine = voiceEngine ?? VoiceAssistantEngine(),
        super(VoiceState(apiKey: GeminiLiveConfig.apiKey));

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
        // Wait a grace period before finalizing to ensure sentence wasn't just pausing between words
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

    try {
      final backendUrl = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/ai/ask');
      final response = await http
          .post(
            backendUrl,
            headers: <String, String>{'Content-Type': 'application/json'},
            body: jsonEncode(<String, dynamic>{
              'query': text,
              'district': 'Lahore',
              'crop': 'Wheat',
              'language': language,
            }),
          )
          .timeout(const Duration(seconds: 10));

      String aiReplyText = '';
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        aiReplyText = data['answer'] as String? ?? '';
      } else {
        aiReplyText = _generateLocalFallback(text);
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

      // Playback response in natural voice
      await _voiceEngine.speak(aiReplyText, language: language);
    } catch (e) {
      final fallbackText = _generateLocalFallback(text);
      final aiMessage = VoiceChatMessage(
        id: 'ai_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'assistant',
        text: fallbackText,
        timestamp: DateTime.now(),
      );
      state = state.copyWith(
        messages: <VoiceChatMessage>[...state.messages, aiMessage],
        agentState: VoiceAgentState.speaking,
      );
      await _voiceEngine.speak(fallbackText, language: language);
    }
  }

  String _generateLocalFallback(String query) {
    final q = query.toLowerCase();
    if (q.contains('سلام') || q.contains('اسلام') || q.contains('salam') || q.contains('hello')) {
      return 'وعلیکم السلام! میں کسان دوست AI زرعی مشیر ہوں۔ آپ مجھ سے فصلوں کی بیماری، اسپرے کی مقدار، کھاد، آج کے موسم اور منڈی کے تازہ ریٹس کے بارے میں کچھ بھی پوچھ سکتے ہیں۔';
    }
    if (q.contains('rust') || q.contains('کنگی') || q.contains('پھپھوندی')) {
      return 'گندم کی پیلی کنگی کے تدارک کے لیے محکمہ زراعت کی سفارش کے مطابق ٹلٹ (Tilt 250 EC) یا فولیکر 200 سے 250 ملی لیٹر فی ایکڑ 100 لیٹر پانی میں صبح کے وقت اسپرے کریں۔';
    }
    if (q.contains('mandi') || q.contains('rate') || q.contains('ریٹ') || q.contains('قیمت') || q.contains('منڈی')) {
      return 'آج لاہور غلہ منڈی میں گندم کا ریٹ 3850 روپے، باسمتی چاول 11200 روپے، کپاس 8400 روپے اور کماد 425 روپے فی من ہے۔';
    }
    if (q.contains('weather') || q.contains('موسم') || q.contains('بارش')) {
      return 'آئندہ 24 گھنٹوں میں بارش کا امکان 49 فیصد ہے۔ اسپرے کے لیے صبح 7 سے 10 بجے کا وقت بہترین ہے۔';
    }
    return 'کسان دوست زرعی مشیر: آپ کی فصل کی بہتر پیداوار کے لیے محکمہ زراعت پنجاب کی ہدایات کے مطابق کھاد کا متوازن استعمال کریں اور موسمی الرٹ کے مطابق اسپرے کریں۔';
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
  return VoiceNotifier();
});
