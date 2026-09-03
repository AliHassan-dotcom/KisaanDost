import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/repositories/mock/mock_dashboard_repository.dart';
import 'package:kisaan_dost/screens/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard shows loading then data', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          dashboardRepositoryProvider.overrideWithValue(
            MockDashboardRepository(delay: const Duration(milliseconds: 100)),
          ),
        ],
        child: const MaterialApp(home: DashboardScreen()),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpAndSettle();

    expect(find.text('Kisaan Dost'), findsOneWidget);
    expect(find.text('Quick Actions'), findsOneWidget);
  });
}
