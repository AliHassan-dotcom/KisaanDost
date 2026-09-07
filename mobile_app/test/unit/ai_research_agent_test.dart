import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/services/ai_research_agent.dart';

void main() {
  group('AiResearchAgent Unit & Verification Tests', () {
    late AiResearchAgent agent;

    setUp(() {
      agent = AiResearchAgent(
        weatherData: const WeatherData(
          condition: 'saaf',
          temp: 28,
          rainProbability: 49,
        ),
        pestData: const PestData(
          pestName: 'wheat midge',
          severity: 'Medium',
          recommendedPesticide: 'Tilt 250 EC',
          dosage: '200ml',
        ),
        marketData: const MarketData(
          crop: 'wheat',
          mandiName: 'Lahore mandi',
          rate: 3850,
          unit: '40kg',
          trend: 'up',
        ),
        sprayAdvice: const SprayAdviceData(
          medicine: 'Tilt 250 EC',
          dosage: '200ml',
          totalCost: 4000,
          timing: 'subah 7 se 10 baje',
        ),
      );
    });

    test('Scenario 1: Weather query resolves from dataset and cites source', () async {
      final answer = await agent.answerQuestion('Aaj ka mausam kya hai?');

      expect(answer.startsWith('✅ Dataset se:'), isTrue);
      expect(answer.contains('saaf'), isTrue);
      expect(answer.contains('28°C'), isTrue);
      expect(answer.contains('49%'), isTrue);
    });

    test('Scenario 2: Pest query resolves from dataset and cites source', () async {
      final answer = await agent.answerQuestion('Wheat mein keeda lag gaya, kya spray karun?');

      expect(answer.startsWith('✅ Dataset se:'), isTrue);
      expect(answer.contains('wheat midge'), isTrue);
      expect(answer.contains('Tilt 250 EC'), isTrue);
      expect(answer.contains('200ml'), isTrue);
    });

    test('Scenario 3: Market query resolves from dataset and cites source', () async {
      final answer = await agent.answerQuestion('Wheat ka rate kya hai Lahore mandi mein?');

      expect(answer.startsWith('✅ Dataset se:'), isTrue);
      expect(answer.contains('wheat'), isTrue);
      expect(answer.contains('Lahore mandi'), isTrue);
      expect(answer.contains('3850'), isTrue);
      expect(answer.contains('40kg'), isTrue);
    });

    test('Scenario 4: Non-dataset crop disease query falls back to Google and cites Google', () async {
      final answer = await agent.answerQuestion('Wheat yellow rust ka ilaj kya hai?');

      expect(answer.startsWith('🌐 Google se:'), isTrue);
      expect(answer.contains('fungal disease'), isTrue);
      expect(answer.contains('Tilt 250 EC'), isTrue);
    });

    test('Scenario 5: Out of domain unknown query gracefully returns polite fallback', () async {
      final answer = await agent.answerQuestion('Pakistan ka capital kya hai?');

      expect(answer, equals('Maaf karein, mujhe iska jawab nahi mila. Koi aur sawal poochiye!'));
    });

    test('Question understanding extracts crop, location, and topic correctly', () async {
      final understood = await agent.understandQuestion('Lahore mein gandum ki fasal pe spray kab karein?');

      expect(understood.contains('crop:wheat'), isTrue);
      expect(understood.contains('location:Lahore'), isTrue);
      expect(understood.contains('topic:spray'), isTrue);
    });
  });
}
