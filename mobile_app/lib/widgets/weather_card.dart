import 'package:flutter/material.dart';

import '../models/weather_summary.dart';
import 'status_badge.dart';

class WeatherCard extends StatelessWidget {
  const WeatherCard({
    super.key,
    required this.summary,
    this.onTap,
    this.isUrdu = false,
  });

  final WeatherSummary summary;
  final VoidCallback? onTap;
  final bool isUrdu;

  @override
  Widget build(BuildContext context) {
    final tempStr = summary.temperatureC != null
        ? '${summary.temperatureC!.toStringAsFixed(1)}°C'
        : '--°C';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.green.shade100),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
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
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.wb_sunny, size: 20, color: Colors.orange.shade800),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        isUrdu ? 'موسم کا حال' : 'Live Weather',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  StatusBadge(status: summary.status),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                '${summary.district} · $tempStr',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              if (summary.weatherDescription != null) ...[
                const SizedBox(height: 2),
                Text(
                  summary.weatherDescription!,
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                ),
              ],
              const SizedBox(height: 8),
              Row(
                children: <Widget>[
                  if (summary.humidityPercent != null) ...[
                    Icon(Icons.water_drop, size: 14, color: Colors.blue.shade600),
                    const SizedBox(width: 4),
                    Text(
                      '${isUrdu ? "نمی" : "Humidity"}: ${summary.humidityPercent!.toStringAsFixed(0)}%',
                      style: const TextStyle(fontSize: 12),
                    ),
                    const SizedBox(width: 16),
                  ],
                  if (summary.windSpeedKmh != null) ...[
                    Icon(Icons.air, size: 14, color: Colors.teal.shade600),
                    const SizedBox(width: 4),
                    Text(
                      '${isUrdu ? "ہوا" : "Wind"}: ${summary.windSpeedKmh!.toStringAsFixed(1)} km/h',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
