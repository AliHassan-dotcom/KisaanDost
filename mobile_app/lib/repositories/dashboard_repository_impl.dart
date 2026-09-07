import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/farm_health_summary.dart';
import '../models/market_price.dart';
import '../models/risk_assessment.dart';
import '../models/satellite_summary.dart';
import '../models/weather_summary.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'dashboard_repository.dart';

class DashboardRepositoryImpl implements DashboardRepository {
  const DashboardRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<DashboardData> getDashboard({
    double? latitude,
    double? longitude,
    String? district,
  }) async {
    final queryParams = <String, String>{};
    if (latitude != null) queryParams['lat'] = latitude.toString();
    if (longitude != null) queryParams['lng'] = longitude.toString();
    if (district != null && district.isNotEmpty) queryParams['district'] = district;

    var uri = AppConfig.apiUri('/dashboard');
    if (queryParams.isNotEmpty) {
      uri = uri.replace(queryParameters: queryParams);
    }

    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? body;

    return DashboardData(
      user: (data['user'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
      weather: WeatherSummary.fromJson(
        (data['weather'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
      ),
      farmHealth: FarmHealthSummary.fromJson(
        (data['farm_health'] as Map<String, dynamic>?) ??
            const <String, dynamic>{},
      ),
      market: MarketPrice.fromJson(
        (data['market'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
      ),
      satellite: SatelliteSummary.fromJson(
        (data['satellite'] as Map<String, dynamic>?) ??
            const <String, dynamic>{},
      ),
      riskAssessment: data['risk_assessment'] != null
          ? RiskAssessment.fromJson(data['risk_assessment'] as Map<String, dynamic>)
          : RiskAssessment.mockDefault(),
      quickActions: _parseQuickActions(data['quick_actions']),
    );
  }

  List<Map<String, String>> _parseQuickActions(Object? value) {
    if (value is! List<dynamic>) return const <Map<String, String>>[];
    return value
        .whereType<Map<String, dynamic>>()
        .map((e) => e.map((k, v) => MapEntry(k, v.toString())))
        .toList();
  }
}
