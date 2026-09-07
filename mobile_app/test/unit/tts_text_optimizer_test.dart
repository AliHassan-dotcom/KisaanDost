import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/services/tts_text_optimizer.dart';

void main() {
  group('TtsTextOptimizer Unit Tests', () {
    test('Optimizes Urdu keywords into Roman Urdu', () {
      final input = 'آج کا موسم صاف ہے اور بارش کا امکان ہے۔';
      final result = TtsTextOptimizer.optimize(input);

      expect(result.contains('Aaj'), isTrue);
      expect(result.contains('mausam'), isTrue);
      expect(result.contains('saaf'), isTrue);
      expect(result.contains('barish'), isTrue);
      expect(result.contains('imkaan'), isTrue);
    });

    test('Replaces agricultural symbols with spoken words', () {
      final input = 'Temperature 28°C, Humidity 49%, Rate Rs. 3850/40kg';
      final result = TtsTextOptimizer.optimize(input);

      expect(result.contains('degrees'), isTrue);
      expect(result.contains('percent'), isTrue);
      expect(result.contains('rupay'), isTrue);
      expect(result.contains('per'), isTrue);
    });

    test('Adds natural pauses and breathing spaces for long text', () {
      final input = 'Spray Tilt 250 EC. Total cost 4000 PKR! Apply in morning.';
      final result = TtsTextOptimizer.optimize(input);

      expect(result.contains(',,'), isTrue);
      expect(result.contains('rupay'), isTrue);
    });

    test('Handles greetings and crop names', () {
      final input = 'السلام علیکم، آج گندم اور کماد کے لیے کھاد کا اسپرے کریں۔';
      final result = TtsTextOptimizer.optimize(input);

      expect(result.contains('Assalamualaikum'), isTrue);
      expect(result.contains('Gandum'), isTrue);
      expect(result.contains('Kamaad'), isTrue);
      expect(result.contains('khaad'), isTrue);
      expect(result.contains('spray'), isTrue);
    });
  });
}
