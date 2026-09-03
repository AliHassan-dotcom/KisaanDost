import 'package:flutter/material.dart';

import '../models/satellite_summary.dart';
import 'status_badge.dart';

class SatelliteCard extends StatelessWidget {
  const SatelliteCard({super.key, required this.summary, this.onTap});

  final SatelliteSummary summary;
  final VoidCallback? onTap;

  String _formatTrend(String trend) {
    switch (trend) {
      case 'vegetation_attention':
        return 'Vegetation Attention';
      case 'water_attention':
        return 'Water Attention';
      case 'boundary_unavailable':
        return 'Boundary Unavailable';
      case 'insufficient_satellite_data':
        return 'Cloud Masked';
      case 'normal_observation':
      default:
        return 'Normal Observation';
    }
  }

  @override
  Widget build(BuildContext context) {
    final periodText = summary.periodStart != null ? ' (${summary.periodStart!.substring(0, 7)})' : '';

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
                    'Satellite Monitoring$periodText',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  StatusBadge(status: summary.status),
                ],
              ),
              const SizedBox(height: 8),
              Text('${summary.crop} · ${summary.district}'),
              const SizedBox(height: 4),
              if (summary.isBoundaryUnavailable)
                const Text(
                  'Boundary unavailable in provincial GIS dataset.',
                  style: TextStyle(color: Colors.grey, fontSize: 12),
                )
              else if (summary.isCloudMasked)
                const Text(
                  'Optical satellite cloud/fog masked for this month.',
                  style: TextStyle(color: Colors.grey, fontSize: 12),
                )
              else ...<Widget>[
                if (summary.ndvi != null)
                  Text('NDVI (Greenness): ${summary.ndvi!.toStringAsFixed(2)}'),
                if (summary.ndwi != null)
                  Text('NDWI (Moisture): ${summary.ndwi!.toStringAsFixed(2)}'),
                if (summary.cloudCoverPercent != null)
                  Text('Cloud cover: ${summary.cloudCoverPercent!.toStringAsFixed(0)}%'),
              ],
              const SizedBox(height: 4),
              Text(
                'Observation: ${_formatTrend(summary.healthTrend)}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
