import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/satellite_coverage.dart';
import '../models/satellite_record.dart';
import '../models/satellite_summary.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'satellite_repository.dart';

class SatelliteRepositoryImpl implements SatelliteRepository {
  const SatelliteRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<SatelliteSummary> getSummary({
    required String district,
    required String crop,
  }) async {
    return getLatest(district: district, crop: crop);
  }

  @override
  Future<SatelliteSummary> getLatest({
    required String district,
    required String crop,
  }) async {
    final uri = AppConfig.apiUri('/satellite/latest').replace(
      queryParameters: <String, String>{
        'district': district,
      },
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = body.containsKey('data') ? (body['data'] as Map<String, dynamic>) : body;
    final summaryJson = Map<String, dynamic>.from(data);
    summaryJson['crop'] = crop;
    return SatelliteSummary.fromJson(summaryJson);
  }

  @override
  Future<List<SatelliteRecord>> getHistory({
    required String district,
    String? start,
    String? end,
  }) async {
    final queryParams = <String, String>{'district': district};
    if (start != null) queryParams['start'] = start;
    if (end != null) queryParams['end'] = end;

    final uri = AppConfig.apiUri('/satellite/history').replace(
      queryParameters: queryParams,
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = body.containsKey('data') ? (body['data'] as Map<String, dynamic>) : body;
    final recordsList = (data['records'] as List<dynamic>?) ?? <dynamic>[];
    return recordsList
        .map((dynamic r) => SatelliteRecord.fromJson(r as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<SatelliteCoverage> getCoverage({required String district}) async {
    final uri = AppConfig.apiUri('/satellite/coverage').replace(
      queryParameters: <String, String>{
        'district': district,
      },
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = body.containsKey('data') ? (body['data'] as Map<String, dynamic>) : body;
    return SatelliteCoverage.fromJson(data);
  }

  @override
  Future<List<String>> getDistricts() async {
    final uri = AppConfig.apiUri('/satellite/districts');
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = body.containsKey('data') ? (body['data'] as Map<String, dynamic>) : body;
    final list = (data['districts'] as List<dynamic>?) ?? <dynamic>[];
    return list
        .map((dynamic d) => (d as Map<String, dynamic>)['district'] as String)
        .toList();
  }
}
