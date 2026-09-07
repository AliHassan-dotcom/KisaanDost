import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisaan_dost/services/real_spray_service.dart';

void main() {
  group('RealSprayService Unit Tests', () {
    test('getSprayRecommendation parses CABI CPC API response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'recommended_pesticide': 'Tilt 250 EC (Propiconazole)',
          'dosage_per_acre': '200ml in 100L water',
          'estimated_cost': 4200,
          'best_application_time': 'subah 7:00 se 10:00 baje',
          'safety_period_days': 14,
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealSprayService(client: mockClient, cabiApiKey: 'test_cabi_key');
      final advice = await service.getSprayRecommendation('rust', 'wheat');

      expect(advice.medicine, equals('Tilt 250 EC (Propiconazole)'));
      expect(advice.dosage, equals('200ml in 100L water'));
      expect(advice.totalCost, equals(4200));
      expect(advice.timing, equals('subah 7:00 se 10:00 baje'));
      expect(advice.safetyPeriod, equals(14));
    });

    test('getSprayRecommendation provides certified fallback on failure', () async {
      final mockClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final service = RealSprayService(client: mockClient, cabiApiKey: 'test_cabi_key');
      final advice = await service.getSprayRecommendation('rust', 'wheat');

      expect(advice.medicine, contains('Tilt 250 EC'));
      expect(advice.dosage, equals('200ml'));
      expect(advice.totalCost, equals(4000));
    });
  });
}
