import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/agri_gdp.dart';
import '../models/agri_trade.dart';
import '../models/land_utilization.dart';
import '../models/water_availability.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'agri_stats_repository.dart';

class AgriStatsRepositoryImpl implements AgriStatsRepository {
  const AgriStatsRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<List<LandUtilization>> getLandUtilization({String? district}) async {
    final queryParams = <String, String>{};
    if (district != null && district.isNotEmpty) {
      queryParams['district'] = district;
    }
    final uri = AppConfig.apiUri('/agri/land-utilization').replace(queryParameters: queryParams);
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['data'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(LandUtilization.fromJson).toList(growable: false);
  }

  @override
  Future<List<WaterAvailability>> getWaterAvailability({String? district}) async {
    final queryParams = <String, String>{};
    if (district != null && district.isNotEmpty) {
      queryParams['district'] = district;
    }
    final uri = AppConfig.apiUri('/agri/water-availability').replace(queryParameters: queryParams);
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['data'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(WaterAvailability.fromJson).toList(growable: false);
  }

  @override
  Future<List<AgriGdp>> getGdp({String? province}) async {
    final queryParams = <String, String>{};
    if (province != null && province.isNotEmpty) {
      queryParams['province'] = province;
    }
    final uri = AppConfig.apiUri('/agri/gdp').replace(queryParameters: queryParams);
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['data'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(AgriGdp.fromJson).toList(growable: false);
  }

  @override
  Future<List<AgriTradeItem>> getExports({String? commodity}) async {
    final queryParams = <String, String>{};
    if (commodity != null && commodity.isNotEmpty) {
      queryParams['commodity'] = commodity;
    }
    final uri = AppConfig.apiUri('/agri/exports').replace(queryParameters: queryParams);
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['data'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(AgriTradeItem.fromJson).toList(growable: false);
  }

  @override
  Future<List<AgriTradeItem>> getImports({String? commodity}) async {
    final queryParams = <String, String>{};
    if (commodity != null && commodity.isNotEmpty) {
      queryParams['commodity'] = commodity;
    }
    final uri = AppConfig.apiUri('/agri/imports').replace(queryParameters: queryParams);
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['data'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(AgriTradeItem.fromJson).toList(growable: false);
  }

  @override
  Future<List<AgriTradeSummary>> getTradeSummary() async {
    final uri = AppConfig.apiUri('/agri/trade-summary');
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['data'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(AgriTradeSummary.fromJson).toList(growable: false);
  }
}

