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

  /// Start real-time voice session
  Future<void> startSession() async {
    state = state.copyWith(clearError: true);

    final key = state.apiKey.isNotEmpty ? state.apiKey : GeminiLiveConfig.apiKey;
    if (key.isEmpty) {
      state = state.copyWith(
        connectionState: GeminiLiveConnectionState.error,
        errorMessage: 'Gemini API Key is required. Please set it in Settings.',
      );
      return;
    }

    // 1. Connect WebSocket to Gemini Live
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
        debugPrint('Gemini Live: Interrupted by user.');
        interrupt();
      },
      onTurnComplete: () {
        _currentAssistantMessageId = null;
        if (state.agentState != VoiceAgentState.speaking) {
          state = state.copyWith(agentState: VoiceAgentState.listening);
        }
      },
      onError: (err) {
        state = state.copyWith(
          connectionState: GeminiLiveConnectionState.error,
          errorMessage: err,
        );
      },
    );

    // 2. Start Microphone Audio Capture
    await _audioService.startRecording(
      onAudioChunk: (chunk) {
        if (!state.isMuted && _geminiLiveService.isConnected) {
          _geminiLiveService.sendRealtimeAudioChunk(chunk);
        }
      },
      onInputAmplitude: (amp) {
        state = state.copyWith(micLevel: amp);

        // Proactive Client-Side Barge-In Detection:
        // If agent is speaking and user starts talking loudly (> 0.20 RMS), stop audio immediately!
        if (state.isSpeaking && amp > 0.22) {
          debugPrint('Local Barge-in: user speech detected during playback (amp: $amp)');
          interrupt();
        }
      },
      onOutputAmplitude: (amp) {
        state = state.copyWith(speakerLevel: amp);
      },
      onPlaybackStarted: () {
        state = state.copyWith(agentState: VoiceAgentState.speaking);
      },
      onPlaybackFinished: () {
        state = state.copyWith(
          agentState: VoiceAgentState.listening,
          speakerLevel: 0.0,
        );
      },
      onError: (err) {
        state = state.copyWith(errorMessage: err);
      },
    );
  }

  /// Stop current voice session and audio recording
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

  /// Instant Barge-in: Immediately stops assistant playback and switches state to listening
  Future<void> interrupt() async {
    await _audioService.stopPlayback();
    state = state.copyWith(
      agentState: VoiceAgentState.interrupted,
      speakerLevel: 0.0,
    );
    // Return back to listening after brief pause
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted && state.isConnected) {
        state = state.copyWith(agentState: VoiceAgentState.listening);
      }
    });
  }

  /// Toggle microphone mute
  void toggleMute() {
    state = state.copyWith(isMuted: !state.isMuted);
  }

  /// Set Gemini API Key
  void setApiKey(String key) {
    state = state.copyWith(apiKey: key.trim(), clearError: true);
  }

  /// Set Voice (e.g. Aoede, Puck, Kore, Fenrir, Charon)
  void setVoice(String voice) {
    state = state.copyWith(selectedVoice: voice);
  }

  /// Send text message / query
  void sendTextMessage(String text) {
    if (text.trim().isEmpty) return;
    _geminiLiveService.sendTextMessage(text.trim());
  }

  /// Clear conversation transcript
  void clearTranscript() {
    state = state.copyWith(messages: const <VoiceChatMessage>[]);
  }

  void _handleTranscriptChunk(String chunk, bool isUser) {
    final now = DateTime.now();

    if (isUser) {
      final userMsg = VoiceChatMessage(
        id: 'msg_${now.millisecondsSinceEpoch}',
        sender: 'user',
        text: chunk,
        timestamp: now,
      );
      state = state.copyWith(
        messages: <VoiceChatMessage>[...state.messages, userMsg],
      );
    } else {
      // Append chunk to ongoing assistant message or create a new message
      if (_currentAssistantMessageId == null) {
        _currentAssistantMessageId = 'msg_${now.millisecondsSinceEpoch}';
        final newAssistantMsg = VoiceChatMessage(
          id: _currentAssistantMessageId!,
          sender: 'assistant',
          text: chunk,
          timestamp: now,
          isStreaming: true,
        );
        state = state.copyWith(
          messages: <VoiceChatMessage>[...state.messages, newAssistantMsg],
        );
      } else {
        final updatedMessages = state.messages.map((m) {
          if (m.id == _currentAssistantMessageId) {
            return m.copyWith(text: '${m.text}$chunk');
          }
          return m;
        }).toList();

        state = state.copyWith(messages: updatedMessages);
      }
    }
  }

  @override
  void dispose() {
    _audioService.dispose();
    _geminiLiveService.dispose();
    super.dispose();
  }
}

/// Global Riverpod provider for Voice AI State
final voiceProvider = StateNotifierProvider<VoiceNotifier, VoiceState>((ref) {
  return VoiceNotifier();
});
