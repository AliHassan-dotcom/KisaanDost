import 'dart:async';
import 'dart:math';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:record/record.dart';

import '../config/gemini_live_config.dart';
import '../utils/wav_header_helper.dart';

/// Audio service responsible for:
/// 1. Capturing 16kHz 16-bit Mono PCM audio from microphone.
/// 2. Calculating live audio amplitude for visualizers.
/// 3. Streaming audio chunks to Gemini Live WebSocket.
/// 4. Playing back 24kHz PCM audio response from Gemini with minimal latency.
/// 5. Instant Barge-in / Interruption handling.
class AudioService {
  AudioService() {
    _initPlayer();
  }

  final AudioRecorder _recorder = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();

  StreamSubscription<Uint8List>? _recordSubscription;
  bool _isRecording = false;
  bool _isPlaying = false;

  // Queue of incoming audio chunks from Gemini
  final List<Uint8List> _playbackQueue = <Uint8List>[];
  bool _isProcessingQueue = false;

  // Callbacks
  Function(Uint8List chunk)? _onAudioChunk;
  Function(double amplitude)? _onInputAmplitude;
  Function(double amplitude)? _onOutputAmplitude;
  VoidCallback? _onPlaybackStarted;
  VoidCallback? _onPlaybackFinished;
  Function(String error)? _onError;

  bool get isRecording => _isRecording;
  bool get isPlaying => _isPlaying;

  void _initPlayer() {
    _player.setReleaseMode(ReleaseMode.stop);
    _player.setPlayerMode(PlayerMode.lowLatency);

    _player.onPlayerStateChanged.listen((state) {
      if (state == PlayerState.completed || state == PlayerState.stopped) {
        if (_playbackQueue.isEmpty) {
          _isPlaying = false;
          _onPlaybackFinished?.call();
        }
      }
    });
  }

  /// Check and request microphone permission
  Future<bool> checkPermission() async {
    try {
      return await _recorder.hasPermission();
    } catch (_) {
      return false;
    }
  }

  /// Start recording 16kHz PCM audio stream from microphone
  Future<void> startRecording({
    required Function(Uint8List chunk) onAudioChunk,
    Function(double amplitude)? onInputAmplitude,
    Function(double amplitude)? onOutputAmplitude,
    VoidCallback? onPlaybackStarted,
    VoidCallback? onPlaybackFinished,
    Function(String error)? onError,
  }) async {
    _onAudioChunk = onAudioChunk;
    _onInputAmplitude = onInputAmplitude;
    _onOutputAmplitude = onOutputAmplitude;
    _onPlaybackStarted = onPlaybackStarted;
    _onPlaybackFinished = onPlaybackFinished;
    _onError = onError;

    final hasPerm = await checkPermission();
    if (!hasPerm) {
      _onError?.call('Microphone permission denied. Please grant microphone access in settings.');
      return;
    }

    try {
      if (await _recorder.isRecording()) {
        await _recorder.stop();
      }

      const recordConfig = RecordConfig(
        encoder: AudioEncoder.pcm16bits,
        sampleRate: GeminiLiveConfig.inputSampleRate,
        numChannels: GeminiLiveConfig.inputChannels,
        echoCancel: true,
        autoGain: true,
        noiseSuppress: true,
      );

      final recordStream = await _recorder.startStream(recordConfig);
      _isRecording = true;

      // Accumulator buffer for sending chunks every ~120ms
      // 16000 samples/sec * 2 bytes/sample * 0.12 sec = ~3840 bytes
      const targetChunkBytes = (GeminiLiveConfig.inputSampleRate * 2 * GeminiLiveConfig.inputChunkDurationMs) ~/ 1000;
      final buffer = BytesBuilder(copy: false);

      _recordSubscription = recordStream.listen(
        (data) {
          buffer.add(data);

          // Calculate RMS amplitude for microphone visualization
          final amplitude = _calculatePcmRms(data);
          _onInputAmplitude?.call(amplitude);

          if (buffer.length >= targetChunkBytes) {
            final chunk = buffer.takeBytes();
            _onAudioChunk?.call(chunk);
          }
        },
        onError: (err) {
          _onError?.call('Microphone stream error: $err');
          _isRecording = false;
        },
        onDone: () {
          if (buffer.isNotEmpty) {
            _onAudioChunk?.call(buffer.takeBytes());
          }
          _isRecording = false;
        },
        cancelOnError: false,
      );
    } catch (e) {
      _isRecording = false;
      _onError?.call('Failed to start microphone recording: $e');
    }
  }

