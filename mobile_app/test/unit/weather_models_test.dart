import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/weather_forecast.dart';
import 'package:kisaan_dost/models/weather_summary.dart';
import 'package:kisaan_dost/repositories/mock/mock_weather_repository.dart';

void main() {
  group('WeatherSummary', () {
    test('parses live Open-Meteo current response correctly', () {
      final json = <String, dynamic>{
        'district': 'Lahore',
        'normalized_district': 'Lahore District',
        'status': 'live',
        'temperature_c': 34.2,
        'humidity_percent': 58.0,
        'rainfall_mm': 0.0,
        'wind_speed_kmh': 11.5,
        'weather_code': 1,
        'weather_description': 'Mainly clear',
        'fetched_at': '2026-09-01T12:00:00Z',
        'cache_status': 'fresh_live',
        'source': 'Open-Meteo / ECMWF IFS / DWD ICON',
        'attribution': 'Weather data by Open-Meteo.com under CC BY 4.0',
        'is_mock': false,
      };

      final summary = WeatherSummary.fromJson(json);
      expect(summary.district, 'Lahore');
      expect(summary.status, ApiDataStatus.live);
      expect(summary.temperatureC, 34.2);
      expect(summary.humidityPercent, 58.0);
      expect(summary.weatherCode, 1);
      expect(summary.isMock, isFalse);
      expect(summary.isStaleCache, isFalse);
    });

    test('parses stale live cache warning correctly', () {
      final json = <String, dynamic>{
        'district': 'Faisalabad',
        'status': 'historical',
        'cache_status': 'stale_fallback',
        'warning': 'Upstream weather provider temporarily unreachable. Showing cached observation from 2026-09-01T10:00:00Z.',
        'temperature_c': 33.0,
      };

      final summary = WeatherSummary.fromJson(json);
      expect(summary.district, 'Faisalabad');
      expect(summary.isStaleCache, isTrue);
    });
  });

  group('WeatherForecast', () {
    test('parses daily and hourly forecast points', () {
      final json = <String, dynamic>{
        'district': 'Multan',
        'normalized_district': 'Multan District',
        'status': 'live',
        'forecast_days': 7,
        'daily': [
          {
            'date': '2026-09-01',
            'temperature_2m_max': 37.5,
            'precipitation_sum': 0.0,
            'precipitation_probability_max': 10.0,
          },
        ],
        'hourly': [
          {
            'time': '2026-09-01T12:00',
            'temperature_2m': 36.0,
            'relative_humidity_2m': 45.0,
          },
        ],
      };

      final forecast = WeatherForecast.fromJson(json);
      expect(forecast.district, 'Multan');
      expect(forecast.status, ApiDataStatus.live);
      expect(forecast.daily.length, 1);
      expect(forecast.daily[0].temperatureMax, 37.5);
      expect(forecast.hourly.length, 1);
      expect(forecast.hourly[0].temperature, 36.0);
    });
  });

  group('MockWeatherRepository', () {
    test('returns live mock current and forecast', () async {
      final repo = MockWeatherRepository(delay: Duration.zero);
      final current = await repo.getCurrent('Lahore');
      expect(current.district, 'Lahore');
      expect(current.status, ApiDataStatus.mock);
      expect(current.temperatureC, isNotNull);

      final forecast = await repo.getForecast('Lahore', days: 7);
      expect(forecast.daily.length, 7);
      expect(forecast.hourly.length, 24);

      final historical = await repo.getHistorical('Lahore');
      expect(historical.length, 12);
    });
  });
}
