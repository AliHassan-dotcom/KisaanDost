import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

import 'tts_text_optimizer.dart';

/// Optimized Text-to-Speech service for natural, clear Roman Urdu / Urdu voice synthesis.
class OptimizedTtsService {
  final FlutterTts _tts = FlutterTts();

  Future<void> initialize() async {
    // Set Urdu language with fallback
    try {
      await _tts.setLanguage('ur-PK');
    } catch (_) {
      try {
        await _tts.setLanguage('ur');
      } catch (_) {}
    }

    // Slow down for clarity (0.45 = 45% speed)
    await _tts.setSpeechRate(0.45);

    // Lower pitch for natural Urdu (0.9 = slightly deeper, warm human tone)
    await _tts.setPitch(0.9);

    // Full volume
    await _tts.setVolume(1.0);

    // Event handlers
    _tts.setStartHandler(() {
      debugPrint('Speech started');
    });

    _tts.setCompletionHandler(() {
      debugPrint('Speech completed');
    });

    _tts.setErrorHandler((msg) {
      debugPrint('TTS error: $msg');
    });
  }

  /// Speaks text after passing through the TTS text optimizer
  Future<void> speak(String text) async {
    final optimizedText = TtsTextOptimizer.optimize(text);
    await _tts.speak(optimizedText);
  }

  /// Stops current speech playback
  Future<void> stop() async {
    await _tts.stop();
  }

  /// Cleans up resources
  void dispose() {
    _tts.stop();
  }
}
