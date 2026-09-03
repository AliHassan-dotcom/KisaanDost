import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/market_mover.dart';
import 'package:kisaan_dost/models/market_price.dart';
import 'package:kisaan_dost/providers/market_provider.dart';
import 'package:kisaan_dost/screens/market_screen.dart';
import 'package:kisaan_dost/widgets/market_card.dart';

class _StaticMarketNotifier extends MarketNotifier {
  _StaticMarketNotifier(this._state);

  final MarketState _state;

  @override
  Future<MarketState> build() async {
    return _state;
  }

  @override
  Future<void> selectCommodity(String crop, {String district = 'Lahore'}) async {}

  @override
  Future<void> load({required String crop, required String district}) async {}

  @override
  Future<void> refresh() async {}
}

void main() {
  final samplePrice = MarketPrice(
    crop: 'Rice Basmati Super (New)',
    commodityId: 3,
    district: 'Lahore District',
    market: 'Lahore',
    status: ApiDataStatus.live,
    validationStatus: 'validated',
    unit: 'Rs/100Kg',
    minPrice: 30500.0,
    maxPrice: 30500.0,
    fqpPrice: 30500.0,
    currentPrice: 30500.0,
    priceDate: '2026-09-02',
    sourceDisplayedDate: '02-09-2026',
    sourceName: 'Official AMIS Punjab',
    sourceUrl: 'http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=3',
    retrievedAt: '2026-09-01T22:07:50Z',
    isMock: false,
  );

  final sampleMovers = const [
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
  ];

  testWidgets('MarketScreen renders commodity selector, movers, and provenance', (WidgetTester tester) async {
    final state = MarketState(
      crop: 'Rice Basmati Super (New)',
      district: 'Lahore District',
      commodities: const [
        'Wheat',
        'Rice Basmati Super (New)',
        'Tomato',
        'Onion',
      ],
      price: samplePrice,
      movers: sampleMovers,
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          marketProvider.overrideWith(() => _StaticMarketNotifier(state)),
        ],
        child: const MaterialApp(
          home: MarketScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Market Rates (AMIS Punjab)'), findsOneWidget);
    expect(find.text('Observed Market Rates (Lahore Mandi):'), findsOneWidget);
    expect(find.text('Onion'), findsWidgets);
    expect(find.text('PKR 20250'), findsOneWidget);
    expect(find.text('Select Commodity:'), findsOneWidget);
    expect(find.text('Rice Basmati Super (New)'), findsWidgets);
    expect(find.text('PKR 30500'), findsWidgets);
    expect(find.text('Unit: Rs/100Kg'), findsOneWidget);
    expect(find.textContaining('Official AMIS Punjab'), findsOneWidget);
  });

  testWidgets('MarketCard renders on dashboard with live rate and unit', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MarketCard(price: samplePrice),
        ),
      ),
    );

    expect(find.text('Market Rates'), findsOneWidget);
    expect(find.text('Rice Basmati Super (New) · Lahore'), findsOneWidget);
    expect(find.text('PKR 30500 Rs/100Kg'), findsOneWidget);
    expect(find.text('Dated: 02-09-2026'), findsOneWidget);
  });
}
