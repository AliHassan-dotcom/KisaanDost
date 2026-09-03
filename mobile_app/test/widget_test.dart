import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/main.dart';

void main() {
  testWidgets('App renders and shows splash', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: KisaanDostApp()),
    );

    expect(find.text('Kisaan Dost'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
