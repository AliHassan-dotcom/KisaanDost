import '../../models/api_data_status.dart';
import '../../models/district.dart';
import '../../models/weather_forecast.dart';
import '../../models/weather_summary.dart';
import '../weather_repository.dart';

class MockWeatherRepository implements WeatherRepository {
  MockWeatherRepository({this.delay = const Duration(milliseconds: 100)});

  final Duration delay;

  static const List<String> _districtNames = <String>[
    'Attock', 'Bahawalnagar', 'Bahawalpur', 'Bhakkar',
    'Chakwal', 'Dera Ghazi Khan', 'Faisalabad', 'Gujranwala',
    'Gujrat', 'Hafizabad', 'Jhang', 'Jhelum',
    'Kasur', 'Khanewal', 'Khushab', 'Lahore',
    'Layyah', 'Lodhran', 'Mandi Bahauddin', 'Mianwali',
    'Multan', 'Muzaffargarh', 'Narowal', 'Okara',
    'Pakpattan', 'Rahim Yar Khan', 'Rajanpur', 'Rawalpindi',
    'Sahiwal', 'Sargodha', 'Sheikhupura', 'Sialkot',
    'Toba Tek Singh', 'Vehari',
  ];

  @override
  Future<List<District>> getDistricts() async {
    await Future<void>.delayed(delay);
    return _districtNames.map((name) => District(name: name)).toList();
  }

  @override
  Future<WeatherSummary> getCurrent(String district) async {
    await Future<void>.delayed(delay);
    return WeatherSummary(
      district: district,
      normalizedDistrict: '$district District',
      status: ApiDataStatus.mock,
      temperatureC: 33.5,
      humidityPercent: 55.0,
      rainfallMm: 0.0,
      precipitationMm: 0.0,
      windSpeedKmh: 12.0,
      weatherCode: 1,
      weatherDescription: 'Mainly clear',
      fetchedAt: '2026-09-01T12:00:00Z',
      expiresAt: '2026-09-01T12:30:00Z',
      cacheStatus: 'fresh_live',
      source: 'Mock Open-Meteo Provider',
      attribution: 'Weather data by Open-Meteo.com under CC BY 4.0',
      isMock: true,
    );
  }

  @override
  Future<WeatherForecast> getForecast(String district, {int days = 7}) async {
    await Future<void>.delayed(delay);
    final daily = <DailyForecastPoint>[];
    for (int i = 0; i < days; i++) {
      final dateStr = '2026-09-${(i + 1).toString().padLeft(2, '0')}';
      daily.add(DailyForecastPoint(
        date: dateStr,
        temperatureMax: 34.0 + (i % 3) * 1.5,
        temperatureMin: 24.0 + (i % 2) * 1.0,
        precipitationSum: i == 2 ? 3.5 : 0.0,
        precipitationProbabilityMax: i == 2 ? 60.0 : 15.0,
        shortwaveRadiationSum: 22.0,
        et0: 5.0,
      ));
    }

    final hourly = <HourlyForecastPoint>[];
    for (int h = 0; h < 24; h++) {
      hourly.add(HourlyForecastPoint(
        time: '2026-09-01T${h.toString().padLeft(2, '0')}:00',
        temperature: 28.0 + (h > 6 && h < 18 ? (18 - (h - 13).abs()) * 0.8 : 0.0),
        relativeHumidity: 60.0 - (h > 6 && h < 18 ? 15.0 : 0.0),
        precipitation: 0.0,
        windSpeed: 10.0,
        weatherCode: 1,
      ));
    }

    return WeatherForecast(
      district: district,
      normalizedDistrict: '$district District',
      latitude: 31.5204,
      longitude: 74.3587,
      status: ApiDataStatus.mock,
      forecastDays: days,
      fetchedAt: '2026-09-01T12:00:00Z',
      expiresAt: '2026-09-01T13:00:00Z',
      cacheStatus: 'fresh_live',
      daily: daily,
      hourly: hourly,
      source: 'Mock Open-Meteo Provider',
      attribution: 'Weather data by Open-Meteo.com under CC BY 4.0',
    );
  }

  @override
  Future<List<WeatherSummary>> getHistorical(String district) async {
    await Future<void>.delayed(delay);
    final list = <WeatherSummary>[];
    for (int m = 1; m <= 12; m++) {
      list.add(WeatherSummary(
        district: district,
        normalizedDistrict: '$district District',
        status: ApiDataStatus.historical,
        year: 2025,
        month: m,
        temperatureC: 22.0 + (m >= 5 && m <= 8 ? 12.0 : 0.0),
        humidityPercent: 50.0 + (m >= 7 ? 20.0 : 0.0),
        rainfallMm: m == 7 || m == 8 ? 65.0 : 5.0,
        source: 'NASA POWER Monthly Agroclimatology',
      ));
    }
    return list;
  }
}
