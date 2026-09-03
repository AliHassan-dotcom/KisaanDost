import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/district.dart';
import '../models/weather_forecast.dart';
import '../models/weather_summary.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'weather_repository.dart';

class WeatherRepositoryImpl implements WeatherRepository {
  const WeatherRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<List<District>> getDistricts() async {
    final response = await _client.get(AppConfig.apiUri('/weather/districts'));
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final districts = (body['districts'] as List<dynamic>?) ?? <dynamic>[];
    return districts
        .whereType<String>()
        .map(District.fromJson)
        .toList(growable: false);
  }

  @override
  Future<WeatherSummary> getCurrent(String district) async {
    final uri = AppConfig.apiUri('/weather/current').replace(
      queryParameters: <String, String>{'district': district},
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return WeatherSummary.fromJson(
      (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
    );
  }

  @override
  Future<WeatherForecast> getForecast(String district, {int days = 7}) async {
    final uri = AppConfig.apiUri('/weather/forecast').replace(
      queryParameters: <String, String>{
        'district': district,
        'days': days.toString(),
      },
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return WeatherForecast.fromJson(
      (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
    );
  }

  @override
  Future<List<WeatherSummary>> getHistorical(String district) async {
    final uri = AppConfig.apiUri('/weather/historical').replace(
      queryParameters: <String, String>{'district': district},
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as List<dynamic>?) ?? <dynamic>[];
    return data
        .whereType<Map<String, dynamic>>()
        .map(WeatherSummary.fromJson)
        .toList(growable: false);
  }
}
