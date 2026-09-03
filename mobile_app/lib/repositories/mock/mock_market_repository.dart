import '../../models/api_data_status.dart';
import '../../models/market_mover.dart';
import '../../models/market_price.dart';
import '../market_repository.dart';

class MockMarketRepository implements MarketRepository {
  MockMarketRepository({this.delay = const Duration(milliseconds: 100)});

  final Duration delay;

  @override
  Future<List<String>> getCommodities() async {
    await Future<void>.delayed(delay);
    return const <String>[
      'Wheat',
      'Rice Basmati Super (New)',
      'Rice (IRRI)',
      'Maize',
      'Potato Fresh',
      'Potato Store',
      'Onion',
      'Tomato',
      'Seed Cotton(Phutti)',
      'Sugarcane',
      'Gram Black Bareek',
      'Moong',
    ];
  }

  @override
  Future<MarketPrice> getLatest({
    required String commodity,
    String? market,
  }) async {
    await Future<void>.delayed(delay);
    final prices = <String, double>{
      'wheat': 3300.0,
      'rice basmati super (new)': 30500.0,
      'rice (irri)': 6500.0,
      'maize': 2200.0,
      'potato fresh': 4200.0,
      'potato store': 3800.0,
      'onion': 20250.0,
      'tomato': 15250.0,
      'seed cotton(phutti)': 8500.0,
      'sugarcane': 450.0,
      'gram black bareek': 20000.0,
      'moong': 18000.0,
    };
    final cKey = commodity.toLowerCase();
    final fqp = prices[cKey] ?? 3000.0;

    return MarketPrice(
      crop: commodity,
      district: market ?? 'Lahore District',
      market: market ?? 'Lahore',
      status: ApiDataStatus.mock,
      unit: 'Rs/100Kg',
      currentPrice: fqp,
      minPrice: fqp - 100.0,
      maxPrice: fqp + 100.0,
      fqpPrice: fqp,
      quantity: 120.0,
      priceDate: '2026-09-02',
      sourceDisplayedDate: '02-09-2026',
      sourceName: 'Mock AMIS Provider',
      sourceUrl: 'http://www.amis.pk/ViewPrices.aspx',
      retrievedAt: '2026-09-01T12:00:00Z',
      isMock: true,
    );
  }

  @override
  Future<List<MarketMover>> getMovers() async {
    await Future<void>.delayed(delay);
    return const <MarketMover>[
      MarketMover(
        commodityId: 3,
        commodityName: 'Rice Basmati Super (New)',
        marketName: 'Lahore',
        currentPricePkr: 30500.0,
        unit: 'Rs/100Kg',
        priceDate: '2026-09-02',
        direction: 'stable',
      ),
      MarketMover(
        commodityId: 23,
        commodityName: 'Onion',
        marketName: 'Lahore',
        currentPricePkr: 20250.0,
        unit: 'Rs/100Kg',
        priceDate: '2026-09-02',
        direction: 'stable',
      ),
      MarketMover(
        commodityId: 9,
        commodityName: 'Gram Black Bareek',
        marketName: 'Lahore',
        currentPricePkr: 20000.0,
        unit: 'Rs/100Kg',
        priceDate: '2026-09-02',
        direction: 'stable',
      ),
    ];
  }

  @override
  Future<MarketPrice> getSummary({
    required String crop,
    required String district,
  }) async {
    return getLatest(commodity: crop, market: district);
  }

  @override
  Future<List<Map<String, dynamic>>> getHistory({
    required String crop,
    required String district,
  }) async {
    await Future<void>.delayed(delay);
    return const <Map<String, dynamic>>[];
  }
}
