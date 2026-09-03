import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/market_mover.dart';
import 'package:kisaan_dost/models/market_price.dart';
import 'package:kisaan_dost/repositories/mock/mock_market_repository.dart';

void main() {
  group('MarketPrice', () {
    test('parses official AMIS response correctly', () {
      final json = <String, dynamic>{
        'commodity_name': 'Rice Basmati Super (New)',
        'commodity_id': 3,
        'district': 'Lahore District',
        'market_name': 'Lahore',
        'data_status': 'official_amis',
        'validation_status': 'validated',
        'unit': 'Rs/100Kg',
        'min_price_pkr': 30500.0,
        'max_price_pkr': 30500.0,
        'fqp_price_pkr': 30500.0,
        'price_date': '2026-09-02',
        'source_displayed_date': '02-09-2026',
        'source_name': 'Official AMIS Punjab',
        'source_url': 'http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=3',
        'retrieved_at': '2026-09-01T22:07:50Z',
      };

      final price = MarketPrice.fromJson(json);
      expect(price.crop, 'Rice Basmati Super (New)');
      expect(price.market, 'Lahore');
      expect(price.district, 'Lahore District');
      expect(price.status, ApiDataStatus.live);
      expect(price.unit, 'Rs/100Kg');
      expect(price.fqpPrice, 30500.0);
      expect(price.sourceName, 'Official AMIS Punjab');
      expect(price.isMock, isFalse);
    });

    test('parses stale warning correctly', () {
      final json = <String, dynamic>{
        'crop': 'Potato Fresh',
        'district': 'Lahore District',
        'status': 'historical',
        'warning': 'Official AMIS price record is from 2026-08-20 (12 days ago).',
        'unit': 'Rs/100Kg',
      };

      final price = MarketPrice.fromJson(json);
      expect(price.crop, 'Potato Fresh');
      expect(price.isStale, isTrue);
    });
  });

  group('MarketMover', () {
    test('parses mover item correctly', () {
      final json = <String, dynamic>{
        'commodity_id': 3,
        'commodity_name': 'Rice Basmati Super (New)',
        'market_name': 'Lahore',
        'current_price_pkr': 30500.0,
        'unit': 'Rs/100Kg',
        'price_date': '2026-09-02',
        'direction': 'stable',
      };

      final mover = MarketMover.fromJson(json);
      expect(mover.commodityId, 3);
      expect(mover.commodityName, 'Rice Basmati Super (New)');
      expect(mover.currentPricePkr, 30500.0);
      expect(mover.unit, 'Rs/100Kg');
    });
  });

  group('MockMarketRepository', () {
    test('returns allowlisted commodities and mock rates', () async {
      final repo = MockMarketRepository(delay: Duration.zero);
      final commodities = await repo.getCommodities();
      expect(commodities.length, 12);
      expect(commodities, contains('Wheat'));
      expect(commodities, contains('Rice Basmati Super (New)'));
      expect(commodities, contains('Tomato'));
      expect(commodities, contains('Onion'));

      final latest = await repo.getLatest(commodity: 'Rice Basmati Super (New)');
      expect(latest.crop, 'Rice Basmati Super (New)');
      expect(latest.status, ApiDataStatus.mock);
      expect(latest.unit, 'Rs/100Kg');
      expect(latest.fqpPrice, 30500.0);

      final movers = await repo.getMovers();
      expect(movers.length, 3);
      expect(movers.first.commodityName, 'Rice Basmati Super (New)');
      expect(movers.first.currentPricePkr, 30500.0);
    });
  });
}
