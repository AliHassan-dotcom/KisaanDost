import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/market_price.dart';
import 'package:kisaan_dost/widgets/market_card.dart';
import 'package:kisaan_dost/widgets/status_badge.dart';

void main() {
  testWidgets('StatusBadge renders correct label for mock', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: StatusBadge(status: ApiDataStatus.mock)),
      ),
    );

    expect(find.text('MOCK'), findsOneWidget);
  });

  testWidgets('MarketCard shows status badge', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: MarketCard(
            price: MarketPrice(
              crop: 'wheat',
              district: 'Lahore',
              status: ApiDataStatus.mock,
              currentPrice: 3200,
            ),
          ),
        ),
      ),
    );

    expect(find.text('MOCK'), findsOneWidget);
    expect(find.text('PKR 3200 per 40kg'), findsOneWidget);
  });
}
