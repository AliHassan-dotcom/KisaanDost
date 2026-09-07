import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisaan_dost/services/real_ai_research_agent.dart';
import 'package:kisaan_dost/services/real_market_service.dart';
import 'package:kisaan_dost/services/real_pest_service.dart';
import 'package:kisaan_dost/services/real_satellite_service.dart';
import 'package:kisaan_dost/services/real_spray_service.dart';
import 'package:kisaan_dost/services/real_weather_service.dart';

void main() {
  group('RealAiResearchAgent Unit Tests', () {
    late MockClient mockClient;
    late RealWeatherService weatherService;
    late RealPestService pestService;
    late RealMarketService marketService;
    late RealSprayService sprayService;
    late RealSatelliteService satelliteService;
    late RealAiResearchAgent agent;

    setUp(() {
      mockClient = MockClient((request) async {
        final path = request.url.path;
        final host = request.url.host;

        // OpenWeatherMap
        if (path.contains('/weather')) {
          return http.Response(
            jsonEncode({
              'name': 'Lahore',
              'main': {'temp': 28.4, 'humidity': 60},
              'weather': [
                {'description': 'saaf'}
              ],
              'wind': {'speed': 12.0},
              'pop': 0.15,
            }),
            200,
          );
        }

        // FAO Pest
        if (path.contains('/alerts')) {
          return http.Response(
            jsonEncode({
              'alerts': [
                {
                  'pest_name': 'wheat midge',
                  'severity': 'Medium',
                  'affected_area': 'Lahore',
                  'recommended_treatment': 'Tilt 250 EC',
                  'dosage': '200ml per acre',
                  'last_updated': '2026-09-06T10:00:00Z',
                }
              ]
            }),
            200,
          );
        }

        // Market Rates
        if (path.contains('/market-rates')) {
          return http.Response(
            jsonEncode({
              'crop': 'wheat',
              'current_rate': 3850,
              'unit': '40kg',
              'mandi_name': 'Lahore mandi',
              'trend': 'up',
              'last_updated': '2026-09-06T10:00:00Z',
            }),
            200,
          );
        }

        // CABI Spray
        if (path.contains('/recommendations')) {
          return http.Response(
            jsonEncode({
              'recommended_pesticide': 'Tilt 250 EC',
              'dosage_per_acre': '200ml',
              'estimated_cost': 4000,
              'best_application_time': 'subah 7:00 se 10:00 baje',
              'safety_period_days': 14,
            }),
            200,
          );
        }

        // Sentinel Satellite
        if (host.contains('sentinel-hub')) {
          return http.Response(
            jsonEncode({
              'soil_moisture': 16.9,
            }),
            200,
          );
        }

        // Google Custom Search
        if (host.contains('googleapis.com') && path.contains('/customsearch')) {
          return http.Response(
            jsonEncode({
              'items': [
                {
                  'snippet':
                      'Wheat yellow rust is caused by Puccinia striiformis. Apply Propiconazole fungicide immediately.'
                }
              ]
            }),
            200,
          );
        }

        return http.Response('Not Found', 404);
      });

      weatherService = RealWeatherService(client: mockClient, apiKey: 'test_owm');
      pestService = RealPestService(client: mockClient, faoApiKey: 'test_fao');
      marketService = RealMarketService(client: mockClient, govApiKey: 'test_gov');
      sprayService = RealSprayService(client: mockClient, cabiApiKey: 'test_cabi');
      satelliteService = RealSatelliteService(client: mockClient, sentinelApiKey: 'test_sentinel');

      agent = RealAiResearchAgent(
        weatherService: weatherService,
        pestService: pestService,
        marketService: marketService,
        sprayService: sprayService,
        satelliteService: satelliteService,
        googleApiKey: 'test_google_key',
        googleSearchEngineId: 'test_cse_id',
        client: mockClient,
      );
    });

    test('understandQuestion extracts entities correctly', () {
      final understood = agent.understandQuestion('Wheat mein keeda lag gaya Lahore mein');
      expect(understood, contains('crop:wheat'));
      expect(understood, contains('location:Lahore'));
      expect(understood, contains('topic:pest'));
    });

    test('Answers greetings naturally and politely without search', () async {
      final answer = await agent.answerQuestion('Salam bhai');
      expect(answer, contains('Walaikum Assalam'));
      expect(answer, contains('KisaanDost'));
    });

    test('Answers weather questions using real dataset', () async {
      final answer = await agent.answerQuestion('Aaj ka mausam kya hai?', 'Lahore');
      expect(answer, contains('28°C'));
      expect(answer, contains('15%'));
    });

    test('Answers pest questions using real dataset', () async {
      final answer = await agent.answerQuestion('Gandum mein keeda lag gaya kya karun?', 'Lahore');
      expect(answer, contains('wheat midge'));
      expect(answer, contains('Tilt 250 EC'));
    });

    test('Answers market rate questions using real dataset', () async {
      final answer = await agent.answerQuestion('Wheat ka rate kya hai Lahore mandi mein?', 'Lahore');
      expect(answer, contains('3850'));
      expect(answer, contains('Lahore mandi'));
    });

    test('Answers spray questions using real dataset', () async {
      final answer = await agent.answerQuestion('Konsa spray karun?', 'Lahore');
      expect(answer, contains('Tilt 250 EC'));
      expect(answer, contains('4000 rupay'));
    });

    test('Answers irrigation questions using satellite data', () async {
      final answer = await agent.answerQuestion('Zameen ko kab pani lagana chahiye?', 'Lahore');
      expect(answer, contains('16.9%'));
    });

    test('Answers specific crop disease knowledge queries', () async {
      final answer = await agent.answerQuestion('Yellow rust ka ilaj kya hai?', 'Lahore');
      expect(answer, contains('Puccinia striiformis'));
    });

    test('Returns polite fallback for out-of-domain queries', () async {
      final answer = await agent.answerQuestion('Pakistan ka capital kya hai?');
      expect(answer, contains('Maaf karein'));
    });
  });
}
