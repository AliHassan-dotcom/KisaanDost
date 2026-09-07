import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisaan_dost/services/real_satellite_service.dart';

void main() {
  group('RealSatelliteService Unit Tests', () {
    test('getNDVI parses NASA Earthdata MODIS API response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'ndvi_value': 0.76,
          'soil_moisture': 18.2,
          'crop_health_index': 'Healthy Canopy (0.76)',
          'last_updated': '2026-09-06T00:00:00Z',
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealSatelliteService(client: mockClient, nasaApiKey: 'test_nasa_token');
      final sat = await service.getNDVI('31.5204', '74.3587', DateTime.now());

      expect(sat.ndvi, equals(0.76));
      expect(sat.soilMoisture, equals(18.2));
      expect(sat.cropHealth, equals('Healthy Canopy (0.76)'));
    });

    test('getSoilMoisture parses Sentinel Hub API response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'soil_moisture': 17.5,
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealSatelliteService(client: mockClient, sentinelApiKey: 'test_sentinel_token');
      final sat = await service.getSoilMoisture('31.5204', '74.3587');

      expect(sat.soilMoisture, equals(17.5));
    });
  });
}
