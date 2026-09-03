import 'package:flutter/material.dart';

import '../models/weather_summary.dart';
import 'status_badge.dart';

class WeatherCard extends StatelessWidget {
  const WeatherCard({super.key, required this.summary, this.onTap});

  final WeatherSummary summary;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tempStr = summary.temperatureC != null
        ? '${summary.temperatureC!.toStringAsFixed(1)}°C'
        : '--°C';

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Text(
                    'Live Weather',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  StatusBadge(status: summary.status),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '${summary.district} · $tempStr',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              if (summary.weatherDescription != null)
                Text(
                  summary.weatherDescription!,
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                ),
              const SizedBox(height: 4),
              if (summary.humidityPercent != null)
                Text('Humidity: ${summary.humidityPercent!.toStringAsFixed(0)}%'),
              if (summary.rainfallMm != null && summary.rainfallMm! > 0)
                Text('Precipitation: ${summary.rainfallMm!.toStringAsFixed(1)} mm'),
              if (summary.windSpeedKmh != null)
                Text('Wind: ${summary.windSpeedKmh!.toStringAsFixed(1)} km/h'),
            ],
          ),
        ),
      ),
    );
  }
}
