import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/advisory.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/pest_alert.dart';
import 'package:kisaan_dost/models/pest_source.dart';
import 'package:kisaan_dost/providers/dependency_providers.dart';
import 'package:kisaan_dost/providers/pest_provider.dart';
import 'package:kisaan_dost/repositories/pest_repository.dart';

import '../helpers/test_container.dart';

class FakePestRepository implements PestRepository {
  String? lastDistrict;
  String? lastCrop;
  String? lastPest;

  @override
  Future<List<PestAlert>> getRecentAlerts({
    String? district,
    String? crop,
    String? category,
    int limit = 50,
  }) async {
    lastDistrict = district;
    lastCrop = crop;
    return <PestAlert>[
      PestAlert(
        id: 'fact_001',
        crop: crop ?? 'wheat',
        pest: 'aphid',
        status: ApiDataStatus.live,
        district: district,
      ),
    ];
  }

  @override
  Future<Advisory> getAdvisory({
    String? crop,
    String? pest,
    String? district,
  }) async {
    lastCrop = crop;
    lastPest = pest;
    return Advisory(
      crop: crop,
      pest: pest,
      district: district,
      status: ApiDataStatus.live,
      sourceStatus: ApiDataStatus.live,
      matched: true,
    );
  }

  @override
  Future<List<PestSource>> getSources() async {
    return const <PestSource>[
      PestSource(
        title: 'Annual Report',
        year: '2024-25',
        filename: 'report.pdf',
        pageCount: 1,
        numFacts: 1,
        numReviewQueue: 0,
        numChunks: 1,
        status: 'live',
      ),
    ];
  }
}

void main() {
  group('PestNotifier', () {
    test('build loads alerts and sources', () async {
      final repo = FakePestRepository();
      final container = createContainer(
        overrides: <Override>[
          pestRepositoryProvider.overrideWithValue(repo),
        ],
      );

      final state = await container.read(pestProvider.future);

      expect(state.alerts, hasLength(1));
      expect(state.alerts.first.pest, 'aphid');
      expect(state.sources, hasLength(1));
      expect(state.sources.first.status, 'live');
      expect(repo.lastDistrict, 'Lahore');
    });

    test('loadAlerts passes optional filters', () async {
      final repo = FakePestRepository();
      final container = createContainer(
        overrides: <Override>[
          pestRepositoryProvider.overrideWithValue(repo),
        ],
      );

      await container.read(pestProvider.future);
      await container
          .read(pestProvider.notifier)
          .loadAlerts(district: 'Faisalabad', crop: 'rice', limit: 10);

      expect(repo.lastDistrict, 'Faisalabad');
      expect(repo.lastCrop, 'rice');
      expect(container.read(pestProvider).value?.district, 'Faisalabad');
      expect(container.read(pestProvider).value?.alerts.first.crop, 'rice');
    });

    test('getAdvisory updates advisory in state', () async {
      final repo = FakePestRepository();
      final container = createContainer(
        overrides: <Override>[
          pestRepositoryProvider.overrideWithValue(repo),
        ],
      );

      await container.read(pestProvider.future);
      await container
          .read(pestProvider.notifier)
          .getAdvisory(crop: 'wheat', pest: 'aphid', district: 'Lahore');

      expect(repo.lastCrop, 'wheat');
      expect(repo.lastPest, 'aphid');
      final state = container.read(pestProvider).value;
      expect(state?.advisory, isNotNull);
      expect(state?.advisory?.matched, isTrue);
    });
  });
}
