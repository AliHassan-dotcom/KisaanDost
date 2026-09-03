import 'package:flutter/material.dart';

import '../models/farm_health_summary.dart';

class FarmHealthCard extends StatelessWidget {
  const FarmHealthCard({
    super.key,
    required this.summary,
    this.onTap,
    this.isUrdu = false,
  });

  final FarmHealthSummary summary;
  final VoidCallback? onTap;
  final bool isUrdu;

  @override
  Widget build(BuildContext context) {
    final hasScan = summary.status != null && summary.status != 'no_recent_scan';

    return Card(
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
                          color: Colors.green.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.psychology, size: 20, color: Colors.green.shade900),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        isUrdu ? 'فصل کی صحت (AI اسکین)' : 'Crop Health & Diagnosis',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey.shade400),
                ],
              ),
              const SizedBox(height: 12),
              if (hasScan) ...[
                Row(
                  children: <Widget>[
                    Icon(
                      summary.uncertain ? Icons.warning_amber : Icons.check_circle,
                      color: summary.uncertain ? Colors.orange : Colors.green.shade700,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        summary.status!,
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
                if (summary.confidence != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    '${isUrdu ? "درستگی" : "AI Confidence"}: ${(summary.confidence! * 100).toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                  ),
                ],
              ] else ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Row(
                    children: <Widget>[
                      Icon(Icons.camera_alt, color: Colors.green.shade800, size: 24),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              isUrdu ? 'پتے کی تصویر اسکین کریں' : 'Scan Leaf Photo for Disease',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                                color: Colors.green.shade900,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              isUrdu
                                  ? '38 بیماریوں کی فوری AI تشخیص اور علاج'
                                  : 'Instant diagnosis & chemical treatment',
                              style: TextStyle(fontSize: 11, color: Colors.green.shade800),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
