import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisaan_dost/services/real_pest_service.dart';

void main() {
  group('RealPestService Unit Tests', () {
    test('getCurrentPestAlerts parses FAO alert JSON response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'alerts': [
            {
              'pest_name': 'Desert Locust',
              'severity': 'High',
              'affected_area': 'Bahawalpur',
              'recommended_treatment': 'Malathion 57 EC',
              'dosage': '300ml per acre',
              'last_updated': '2026-09-06T10:00:00Z',
            }
          ]
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealPestService(client: mockClient, faoApiKey: 'test_fao_key');
      final alert = await service.getCurrentPestAlerts('Bahawalpur');

      expect(alert.hasAlert, isTrue);
      expect(alert.pestName, equals('Desert Locust'));
      expect(alert.severity, equals('High'));
      expect(alert.affectedArea, equals('Bahawalpur'));
      expect(alert.recommendedPesticide, equals('Malathion 57 EC'));
      expect(alert.dosage, equals('300ml per acre'));
    });

    test('getCurrentPestAlerts returns noAlert when list is empty', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'alerts': []}), 200);
      });

      final service = RealPestService(client: mockClient, faoApiKey: 'test_fao_key');
      final alert = await service.getCurrentPestAlerts('Lahore');

      expect(alert.hasAlert, isFalse);
      expect(alert.pestName, equals('None'));
    });

    test('getSeasonalPestForecast parses CABI response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'pests': [
            {
              'pest_name': 'Yellow Rust',
              'severity': 'Medium',
              'affected_area': 'Punjab',
              'recommended_treatment': 'Tilt 250 EC',
              'dosage': '200ml per acre',
              'last_updated': '2026-09-06T12:00:00Z',
            }
          ]
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealPestService(client: mockClient, cabiApiKey: 'test_cabi_key');
      final pests = await service.getSeasonalPestForecast('wheat', 'Punjab');

      expect(pests.length, equals(1));
      expect(pests[0].pestName, equals('Yellow Rust'));
      expect(pests[0].recommendedPesticide, equals('Tilt 250 EC'));
    });
  });
}
