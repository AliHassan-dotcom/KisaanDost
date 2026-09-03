import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/advisory.dart';
import '../models/pest_alert.dart';
import '../models/pest_source.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'pest_repository.dart';

class PestRepositoryImpl implements PestRepository {
  const PestRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<List<PestAlert>> getRecentAlerts({
    String? district,
    String? crop,
    String? category,
    int limit = 50,
  }) async {
    final query = <String, String>{
      if (district != null && district.isNotEmpty) 'district': district,
      if (crop != null && crop.isNotEmpty) 'crop': crop,
      if (category != null && category.isNotEmpty) 'category': category,
      'limit': limit.toString(),
    };
    final uri = AppConfig.apiUri('/pest-alerts/recent').replace(
      queryParameters: query,
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final alerts = (body['alerts'] as List<dynamic>?) ?? <dynamic>[];
    return alerts
        .whereType<Map<String, dynamic>>()
        .map(PestAlert.fromJson)
        .toList(growable: false);
  }

  @override
  Future<Advisory> getAdvisory({
    String? crop,
    String? pest,
    String? district,
  }) async {
    final body = <String, String>{
      if (crop != null && crop.isNotEmpty) 'crop': crop,
      if (pest != null && pest.isNotEmpty) 'pest': pest,
      if (district != null && district.isNotEmpty) 'district': district,
    };
    final response = await _client.post(
      AppConfig.apiUri('/pest-alerts/advisory'),
      body: body,
    );
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return Advisory.fromJson(json);
  }

  @override
  Future<List<PestSource>> getSources() async {
    final response = await _client.get(AppConfig.apiUri('/pest-alerts/sources'));
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final sources = (body['sources'] as List<dynamic>?) ?? <dynamic>[];
    return sources
        .whereType<Map<String, dynamic>>()
        .map(PestSource.fromJson)
        .toList(growable: false);
  }
}
