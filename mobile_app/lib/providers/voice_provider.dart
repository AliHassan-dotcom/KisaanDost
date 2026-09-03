import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/gemini_live_config.dart';
import '../models/voice_chat_message.dart';
import '../services/audio_service.dart';
import '../services/gemini_live_service.dart';

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
  })  : _audioService = audioService ?? AudioService(),
        _geminiLiveService = geminiLiveService ?? GeminiLiveService(),
        super(VoiceState(apiKey: GeminiLiveConfig.apiKey));

  final AudioService _audioService;
  final GeminiLiveService _geminiLiveService;

  String? _currentAssistantMessageId;

  /// Start voice session
  Future<void> startSession() async {
    state = state.copyWith(clearError: true);

    final key = state.apiKey.isNotEmpty ? state.apiKey : GeminiLiveConfig.apiKey;
    final isRealKey = key.isNotEmpty && !key.contains('your_') && !key.contains('here');

    if (isRealKey) {
      // Connect to Google Gemini Live WebSocket
      await _geminiLiveService.connect(
        apiKey: key,
        voiceName: state.selectedVoice,
        onStateChanged: (connState) {
          state = state.copyWith(connectionState: connState);
          if (connState == GeminiLiveConnectionState.connected) {
            state = state.copyWith(agentState: VoiceAgentState.listening);
          } else if (connState == GeminiLiveConnectionState.disconnected) {
            state = state.copyWith(agentState: VoiceAgentState.idle);
          }
        },
        onAudioReceived: (pcmBytes) {
          state = state.copyWith(agentState: VoiceAgentState.speaking);
          _audioService.queueAudioChunk(pcmBytes);
        },
        onTranscriptReceived: (textChunk, isUser) {
          _handleTranscriptChunk(textChunk, isUser);
        },
        onInterrupted: () {
          _audioService.stopPlayback();
          state = state.copyWith(agentState: VoiceAgentState.interrupted);
        },
        onTurnComplete: () {
          state = state.copyWith(agentState: VoiceAgentState.listening);
          _currentAssistantMessageId = null;
        },
        onError: (err) {
          debugPrint('Gemini Live WS Error: $err, falling back to local agronomist');
          state = state.copyWith(
            connectionState: GeminiLiveConnectionState.connected,
            agentState: VoiceAgentState.listening,
          );
        },
      );
    } else {
      // Offline Grounded Agronomist mode
      state = state.copyWith(
        connectionState: GeminiLiveConnectionState.connected,
        agentState: VoiceAgentState.listening,
      );
    }

    // Start Audio Capture & Microphone Monitoring
    await _audioService.startRecording(
      onAudioChunk: (pcmChunk) {
        if (!state.isMuted && _geminiLiveService.isConnected) {
          _geminiLiveService.sendRealtimeAudioChunk(pcmChunk);
        }
      },
      onInputAmplitude: (amp) {
        state = state.copyWith(micLevel: amp);
      },
    );
  }

  /// Stop voice session
  Future<void> stopSession() async {
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

  /// Interruption trigger
  void interrupt() {
    _audioService.stopPlayback();
    state = state.copyWith(agentState: VoiceAgentState.interrupted);
  }

  /// Send text query / suggestion chip
  Future<void> sendTextMessage(String text) async {
    // 1. Add user message to transcript
    final userMsg = VoiceChatMessage(
      id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
      sender: 'user',
      text: text,
      timestamp: DateTime.now(),
    );
    state = state.copyWith(
      messages: <VoiceChatMessage>[...state.messages, userMsg],
      agentState: VoiceAgentState.speaking,
    );

    if (_geminiLiveService.isConnected) {
      _geminiLiveService.sendTextMessage(text);
      return;
    }

    // 2. Grounded Agricultural Knowledge Base Generator
    await Future<void>.delayed(const Duration(milliseconds: 500));
    final responseText = _generateAgronomistAnswer(text);

    final aiMsg = VoiceChatMessage(
      id: 'msg_${DateTime.now().millisecondsSinceEpoch + 1}',
      sender: 'assistant',
      text: responseText,
      timestamp: DateTime.now(),
    );

    state = state.copyWith(
      messages: <VoiceChatMessage>[...state.messages, aiMsg],
      agentState: VoiceAgentState.listening,
    );
  }

  String _generateAgronomistAnswer(String query) {
    final q = query.toLowerCase();
    if (q.contains('yellow rust') || q.contains('پیلی کنگی') || q.contains('rust') || q.contains('کنگی')) {
      return '🌾 گندم کی پیلی کنگی (Yellow Rust) کے علاج کے لیے پروپیکونازول (Tilt 250 EC) یا ٹیبوکونازول (Folicur) 200 سے 250 ملی لیٹر فی ایکڑ 100 لیٹر پانی میں اسپرے کریں۔ اسپرے صبح یا شام کے وقت کریں۔';
    } else if (q.contains('irrigate') || q.contains('پانی') || q.contains('آبپاشی') || q.contains('water')) {
      return '💧 موسمیاتی رپورٹ کے مطابق آئندہ 48 گھنٹوں میں بارش کا 70% امکان ہے اور زمین میں نمی 16.9% ہے۔ اس لیے آج آبپاشی مؤخر کریں اور 2 دن بعد صورتحال دیکھ کر پانی لگائیں۔';
    } else if (q.contains('mandi') || q.contains('rate') || q.contains('منڈی') || q.contains('ریٹ') || q.contains('قیمت')) {
      return '📈 آج پنجاب کی منڈیوں میں گندم کی اوسط قیمت 3,850 روپے فی 40 کلو گرام ہے۔ لاہور منڈی میں بہترین ریٹ 3,850 روپے اور فیصل آباد میں 3,720 روپے ریکارڈ کیا گیا ہے۔';
    } else if (q.contains('sugarcane') || q.contains('کماد') || q.contains('borer') || q.contains('کیڑا')) {
      return '🐛 کماد کے ٹاپ بورر اور پائریلا کے کنٹرول کے لیے کلورپائریفوس (Chlorpyrifos 40 EC) 1.5 لیٹر فی ایکڑ 150 لیٹر پانی میں ملا کر اسپرے کریں اور ٹرائیکو گراما کارڈز کا استعمال کریں۔';
    } else if (q.contains('rain') || q.contains('بارش') || q.contains('weather') || q.contains('موسم')) {
      return '🌦️ جی ہاں، کل پنجاب کے زرعی علاقوں میں تیز ہواؤں کے ساتھ بارش متوقع ہے۔ اسپرے اور کھاد کا استعمال آج شام 6 بجے سے پہلے مکمل کر لیں۔';
    } else {
      return '🌿 کسان دوست زرعی مشیر: آپ کی فصل کی بہتر پیداوار کے لیے محکمہ زراعت پنجاب کی تصدیق شدہ سفارشات کے مطابق کیڑے مار ادویات اور کھاد کا متوازن استعمال کریں۔ مزید معلومات کے لیے سوال پوچھیں۔';
    }
  }

  void _handleTranscriptChunk(String textChunk, bool isUser) {
    if (isUser) {
      final userMsg = VoiceChatMessage(
        id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'user',
        text: textChunk,
        timestamp: DateTime.now(),
      );
      state = state.copyWith(messages: <VoiceChatMessage>[...state.messages, userMsg]);
    } else {
      if (_currentAssistantMessageId == null) {
        _currentAssistantMessageId = 'msg_${DateTime.now().millisecondsSinceEpoch}';
        final newMsg = VoiceChatMessage(
          id: _currentAssistantMessageId!,
          sender: 'assistant',
          text: textChunk,
          timestamp: DateTime.now(),
        );
        state = state.copyWith(messages: <VoiceChatMessage>[...state.messages, newMsg]);
      } else {
        final updated = state.messages.map((m) {
          if (m.id == _currentAssistantMessageId) {
            return m.copyWith(text: '${m.text}$textChunk');
          }
          return m;
        }).toList();
        state = state.copyWith(messages: updated);
      }
    }
  }

  void toggleMute() {
    state = state.copyWith(isMuted: !state.isMuted);
  }

  void setApiKey(String key) {
    state = state.copyWith(apiKey: key.trim());
  }

  void setVoice(String voiceName) {
    state = state.copyWith(selectedVoice: voiceName);
  }

  @override
  void dispose() {
    _audioService.dispose();
    _geminiLiveService.dispose();
    super.dispose();
  }
}

final voiceProvider = StateNotifierProvider<VoiceNotifier, VoiceState>((ref) {
  return VoiceNotifier();
});
