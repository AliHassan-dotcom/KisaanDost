import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/api_data_status.dart';
import '../models/market_mover.dart';
import '../models/market_price.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'market_repository.dart';

class MarketRepositoryImpl implements MarketRepository {
  const MarketRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<List<String>> getCommodities() async {
    final uri = AppConfig.apiUri('/market/commodities');
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['commodities'] as List<dynamic>?) ?? <dynamic>[];
    return list
        .map((dynamic c) => (c as Map<String, dynamic>)['commodity_name'] as String? ?? '')
        .where((name) => name.isNotEmpty)
        .toList(growable: false);
  }

  @override
  Future<MarketPrice> getLatest({
    required String commodity,
    String? market,
  }) async {
    final queryParams = <String, String>{'commodity': commodity};
    if (market != null) {
      queryParams['market'] = market;
    }
    final uri = AppConfig.apiUri('/market/latest').replace(queryParameters: queryParams);
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final records = (data['records'] as List<dynamic>?) ?? <dynamic>[];
    if (records.isNotEmpty) {
      return MarketPrice.fromJson(records.first as Map<String, dynamic>);
    }
    return MarketPrice(
      crop: commodity,
      district: market ?? 'Lahore',
      status: ApiDataStatus.unavailable,
    );
  }

  @override
  Future<List<MarketMover>> getMovers() async {
    final uri = AppConfig.apiUri('/market/movers');
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final gainers = (data['gainers'] as List<dynamic>?) ?? <dynamic>[];
    return gainers.whereType<Map<String, dynamic>>().map(MarketMover.fromJson).toList(growable: false);
  }

  @override
  Future<MarketPrice> getSummary({
    required String crop,
    required String district,
  }) async {
    final uri = AppConfig.apiUri('/market/summary').replace(
      queryParameters: <String, String>{
        'crop': crop,
        'district': district,
      },
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return MarketPrice.fromJson(
      (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
    );
  }

  @override
  Future<List<Map<String, dynamic>>> getHistory({
    required String crop,
    required String district,
  }) async {
    final uri = AppConfig.apiUri('/market/history').replace(
      queryParameters: <String, String>{
        'commodity': crop,
        'market': district,
      },
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['records'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().toList(growable: false);
  }
}
