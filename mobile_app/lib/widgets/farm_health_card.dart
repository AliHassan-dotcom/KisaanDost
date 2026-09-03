import 'package:flutter/material.dart';

import '../models/farm_health_summary.dart';

class FarmHealthCard extends StatelessWidget {
  const FarmHealthCard({super.key, required this.summary, this.onTap});

  final FarmHealthSummary summary;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Farm Health',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                summary.status ?? 'No recent scan',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              if (summary.confidence != null)
                Text(
                  'Confidence: ${(summary.confidence! * 100).toStringAsFixed(1)}%',
                ),
              if (summary.uncertain)
                const Text(
                  'Result is uncertain',
                  style: TextStyle(color: Colors.orange),
                ),
              if (summary.lastScannedAt != null)
                Text('Last scan: ${summary.lastScannedAt}'),
            ],
          ),
        ),
      ),
    );
  }
}
