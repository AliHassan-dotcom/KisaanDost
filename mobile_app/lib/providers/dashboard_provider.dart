import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../repositories/dashboard_repository.dart';
import 'dependency_providers.dart';
import 'location_provider.dart';

class DashboardNotifier extends AsyncNotifier<DashboardData> {
  DashboardRepository get _repository => ref.read(dashboardRepositoryProvider);

  @override
  Future<DashboardData> build() async {
    final locationState = ref.watch(locationProvider);
    final loc = locationState.location;
    return _repository.getDashboard(
      latitude: loc.latitude,
      longitude: loc.longitude,
      district: loc.district,
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading<DashboardData>();
    final loc = ref.read(locationProvider).location;
    state = await AsyncValue.guard<DashboardData>(
      () => _repository.getDashboard(
        latitude: loc.latitude,
        longitude: loc.longitude,
        district: loc.district,
      ),
    );
  }
}

final dashboardProvider =
    AsyncNotifierProvider<DashboardNotifier, DashboardData>(
  DashboardNotifier.new,
);
