import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/district.dart';
import 'package:kisaan_dost/models/weather_forecast.dart';
import 'package:kisaan_dost/models/weather_summary.dart';
import 'package:kisaan_dost/providers/weather_provider.dart';
import 'package:kisaan_dost/screens/weather_screen.dart';
import 'package:kisaan_dost/widgets/weather_card.dart';

class _StaticWeatherNotifier extends WeatherNotifier {
  _StaticWeatherNotifier(this._state);

  final WeatherState _state;

  @override
  Future<WeatherState> build() async {
    return _state;
  }

  @override
  Future<void> selectDistrict(District district) async {}

  @override
  Future<void> refresh() async {}
}

void main() {
  const sampleDistrict = District(name: 'Lahore');
  final sampleCurrent = WeatherSummary(
    district: 'Lahore',
    normalizedDistrict: 'Lahore District',
    status: ApiDataStatus.live,
    temperatureC: 34.2,
    humidityPercent: 58.0,
    rainfallMm: 0.0,
    precipitationMm: 0.0,
    windSpeedKmh: 11.5,
    weatherCode: 1,
    weatherDescription: 'Mainly clear',
    fetchedAt: '2026-09-01T12:00:00Z',
    cacheStatus: 'fresh_live',
    source: 'Open-Meteo / ECMWF IFS / DWD ICON',
    attribution: 'Weather data by Open-Meteo.com under CC BY 4.0',
    isMock: false,
  );

  final sampleForecast = WeatherForecast(
    district: 'Lahore',
    normalizedDistrict: 'Lahore District',
    latitude: 31.5204,
    longitude: 74.3587,
    status: ApiDataStatus.live,
    forecastDays: 3,
    daily: const [
      DailyForecastPoint(
        date: '2026-09-01',
        temperatureMax: 35.1,
        precipitationSum: 0.0,
        precipitationProbabilityMax: 10.0,
      ),
      DailyForecastPoint(
        date: '2026-09-02',
        temperatureMax: 36.0,
        precipitationSum: 2.5,
        precipitationProbabilityMax: 45.0,
      ),
    ],
  );

  final sampleHistorical = <WeatherSummary>[
    const WeatherSummary(
      district: 'Lahore',
      normalizedDistrict: 'Lahore District',
      status: ApiDataStatus.historical,
      year: 2025,
      month: 12,
      temperatureC: 18.5,
      humidityPercent: 65.0,
      rainfallMm: 12.0,
      source: 'NASA POWER Monthly Agroclimatology',
    ),
  ];

  testWidgets('WeatherScreen renders current weather, forecast, and attribution', (WidgetTester tester) async {
    final state = WeatherState(
      districts: const [sampleDistrict, District(name: 'Faisalabad')],
      selectedDistrict: sampleDistrict,
      current: sampleCurrent,
      forecast: sampleForecast,
      historical: sampleHistorical,
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          weatherProvider.overrideWith(() => _StaticWeatherNotifier(state)),
        ],
        child: const MaterialApp(
          home: WeatherScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Weather & Forecast'), findsOneWidget);
    expect(find.text('Lahore'), findsWidgets);
    expect(find.text('Mainly clear'), findsOneWidget);
    expect(find.text('34.2°C'), findsOneWidget);
    expect(find.text('7-Day Forecast'), findsOneWidget);
    expect(find.text('Weather data by Open-Meteo.com under CC BY 4.0'), findsOneWidget);
  });

  testWidgets('WeatherCard renders on dashboard with live badge and temperature', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WeatherCard(summary: sampleCurrent),
        ),
      ),
    );

    expect(find.text('Live Weather'), findsOneWidget);
    expect(find.text('Lahore · 34.2°C'), findsOneWidget);
    expect(find.text('Mainly clear'), findsOneWidget);
    expect(find.text('Humidity: 58%'), findsOneWidget);
  });
}
