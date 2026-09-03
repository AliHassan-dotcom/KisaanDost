import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/farmer_profile.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'profile_repository.dart';

class ProfileRepositoryImpl implements ProfileRepository {
  const ProfileRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<FarmerProfile> getProfile() async {
    final response = await _client.get(AppConfig.apiUri('/profile'));
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    return FarmerProfile.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  @override
  Future<FarmerProfile> updateProfile(Map<String, dynamic> updates) async {
    final response = await _client.patch(
      AppConfig.apiUri('/profile'),
      body: updates,
    );
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    return FarmerProfile.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
