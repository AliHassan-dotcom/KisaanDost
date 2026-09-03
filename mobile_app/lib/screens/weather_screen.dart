import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/api_data_status.dart';
import '../models/weather_forecast.dart';
import '../models/weather_summary.dart';
import '../providers/settings_provider.dart';
import '../providers/weather_provider.dart';
import '../widgets/district_selector.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/status_badge.dart';

class WeatherScreen extends ConsumerWidget {
  const WeatherScreen({super.key});

  IconData _getWeatherIcon(int? code) {
    if (code == null) return Icons.wb_sunny_outlined;
    if (code == 0) return Icons.wb_sunny;
    if (code <= 3) return Icons.cloud_queue;
    if (code <= 48) return Icons.cloud;
    if (code <= 67) return Icons.water_drop;
    if (code <= 82) return Icons.grain;
    return Icons.thunderstorm;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final weatherAsync = ref.watch(weatherProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'موسم کی تفصیلات' : 'Weather & Forecast',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(weatherProvider.notifier).refresh(),
          ),
        ],
      ),
      body: weatherAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'موسم کا ڈیٹا لوڈ نہیں ہو سکا' : 'Failed to load weather',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  '$error',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(weatherProvider.notifier).refresh(),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) => RefreshIndicator(
          onRefresh: () => ref.read(weatherProvider.notifier).refresh(),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                DistrictSelector(
                  districts: state.districts,
                  selected: state.selectedDistrict,
                  onSelected: (district) =>
                      ref.read(weatherProvider.notifier).selectDistrict(district),
                ),
                const SizedBox(height: 16),

                if (state.current != null) ...<Widget>[
                  // Live Current Weather Card
                  _buildCurrentWeatherCard(context, state.current!, isUrdu),
                  const SizedBox(height: 16),

                  // Stale Fallback Warning Banner
                  if (state.current!.isStaleCache || state.current!.warning != null)
                    _buildWarningBanner(context, state.current!.warning ?? 'Showing cached weather observation.'),

                  // 7-Day Forecast Section
                  if (state.forecast != null && state.forecast!.daily.isNotEmpty) ...<Widget>[
                    _buildForecastSection(context, state.forecast!, isUrdu),
                    const SizedBox(height: 16),
                  ],

                  // Historical NASA POWER Monthly Weather Section
                  _buildHistoricalSection(context, state.historical, isUrdu),
                  const SizedBox(height: 16),

                  // Open-Meteo CC BY 4.0 Attribution Footer
                  _buildAttributionFooter(context, state.current!),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCurrentWeatherCard(
    BuildContext context,
    WeatherSummary current,
    bool isUrdu,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(_getWeatherIcon(current.weatherCode), color: Colors.amber.shade800, size: 28),
                    const SizedBox(width: 8),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          current.district,
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          current.weatherDescription ?? (isUrdu ? 'موسم کا حال' : 'Live Observation'),
                          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ],
                ),
                StatusBadge(status: current.status),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                Text(
                  current.temperatureC != null
                      ? '${current.temperatureC!.toStringAsFixed(1)}°C'
                      : '--°C',
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: <Widget>[
                    if (current.humidityPercent != null)
                      Text(
                        isUrdu ? 'نمی: ${current.humidityPercent!.toStringAsFixed(0)}%' : 'Humidity: ${current.humidityPercent!.toStringAsFixed(0)}%',
                        style: const TextStyle(fontSize: 13),
                      ),
                    if (current.rainfallMm != null)
                      Text(
                        isUrdu ? 'بارش: ${current.rainfallMm!.toStringAsFixed(1)} ملی میٹر' : 'Precipitation: ${current.rainfallMm!.toStringAsFixed(1)} mm',
                        style: const TextStyle(fontSize: 13),
                      ),
                    if (current.windSpeedKmh != null)
                      Text(
                        isUrdu ? 'ہوا: ${current.windSpeedKmh!.toStringAsFixed(1)} کلومیٹر/گھنٹہ' : 'Wind: ${current.windSpeedKmh!.toStringAsFixed(1)} km/h',
                        style: const TextStyle(fontSize: 13),
                      ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWarningBanner(BuildContext context, String warning) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.amber.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.amber.shade300),
      ),
      child: Row(
        children: <Widget>[
          Icon(Icons.info_outline, size: 20, color: Colors.amber.shade900),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              warning,
              style: TextStyle(fontSize: 12, color: Colors.amber.shade900),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildForecastSection(
    BuildContext context,
    WeatherForecast forecast,
    bool isUrdu,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          isUrdu ? '7 دن کی پیشین گوئی' : '7-Day Forecast',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 120,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: forecast.daily.length,
            itemBuilder: (context, index) {
              final day = forecast.daily[index];
              return Card(
                elevation: 1,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                margin: const EdgeInsets.only(right: 8),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: <Widget>[
                      Text(
                        day.date.length >= 10 ? day.date.substring(5) : day.date,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                      const SizedBox(height: 6),
                      Icon(Icons.wb_sunny_outlined, size: 22, color: Colors.orange.shade700),
                      const SizedBox(height: 6),
                      Text(
                        day.temperatureMax != null ? '${day.temperatureMax!.toStringAsFixed(0)}°C' : '--',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      if (day.precipitationProbabilityMax != null && day.precipitationProbabilityMax! > 0)
                        Text(
                          '${day.precipitationProbabilityMax!.toStringAsFixed(0)}% rain',
                          style: TextStyle(fontSize: 10, color: Colors.blue.shade700),
                        ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildHistoricalSection(
    BuildContext context,
    List<WeatherSummary> historical,
    bool isUrdu,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          isUrdu ? 'تاریخی ماہانہ موسم (NASA POWER)' : 'Historical Weather Baseline (NASA POWER)',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        if (historical.isEmpty)
          const Text('No historical observations recorded.')
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: historical.length.clamp(0, 6),
            itemBuilder: (context, index) {
              final item = historical[index];
              final periodStr = item.year != null && item.month != null
                  ? '${item.year}-${item.month.toString().padLeft(2, '0')}'
                  : 'Historical';
              return Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 6),
                color: Colors.grey.shade50,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(6),
                  side: BorderSide(color: Colors.grey.shade300),
                ),
                child: ListTile(
                  dense: true,
                  title: Text(periodStr, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  subtitle: Text(
                    '${item.temperatureC?.toStringAsFixed(1) ?? '--'}°C · '
                    '${item.humidityPercent?.toStringAsFixed(0) ?? '--'}% humidity · '
                    '${item.rainfallMm?.toStringAsFixed(1) ?? '--'} mm rain',
                    style: const TextStyle(fontSize: 12),
                  ),
                  trailing: const StatusBadge(status: ApiDataStatus.historical),
                ),
              );
            },
          ),
      ],
    );
  }

  Widget _buildAttributionFooter(BuildContext context, WeatherSummary current) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Center(
        child: Text(
          current.attribution ?? 'Weather data by Open-Meteo.com under CC BY 4.0',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 11, color: Colors.grey.shade600, fontStyle: FontStyle.italic),
        ),
      ),
    );
  }
}
