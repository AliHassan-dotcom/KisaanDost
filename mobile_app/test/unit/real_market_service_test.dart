import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisaan_dost/services/real_market_service.dart';

void main() {
  group('RealMarketService Unit Tests', () {
    test('getCurrentMarketRate parses Pakistan Agri Market Rates API response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'crop': 'wheat',
          'current_rate': 3900,
          'unit': '40kg',
          'mandi_name': 'Multan mandi',
          'trend': 'up',
          'last_updated': '2026-09-06T12:00:00Z',
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealMarketService(client: mockClient, govApiKey: 'test_gov_key');
      final market = await service.getCurrentMarketRate('wheat', 'Multan');

      expect(market.crop, equals('wheat'));
      expect(market.rate, equals(3900));
      expect(market.unit, equals('40kg'));
      expect(market.mandiName, equals('Multan mandi'));
      expect(market.trend, equals('up'));
    });

    test('getHistoricalRates parses PMAS API response', () async {
      final mockClient = MockClient((request) async {
        final payload = {
          'rates': [
            {
              'crop': 'rice',
              'current_rate': 11200,
              'unit': '40kg',
              'mandi_name': 'Lahore mandi',
              'trend': 'stable',
              'last_updated': '2026-09-05T12:00:00Z',
            },
            {
              'crop': 'rice',
              'current_rate': 11250,
              'unit': '40kg',
              'mandi_name': 'Lahore mandi',
              'trend': 'up',
              'last_updated': '2026-09-06T12:00:00Z',
            }
          ]
        };
        return http.Response(jsonEncode(payload), 200);
      });

      final service = RealMarketService(client: mockClient, pmasApiKey: 'test_pmas_key');
      final list = await service.getHistoricalRates('rice', 'Lahore', 7);

      expect(list.length, equals(2));
      expect(list[0].rate, equals(11200));
      expect(list[1].rate, equals(11250));
    });
  });
}
