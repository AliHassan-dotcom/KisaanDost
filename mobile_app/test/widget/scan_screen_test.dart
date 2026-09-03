import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/repositories/mock/mock_scan_repository.dart';
import 'package:kisaan_dost/screens/scan_screen.dart';

void main() {
  testWidgets('Scan screen shows image picker buttons', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          scanRepositoryProvider.overrideWithValue(MockScanRepository()),
        ],
        child: const MaterialApp(home: ScanScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Camera'), findsOneWidget);
    expect(find.text('Gallery'), findsOneWidget);
    expect(find.text('Scan'), findsOneWidget);
  });
}