  /// Stop microphone recording
  Future<void> stopRecording() async {
    try {
      await _recordSubscription?.cancel();
      _recordSubscription = null;
      if (await _recorder.isRecording()) {
        await _recorder.stop();
      }
    } catch (e) {
      debugPrint('Error stopping recorder: $e');
    } finally {
      _isRecording = false;
      _onInputAmplitude?.call(0.0);
    }
  }

  /// Queue incoming PCM chunk from Gemini Live response and start playing
  Future<void> queueAudioChunk(Uint8List pcmChunk) async {
    if (pcmChunk.isEmpty) return;

    _playbackQueue.add(pcmChunk);

    if (!_isProcessingQueue) {
      _processPlaybackQueue();
    }
  }

  /// Sequentially plays queued audio chunks
  Future<void> _processPlaybackQueue() async {
    if (_isProcessingQueue) return;
    _isProcessingQueue = true;

    try {
      while (_playbackQueue.isNotEmpty) {
        // Combine all currently accumulated chunks in queue for smooth playback
        final bytesBuilder = BytesBuilder(copy: false);
        while (_playbackQueue.isNotEmpty) {
          bytesBuilder.add(_playbackQueue.removeAt(0));
        }
        final fullPcm = bytesBuilder.takeBytes();
        if (fullPcm.isEmpty) continue;

        final wavBytes = WavHeaderHelper.pcmToWav(
          fullPcm,
          sampleRate: GeminiLiveConfig.outputSampleRate,
          channels: GeminiLiveConfig.outputChannels,
        );

        final amp = _calculatePcmRms(fullPcm);
        _onOutputAmplitude?.call(amp);

        if (!_isPlaying) {
          _isPlaying = true;
          _onPlaybackStarted?.call();
        }

        final completer = Completer<void>();
        StreamSubscription<void>? completeSub;

        completeSub = _player.onPlayerComplete.listen((_) {
          completeSub?.cancel();
          if (!completer.isCompleted) completer.complete();
        });

        await _player.play(BytesSource(wavBytes));
        await completer.future;
      }
    } catch (e) {
      debugPrint('Error playing audio chunk: $e');
    } finally {
      _isProcessingQueue = false;
      if (_playbackQueue.isEmpty) {
        _isPlaying = false;
        _onOutputAmplitude?.call(0.0);
        _onPlaybackFinished?.call();
      }
    }
  }

  /// Instant Barge-in / Interruption: immediately stops all audio playback and clears buffer
  Future<void> stopPlayback() async {
    _playbackQueue.clear();
    _isProcessingQueue = false;
    _isPlaying = false;
    try {
      await _player.stop();
    } catch (e) {
      debugPrint('Error stopping audio playback: $e');
    } finally {
      _onOutputAmplitude?.call(0.0);
      _onPlaybackFinished?.call();
    }
  }

  /// Calculate Normalized Root Mean Square (RMS) amplitude from 16-bit PCM samples (0.0 to 1.0)
  double _calculatePcmRms(Uint8List pcmBytes) {
    if (pcmBytes.length < 2) return 0.0;

    final byteData = ByteData.view(pcmBytes.buffer, pcmBytes.offsetInBytes, pcmBytes.lengthInBytes);
    final numSamples = pcmBytes.lengthInBytes ~/ 2;
    if (numSamples == 0) return 0.0;

    double sumSquares = 0.0;
    for (int i = 0; i < numSamples; i++) {
      final sample = byteData.getInt16(i * 2, Endian.little);
      sumSquares += sample * sample;
    }

    final rms = sqrt(sumSquares / numSamples);
    // Normalize 16-bit PCM range (0 to 32768)
    final normalized = (rms / 32768.0).clamp(0.0, 1.0);
    // Apply logarithmic scaling for natural visual dynamics
    return min(1.0, normalized * 3.5);
  }

  /// Clean up and dispose all audio resources
  Future<void> dispose() async {
    await stopRecording();
    await stopPlayback();
    await _recorder.dispose();
    await _player.dispose();
  }
}
