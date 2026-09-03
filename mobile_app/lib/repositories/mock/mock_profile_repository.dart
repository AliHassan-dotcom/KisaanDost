import '../../models/farmer_profile.dart';
import '../../repositories/profile_repository.dart';

class MockProfileRepository implements ProfileRepository {
  MockProfileRepository({this.delay = const Duration(milliseconds: 200)});

  final Duration delay;
  FarmerProfile _profile = const FarmerProfile(
    userId: 'user_000001',
    name: 'Test Farmer',
    phone: '03001001000',
    district: 'Lahore',
    crop: 'wheat',
    farmSizeAcres: 12.5,
    irrigationType: 'canal',
    language: 'en',
  );

  @override
  Future<FarmerProfile> getProfile() async {
    await Future<void>.delayed(delay);
    return _profile;
  }

  @override
  Future<FarmerProfile> updateProfile(Map<String, dynamic> updates) async {
    await Future<void>.delayed(delay);
    _profile = _profile.copyWith(
      name: updates['name'] as String?,
      email: updates['email'] as String?,
      district: updates['district'] as String?,
      crop: updates['crop'] as String?,
      farmSizeAcres: (updates['farm_size_acres'] as num?)?.toDouble(),
      irrigationType: updates['irrigation_type'] as String?,
      language: updates['language'] as String?,
    );
    return _profile;
  }
}
