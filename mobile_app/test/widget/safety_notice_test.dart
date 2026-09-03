import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/widgets/safety_notice.dart';

void main() {
  testWidgets('SafetyNotice renders text and warning icon', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SafetyNotice(text: 'Wear protective equipment.'),
        ),
      ),
    );

    expect(find.text('Wear protective equipment.'), findsOneWidget);
    expect(find.byIcon(Icons.warning_amber_rounded), findsOneWidget);
  });
}
