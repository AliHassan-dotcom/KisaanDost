import '../models/district.dart';
import '../models/weather_forecast.dart';
import '../models/weather_summary.dart';

abstract interface class WeatherRepository {
  Future<List<District>> getDistricts();
  Future<WeatherSummary> getCurrent(String district);
  Future<WeatherForecast> getForecast(String district, {int days = 7});
  Future<List<WeatherSummary>> getHistorical(String district);
}
