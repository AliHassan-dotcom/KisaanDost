import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/gemini_live_config.dart';

/// State of the Gemini Live connection
enum GeminiLiveConnectionState {
  disconnected,
  connecting,
  connected,
  error,
}

/// Service managing the real-time bidirectional WebSocket connection to Google Gemini Live API.
class GeminiLiveService {
  GeminiLiveService();

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _channelSubscription;
  GeminiLiveConnectionState _connectionState = GeminiLiveConnectionState.disconnected;

  // Callbacks
  Function(GeminiLiveConnectionState state)? _onStateChanged;
  Function(Uint8List audioPcm)? _onAudioReceived;
  Function(String text, bool isUser)? _onTranscriptReceived;
  VoidCallback? _onInterrupted;
  VoidCallback? _onTurnComplete;
  Function(String error)? _onError;

  GeminiLiveConnectionState get connectionState => _connectionState;
  bool get isConnected => _connectionState == GeminiLiveConnectionState.connected;

  /// Connect to Gemini Live WebSocket and send the initial setup payload
  Future<void> connect({
    required String apiKey,
    String? model,
    String? voiceName,
    String? systemInstruction,
    Function(GeminiLiveConnectionState state)? onStateChanged,
    Function(Uint8List audioPcm)? onAudioReceived,
    Function(String text, bool isUser)? onTranscriptReceived,
    VoidCallback? onInterrupted,
    VoidCallback? onTurnComplete,
    Function(String error)? onError,
  }) async {
    _onStateChanged = onStateChanged;
    _onAudioReceived = onAudioReceived;
    _onTranscriptReceived = onTranscriptReceived;
    _onInterrupted = onInterrupted;
    _onTurnComplete = onTurnComplete;
    _onError = onError;

    if (apiKey.isEmpty) {
      _updateState(GeminiLiveConnectionState.error);
      _onError?.call('Gemini API Key is missing. Please provide a valid key.');
      return;
    }

    await disconnect();

    _updateState(GeminiLiveConnectionState.connecting);

    final wsUri = Uri.parse(
      '${GeminiLiveConfig.defaultWebSocketUrl}?key=$apiKey',
    );

    try {
      _channel = IOWebSocketChannel.connect(
        wsUri,
        pingInterval: const Duration(seconds: 15),
      );

      _channelSubscription = _channel!.stream.listen(
        _handleServerMessage,
        onError: (error) {
          debugPrint('Gemini Live WebSocket error: $error');
          _updateState(GeminiLiveConnectionState.error);
          _onError?.call('WebSocket connection error: $error');
        },
        onDone: () {
          debugPrint('Gemini Live WebSocket closed.');
          _updateState(GeminiLiveConnectionState.disconnected);
        },
        cancelOnError: true,
      );

      // Send initial Setup handshake message
      _sendSetupMessage(
        model: model ?? GeminiLiveConfig.defaultModel,
        voiceName: voiceName ?? GeminiLiveConfig.defaultVoiceName,
        systemInstruction: systemInstruction ?? GeminiLiveConfig.systemInstruction,
      );
    } catch (e) {
      _updateState(GeminiLiveConnectionState.error);
      _onError?.call('Failed to connect to Gemini Live: $e');
    }
  }

  /// Sends the required initial setup message to configure model, audio modality, voice, and system prompt.
  void _sendSetupMessage({
    required String model,
    required String voiceName,
    required String systemInstruction,
  }) {
    final setupPayload = <String, dynamic>{
      'setup': <String, dynamic>{
        'model': model,
        'generationConfig': <String, dynamic>{
          'responseModalities': <String>['AUDIO'],
          'speechConfig': <String, dynamic>{
            'voiceConfig': <String, dynamic>{
              'prebuiltVoiceConfig': <String, dynamic>{
                'voiceName': voiceName,
              },
            },
          },
        },
        'systemInstruction': <String, dynamic>{
          'parts': <Map<String, dynamic>>[
            <String, dynamic>{
              'text': systemInstruction,
            },
          ],
        },
      },
    };

    _sendJson(setupPayload);
  }

