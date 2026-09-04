import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/advisory.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/farmer_profile.dart';
import 'package:kisaan_dost/models/pest_alert.dart';
import 'package:kisaan_dost/models/pest_citation.dart';
import 'package:kisaan_dost/models/pest_source.dart';
import 'package:kisaan_dost/providers/pest_provider.dart';
import 'package:kisaan_dost/providers/profile_provider.dart';
import 'package:kisaan_dost/screens/pest_alerts_screen.dart';

void main() {
  final alert = PestAlert(
    id: 'fact_001',
    crop: 'wheat',
    pest: 'aphid',
    status: ApiDataStatus.live,
    district: 'Lahore',
    severity: 'medium',
    explicitDoseText: '125 ml per acre',
    safetyText: 'Wear gloves.',
    recommendations: const <String>['Monitor regularly'],
  );

  final advisory = Advisory(
    crop: 'wheat',
    pest: 'aphid',
    district: 'Lahore',
    status: ApiDataStatus.live,
    sourceStatus: ApiDataStatus.live,
    matched: true,
    doseGuidance: '125 ml per acre',
    safetyNotice: 'Use protective equipment.',
    citations: const <PestCitation>[
      PestCitation(
        factId: 'c1',
        category: 'advisory',
        sourcePage: 10,
        sourceSection: 'Wheat',
        sourceExcerpt: 'Aphid advisory excerpt',
      ),
    ],
  );

  const source = PestSource(
    title: 'Annual Report',
    year: '2024-25',
    filename: 'report.pdf',
    pageCount: 120,
    numFacts: 45,
    numReviewQueue: 3,
    numChunks: 200,
    status: 'live',
  );

  const profile = FarmerProfile(
    userId: 'u1',
    name: 'Test Farmer',
    phone: '03001001000',
    district: 'Lahore',
  );

  testWidgets('PestAlertsScreen renders alerts, advisory and sources', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          pestProvider.overrideWith(
            () => _StaticPestNotifier(
              PestState(
                district: 'Lahore',
                alerts: <PestAlert>[alert],
                advisory: advisory,
                sources: const <PestSource>[source],
              ),
            ),
          ),
          profileProvider.overrideWith(() => _StaticProfileNotifier(profile)),
        ],
        child: const MaterialApp(
          home: PestAlertsScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Pest Alerts'), findsOneWidget);
    expect(find.text('wheat · aphid'), findsOneWidget);
    expect(find.text('Wear gloves.'), findsOneWidget);
  });

  testWidgets('Advisory card shows dose guidance and safety notice', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          pestProvider.overrideWith(
            () => _StaticPestNotifier(
              PestState(
                district: 'Lahore',
                alerts: const <PestAlert>[],
                advisory: advisory,
                sources: const <PestSource>[],
              ),
            ),
          ),
          profileProvider.overrideWith(() => _StaticProfileNotifier(profile)),
        ],
        child: const MaterialApp(
          home: PestAlertsScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Advisory: aphid'), findsOneWidget);
    expect(find.text('Use protective equipment.'), findsOneWidget);
    expect(find.text('Aphid advisory excerpt'), findsOneWidget);
  });
}

class _StaticPestNotifier extends PestNotifier {
  _StaticPestNotifier(this._state);

  final PestState _state;

  @override
  Future<PestState> build() async => _state;
}

class _StaticProfileNotifier extends ProfileNotifier {
  _StaticProfileNotifier(this._profile);

  final FarmerProfile _profile;

  @override
  Future<FarmerProfile> build() async => _profile;
}
