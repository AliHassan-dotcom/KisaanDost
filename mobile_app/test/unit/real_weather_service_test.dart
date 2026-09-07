import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisaan_dost/services/real_weather_service.dart';

void main() {
  group('RealWeatherService Unit Tests', () {
    test('getCurrentWeather parses valid OpenWeatherMap response', () async {
      final mockClient = MockClient((request) async {
        if (request.url.path.contains('/weather')) {
          final payload = {
            'name': 'Lahore',
            'main': {
              'temp': 31.5,
              'humidity': 58,
            },
            'weather': [
              {'description': 'clear sky'}
            ],
            'wind': {'speed': 14.2},
            'pop': 0.15,
          };
          return http.Response(jsonEncode(payload), 200);
        }
        return http.Response('Not Found', 404);
      });

      final service = RealWeatherService(client: mockClient, apiKey: 'test_key');
      final weather = await service.getCurrentWeather('Lahore');

      expect(weather.city, equals('Lahore'));
      expect(weather.temp, equals(31.5));
      expect(weather.condition, equals('clear sky'));
      expect(weather.humidity, equals(58.0));
      expect(weather.windSpeed, equals(14.2));
      expect(weather.rainProbability, equals(15.0));
    });

    test('getTomorrowWeather parses 5-day forecast response interval', () async {
      final mockClient = MockClient((request) async {
        if (request.url.path.contains('/forecast')) {
          final items = List.generate(
            10,
            (index) => {
              'main': {'temp': 29.0 + index, 'humidity': 50 + index},
              'weather': [
                {'description': 'partly cloudy'}
              ],
              'wind': {'speed': 11.0},
              'pop': 0.25,
            },
          );
          return http.Response(jsonEncode({'list': items}), 200);
        }
        return http.Response('Not Found', 404);
      });

      final service = RealWeatherService(client: mockClient, apiKey: 'test_key');
      final forecast = await service.getTomorrowWeather('Multan');

      expect(forecast.condition, equals('partly cloudy'));
      expect(forecast.temp, equals(37.0));
      expect(forecast.rainProbability, equals(25.0));
    });

    test('getCurrentWeather falls back gracefully on API error', () async {
      final mockClient = MockClient((request) async {
        return http.Response('Unauthorized', 401);
      });

      final service = RealWeatherService(client: mockClient, apiKey: 'invalid_key');
      final weather = await service.getCurrentWeather('Faisalabad');

      expect(weather, isNotNull);
      expect(weather.temp, isNotNull);
      expect(weather.condition, isNotEmpty);
    });
  });
}
