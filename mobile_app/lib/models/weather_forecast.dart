import 'api_data_status.dart';

class DailyForecastPoint {
  const DailyForecastPoint({
    required this.date,
    this.temperatureMax,
    this.temperatureMin,
    this.precipitationSum,
    this.precipitationProbabilityMax,
    this.shortwaveRadiationSum,
    this.et0,
  });

  final String date;
  final double? temperatureMax;
  final double? temperatureMin;
  final double? precipitationSum;
  final double? precipitationProbabilityMax;
  final double? shortwaveRadiationSum;
  final double? et0;

  factory DailyForecastPoint.fromJson(Map<String, dynamic> json) {
    return DailyForecastPoint(
      date: json['date'] as String,
      temperatureMax: (json['temperature_2m_max'] as num?)?.toDouble(),
      temperatureMin: (json['temperature_2m_min'] as num?)?.toDouble(),
      precipitationSum: (json['precipitation_sum'] as num?)?.toDouble(),
      precipitationProbabilityMax:
          (json['precipitation_probability_max'] as num?)?.toDouble(),
      shortwaveRadiationSum:
          (json['shortwave_radiation_sum'] as num?)?.toDouble(),
      et0: (json['et0_fao_evapotranspiration'] as num?)?.toDouble(),
    );
  }
}

class HourlyForecastPoint {
  const HourlyForecastPoint({
    required this.time,
    this.temperature,
    this.relativeHumidity,
    this.dewpoint,
    this.precipitation,
    this.vpd,
    this.et0,
    this.windSpeed,
    this.windGusts,
    this.weatherCode,
    this.soilTemperature0cm,
    this.soilTemperature6cm,
    this.soilTemperature18cm,
    this.soilMoisture0to1cm,
    this.soilMoisture1to3cm,
    this.soilMoisture3to9cm,
    this.soilMoisture9to27cm,
    this.shortwaveRadiation,
    this.directNormalIrradiance,
  });

  final String time;
  final double? temperature;
  final double? relativeHumidity;
  final double? dewpoint;
  final double? precipitation;
  final double? vpd;
  final double? et0;
  final double? windSpeed;
  final double? windGusts;
  final int? weatherCode;
  final double? soilTemperature0cm;
  final double? soilTemperature6cm;
  final double? soilTemperature18cm;
  final double? soilMoisture0to1cm;
  final double? soilMoisture1to3cm;
  final double? soilMoisture3to9cm;
  final double? soilMoisture9to27cm;
  final double? shortwaveRadiation;
  final double? directNormalIrradiance;

  factory HourlyForecastPoint.fromJson(Map<String, dynamic> json) {
    return HourlyForecastPoint(
      time: json['time'] as String,
      temperature: (json['temperature_2m'] as num?)?.toDouble(),
      relativeHumidity: (json['relative_humidity_2m'] as num?)?.toDouble(),
      dewpoint: (json['dewpoint_2m'] as num?)?.toDouble(),
      precipitation: (json['precipitation'] as num?)?.toDouble(),
      vpd: (json['vapour_pressure_deficit'] as num?)?.toDouble(),
      et0: (json['et0_fao_evapotranspiration'] as num?)?.toDouble(),
      windSpeed: (json['wind_speed_10m'] as num?)?.toDouble(),
      windGusts: (json['wind_gusts_10m'] as num?)?.toDouble(),
      weatherCode: (json['weather_code'] as num?)?.toInt(),
      soilTemperature0cm: (json['soil_temperature_0cm'] as num?)?.toDouble(),
      soilTemperature6cm: (json['soil_temperature_6cm'] as num?)?.toDouble(),
      soilTemperature18cm: (json['soil_temperature_18cm'] as num?)?.toDouble(),
      soilMoisture0to1cm: (json['soil_moisture_0_to_1cm'] as num?)?.toDouble(),
      soilMoisture1to3cm: (json['soil_moisture_1_to_3cm'] as num?)?.toDouble(),
      soilMoisture3to9cm: (json['soil_moisture_3_to_9cm'] as num?)?.toDouble(),
      soilMoisture9to27cm: (json['soil_moisture_9_to_27cm'] as num?)?.toDouble(),
      shortwaveRadiation: (json['shortwave_radiation'] as num?)?.toDouble(),
      directNormalIrradiance: (json['direct_normal_irradiance'] as num?)?.toDouble(),
    );
  }
}

class WeatherForecast {
  const WeatherForecast({
    required this.district,
    required this.normalizedDistrict,
    required this.latitude,
    required this.longitude,
    required this.status,
    required this.forecastDays,
    this.fetchedAt,
    this.expiresAt,
    this.cacheStatus,
    this.daily = const <DailyForecastPoint>[],
    this.hourly = const <HourlyForecastPoint>[],
    this.source,
    this.attribution,
    this.warning,
  });

  final String district;
  final String normalizedDistrict;
  final double latitude;
  final double longitude;
  final ApiDataStatus status;
  final int forecastDays;
  final String? fetchedAt;
  final String? expiresAt;
  final String? cacheStatus;
  final List<DailyForecastPoint> daily;
  final List<HourlyForecastPoint> hourly;
  final String? source;
  final String? attribution;
  final String? warning;

  factory WeatherForecast.fromJson(Map<String, dynamic> json) {
    final dailyList = (json['daily'] as List<dynamic>?) ?? <dynamic>[];
    final hourlyList = (json['hourly'] as List<dynamic>?) ?? <dynamic>[];

    return WeatherForecast(
      district: (json['district'] as String?) ?? 'Lahore',
      normalizedDistrict: (json['normalized_district'] as String?) ?? 'Lahore District',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 31.5204,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 74.3587,
      status: ApiDataStatus.fromJson(json['status'] as String?),
      forecastDays: (json['forecast_days'] as num?)?.toInt() ?? 7,
      fetchedAt: json['fetched_at'] as String?,
      expiresAt: json['expires_at'] as String?,
      cacheStatus: json['cache_status'] as String?,
      daily: dailyList
          .map((dynamic d) => DailyForecastPoint.fromJson(d as Map<String, dynamic>))
          .toList(),
      hourly: hourlyList
          .map((dynamic h) => HourlyForecastPoint.fromJson(h as Map<String, dynamic>))
          .toList(),
      source: json['source'] as String?,
      attribution: json['attribution'] as String?,
      warning: json['warning'] as String?,
    );
  }
}
