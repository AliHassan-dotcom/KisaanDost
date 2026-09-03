import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/advisory.dart';
import '../models/pest_alert.dart';
import '../models/pest_source.dart';
import '../repositories/pest_repository.dart';
import 'dependency_providers.dart';

class PestNotifier extends AsyncNotifier<PestState> {
  PestRepository get _repository => ref.read(pestRepositoryProvider);

  @override
  Future<PestState> build() async {
    final alerts = await _repository.getRecentAlerts(district: 'Lahore');
    final sources = await _repository.getSources();
    return PestState(alerts: alerts, sources: sources);
  }

  Future<void> loadAlerts({
    String? district,
    String? crop,
    String? category,
    int limit = 50,
  }) async {
    state = const AsyncLoading<PestState>();
    state = await AsyncValue.guard<PestState>(() async {
      final alerts = await _repository.getRecentAlerts(
        district: district,
        crop: crop,
        category: category,
        limit: limit,
      );
      final current = state.value;
      return PestState(
        district: district ?? current?.district ?? 'Lahore',
        crop: crop ?? current?.crop,
        category: category ?? current?.category,
        alerts: alerts,
        advisory: current?.advisory,
        sources: current?.sources ?? const <PestSource>[],
      );
    });
  }

  Future<void> loadSources() async {
    state = const AsyncLoading<PestState>();
    state = await AsyncValue.guard<PestState>(() async {
      final sources = await _repository.getSources();
      final current = state.value;
      return PestState(
        district: current?.district ?? 'Lahore',
        crop: current?.crop,
        category: current?.category,
        alerts: current?.alerts ?? const <PestAlert>[],
        advisory: current?.advisory,
        sources: sources,
      );
    });
  }

  Future<void> getAdvisory({
    String? crop,
    String? pest,
    String? district,
  }) async {
    state = const AsyncLoading<PestState>();
    state = await AsyncValue.guard<PestState>(() async {
      final advisory = await _repository.getAdvisory(
        crop: crop,
        pest: pest,
        district: district,
      );
      final current = state.value;
      return PestState(
        district: current?.district ?? district ?? 'Lahore',
        crop: current?.crop ?? crop,
        category: current?.category,
        alerts: current?.alerts ?? const <PestAlert>[],
        advisory: advisory,
        sources: current?.sources ?? const <PestSource>[],
      );
    });
  }
}

class PestState {
  const PestState({
    this.district = 'Lahore',
    this.crop,
    this.category,
    this.alerts = const <PestAlert>[],
    this.advisory,
    this.sources = const <PestSource>[],
  });

  final String district;
  final String? crop;
  final String? category;
  final List<PestAlert> alerts;
  final Advisory? advisory;
  final List<PestSource> sources;
}

final pestProvider = AsyncNotifierProvider<PestNotifier, PestState>(
  PestNotifier.new,
);
