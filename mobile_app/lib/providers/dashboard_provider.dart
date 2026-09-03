import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../repositories/dashboard_repository.dart';
import 'dependency_providers.dart';

class DashboardNotifier extends AsyncNotifier<DashboardData> {
  DashboardRepository get _repository => ref.read(dashboardRepositoryProvider);

  @override
  Future<DashboardData> build() async {
    return _repository.getDashboard();
  }

  Future<void> refresh() async {
    state = const AsyncLoading<DashboardData>();
    state = await AsyncValue.guard<DashboardData>(
      () => _repository.getDashboard(),
    );
  }
}

final dashboardProvider =
    AsyncNotifierProvider<DashboardNotifier, DashboardData>(
  DashboardNotifier.new,
);
