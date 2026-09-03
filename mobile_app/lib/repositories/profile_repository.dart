import '../models/farmer_profile.dart';

abstract interface class ProfileRepository {
  Future<FarmerProfile> getProfile();
  Future<FarmerProfile> updateProfile(Map<String, dynamic> updates);
}