  /// Streams real-time 16kHz PCM audio chunk to Gemini Live
  void sendRealtimeAudioChunk(Uint8List pcmBytes) {
    if (!isConnected || _channel == null || pcmBytes.isEmpty) return;

    final base64Audio = base64Encode(pcmBytes);
    final payload = <String, dynamic>{
      'realtimeInput': <String, dynamic>{
        'mediaChunks': <Map<String, dynamic>>[
          <String, dynamic>{
            'mimeType': GeminiLiveConfig.inputMimeType,
            'data': base64Audio,
          },
        ],
      },
    };

    _sendJson(payload);
  }

  /// Sends a text turn or prompt
  void sendTextMessage(String text) {
    if (!isConnected || _channel == null || text.trim().isEmpty) return;

    final payload = <String, dynamic>{
      'clientContent': <String, dynamic>{
        'turns': <Map<String, dynamic>>[
          <String, dynamic>{
            'role': 'user',
            'parts': <Map<String, dynamic>>[
              <String, dynamic>{'text': text},
            ],
          },
        ],
        'turnComplete': true,
      },
    };

    _onTranscriptReceived?.call(text, true);
    _sendJson(payload);
  }

  /// Parses server message from Gemini Live WebSocket
  void _handleServerMessage(dynamic message) {
    try {
      final text = message is String ? message : utf8.decode(message as List<int>);
      final data = jsonDecode(text) as Map<String, dynamic>;

      // 1. Setup Complete
      if (data.containsKey('setupComplete')) {
        debugPrint('Gemini Live Setup Complete. Ready for real-time conversation.');
        _updateState(GeminiLiveConnectionState.connected);
        return;
      }

      // 2. Server Content
      if (data.containsKey('serverContent')) {
        final serverContent = data['serverContent'] as Map<String, dynamic>;

        // Interruption / Barge-in detection from server
        final bool isInterrupted = serverContent['interrupted'] as bool? ?? false;
        if (isInterrupted) {
          debugPrint('Gemini Live: Barge-in / Interruption signal received.');
          _onInterrupted?.call();
          return;
        }

        // Model response turn
        if (serverContent.containsKey('modelTurn')) {
          final modelTurn = serverContent['modelTurn'] as Map<String, dynamic>;
          final parts = modelTurn['parts'] as List<dynamic>? ?? <dynamic>[];

          for (final part in parts) {
            if (part is Map<String, dynamic>) {
              // Audio response chunk
              if (part.containsKey('inlineData')) {
                final inlineData = part['inlineData'] as Map<String, dynamic>;
                final base64Data = inlineData['data'] as String? ?? '';

                if (base64Data.isNotEmpty) {
                  final audioBytes = base64Decode(base64Data);
                  _onAudioReceived?.call(audioBytes);
                }
              }

              // Text transcript chunk
              if (part.containsKey('text')) {
                final textChunk = part['text'] as String? ?? '';
                if (textChunk.isNotEmpty) {
                  _onTranscriptReceived?.call(textChunk, false);
                }
              }
            }
          }
        }

        // Turn complete
        final bool turnComplete = serverContent['turnComplete'] as bool? ?? false;
        if (turnComplete) {
          _onTurnComplete?.call();
        }
      }
    } catch (e) {
      debugPrint('Error handling Gemini Live server message: $e');
    }
  }

  void _sendJson(Map<String, dynamic> data) {
    try {
      final jsonString = jsonEncode(data);
      _channel?.sink.add(jsonString);
    } catch (e) {
      debugPrint('Error sending JSON to Gemini Live: $e');
    }
  }

  void _updateState(GeminiLiveConnectionState state) {
    if (_connectionState != state) {
      _connectionState = state;
      _onStateChanged?.call(state);
    }
  }

  /// Disconnect and cleanup WebSocket channel
  Future<void> disconnect() async {
    try {
      await _channelSubscription?.cancel();
      _channelSubscription = null;
      await _channel?.sink.close();
      _channel = null;
    } catch (e) {
      debugPrint('Error disconnecting Gemini Live: $e');
    } finally {
      _updateState(GeminiLiveConnectionState.disconnected);
    }
  }

  /// Dispose all resources
  Future<void> dispose() async {
    await disconnect();
  }
}
