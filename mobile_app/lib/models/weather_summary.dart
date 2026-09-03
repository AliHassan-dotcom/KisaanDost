import 'api_data_status.dart';

class WeatherSummary {
  const WeatherSummary({
    required this.district,
    required this.status,
    this.normalizedDistrict,
    this.year,
    this.month,
    this.temperatureC,
    this.humidityPercent,
    this.rainfallMm,
    this.precipitationMm,
    this.windSpeedKmh,
    this.windGustsKmh,
    this.weatherCode,
    this.weatherDescription,
    this.fetchedAt,
    this.expiresAt,
    this.cacheStatus,
    this.source,
    this.sourceFiles,
    this.attribution,
    this.isMock = false,
    this.warning,
  });

  final String district;
  final String? normalizedDistrict;
  final ApiDataStatus status;
  final int? year;
  final int? month;
  final double? temperatureC;
  final double? humidityPercent;
  final double? rainfallMm;
  final double? precipitationMm;
  final double? windSpeedKmh;
  final double? windGustsKmh;
  final int? weatherCode;
  final String? weatherDescription;
  final String? fetchedAt;
  final String? expiresAt;
  final String? cacheStatus;
  final String? source;
  final String? sourceFiles;
  final String? attribution;
  final bool isMock;
  final String? warning;

  bool get isStaleCache =>
      status == ApiDataStatus.historical && cacheStatus == 'stale_fallback' ||
      (warning != null && warning!.contains('temporarily unreachable'));

  factory WeatherSummary.fromJson(Map<String, dynamic> json) {
    return WeatherSummary(
      district: (json['district'] as String?) ?? 'Lahore',
      normalizedDistrict: json['normalized_district'] as String?,
      status: ApiDataStatus.fromJson(json['status'] as String?),
      year: (json['year'] as num?)?.toInt(),
      month: (json['month'] as num?)?.toInt(),
      temperatureC: (json['temperature_c'] as num?)?.toDouble(),
      humidityPercent: (json['humidity_percent'] as num?)?.toDouble(),
      rainfallMm: (json['rainfall_mm'] as num?)?.toDouble() ??
          (json['precipitation_mm'] as num?)?.toDouble(),
      precipitationMm: (json['precipitation_mm'] as num?)?.toDouble() ??
          (json['rainfall_mm'] as num?)?.toDouble(),
      windSpeedKmh: (json['wind_speed_kmh'] as num?)?.toDouble(),
      windGustsKmh: (json['wind_gusts_kmh'] as num?)?.toDouble(),
      weatherCode: (json['weather_code'] as num?)?.toInt(),
      weatherDescription: json['weather_description'] as String?,
      fetchedAt: json['fetched_at'] as String? ?? json['recorded_at'] as String?,
      expiresAt: json['expires_at'] as String?,
      cacheStatus: json['cache_status'] as String?,
      source: json['source'] as String?,
      sourceFiles: json['source_files'] as String?,
      attribution: json['attribution'] as String?,
      isMock: (json['is_mock'] as bool?) ?? false,
      warning: json['warning'] as String?,
    );
  }
}
