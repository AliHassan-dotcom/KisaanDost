import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/farmer_profile.dart';
import '../repositories/profile_repository.dart';
import 'dependency_providers.dart';

class ProfileNotifier extends AsyncNotifier<FarmerProfile> {
  ProfileRepository get _repository => ref.read(profileRepositoryProvider);

  @override
  Future<FarmerProfile> build() async {
    return _repository.getProfile();
  }

  Future<void> updateProfile(Map<String, dynamic> updates) async {
    state = const AsyncLoading<FarmerProfile>();
    state = await AsyncValue.guard<FarmerProfile>(
      () => _repository.updateProfile(updates),
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading<FarmerProfile>();
    state = await AsyncValue.guard<FarmerProfile>(
      () => _repository.getProfile(),
    );
  }
}

final profileProvider =
    AsyncNotifierProvider<ProfileNotifier, FarmerProfile>(
  ProfileNotifier.new,
);
