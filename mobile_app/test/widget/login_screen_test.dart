import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/repositories/mock/mock_auth_repository.dart';
import 'package:kisaan_dost/routing/app_router.dart';
import 'package:kisaan_dost/screens/login_screen.dart';

void main() {
  testWidgets('Login screen validates empty fields', (tester) async {
    final router = GoRouter(
      initialLocation: AppRoutes.login,
      routes: <RouteBase>[
        GoRoute(
          path: AppRoutes.login,
          builder: (context, state) => const LoginScreen(),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          authRepositoryProvider.overrideWithValue(MockAuthRepository()),
        ],
        child: MaterialApp.router(
          theme: ThemeData(splashFactory: InkRipple.splashFactory),
          routerConfig: router,
        ),
      ),
    );

    await tester.tap(find.widgetWithText(ElevatedButton, 'Login'));
    await tester.pumpAndSettle();

    expect(find.text('Phone number is required'), findsOneWidget);
    expect(find.text('Password must be at least 6 characters'), findsOneWidget);
  });
}
