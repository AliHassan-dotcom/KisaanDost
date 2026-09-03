import 'package:flutter/material.dart';

import '../models/satellite_summary.dart';
import 'status_badge.dart';

class SatelliteCard extends StatelessWidget {
  const SatelliteCard({
    super.key,
    required this.summary,
    this.onTap,
    this.isUrdu = false,
  });

  final SatelliteSummary summary;
  final VoidCallback? onTap;
  final bool isUrdu;

  String _formatTrend(String trend) {
    if (isUrdu) {
      switch (trend) {
        case 'vegetation_attention':
          return 'فصل کی صحت پر توجہ درکار';
        case 'water_attention':
          return 'پانی کی کمی کا اندیشہ';
        case 'boundary_unavailable':
          return 'حدود دستیاب نہیں';
        case 'insufficient_satellite_data':
          return 'بادلوں کی وجہ سے جزوی ڈیٹا';
        case 'normal_observation':
        default:
          return 'فصل کی نشوونما نارمل';
      }
    }
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
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.teal.shade100),
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
                          color: Colors.teal.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.satellite_alt, size: 20, color: Colors.teal.shade900),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Satellite Monitoring$periodText',
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
                '${summary.crop} · ${summary.district}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 6),
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
                  Text(
                    'NDVI (Greenness): ${summary.ndvi!.toStringAsFixed(2)}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  ),
                if (summary.ndwi != null)
                  Text(
                    'NDWI (Moisture): ${summary.ndwi!.toStringAsFixed(2)}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  ),
                if (summary.cloudCoverPercent != null)
                  Text('Cloud cover: ${summary.cloudCoverPercent!.toStringAsFixed(0)}%'),
              ],
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: <Widget>[
                    Icon(Icons.eco, size: 16, color: Colors.green.shade800),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Observation: ${_formatTrend(summary.healthTrend)}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Colors.green.shade900,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
