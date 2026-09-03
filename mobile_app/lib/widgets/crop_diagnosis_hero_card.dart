import 'package:flutter/material.dart';

import '../models/farm_health_summary.dart';

/// Crop Diagnosis Card matching Screenshot 2:
/// - Thumbnail of crop/disease (Wheat / گندم)
/// - Leaf Rust Detected (Amber warning text)
/// - Severity: Medium (65%)
/// - Confidence: 92% (with animated progress bar)
/// - View Details button
class CropDiagnosisHeroCard extends StatelessWidget {
  const CropDiagnosisHeroCard({
    super.key,
    required this.summary,
    required this.isUrdu,
    required this.onViewDetails,
  });

  final FarmHealthSummary summary;
  final bool isUrdu;
  final VoidCallback onViewDetails;

  @override
  Widget build(BuildContext context) {
    final confidencePercent = ((summary.confidence ?? 0.92) * 100).toInt();

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F2E1E),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.green.withAlpha(50), width: 1),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Colors.black26,
            blurRadius: 8,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            isUrdu ? 'فصل کی تشخیص (AI ماڈل)' : 'Crop Diagnosis',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 14),

          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              // Crop Thumbnail
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(14),
                  color: Colors.amber.shade900.withAlpha(80),
                  border: Border.all(color: Colors.amber.shade700, width: 1.5),
                  image: const DecorationImage(
                    image: AssetImage('assets/images/wheat_sample.jpg'),
                    fit: BoxFit.cover,
                    onError: _ignoreImageError,
                  ),
                ),
                child: Center(
                  child: Icon(Icons.grain, size: 36, color: Colors.amber.shade200),
                ),
              ),
              const SizedBox(width: 14),

              // Diagnostic Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'Wheat (گندم)' : 'Wheat (گندم)',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 3),
                    const Text(
                      'Leaf Rust Detected',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFFFA726), // Amber warning
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      isUrdu ? 'شدت: درمیانی (65%)' : 'Severity: Medium (65%)',
                      style: const TextStyle(
                        fontSize: 11,
                        color: Colors.white70,
                      ),
                    ),
                    const SizedBox(height: 6),

                    // Confidence Bar
                    Row(
                      children: <Widget>[
                        Text(
                          isUrdu ? 'اعتماد: $confidencePercent%' : 'Confidence: $confidencePercent%',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: const LinearProgressIndicator(
                        value: 0.92,
                        minHeight: 5,
                        backgroundColor: Colors.white24,
                        valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFFFA726)),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // View Details Button
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: onViewDetails,
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.white.withAlpha(40)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
                padding: const EdgeInsets.symmetric(vertical: 12),
                backgroundColor: Colors.white.withAlpha(15),
              ),
              child: Text(
                isUrdu ? 'تفصیلات اور علاج دیکھیں' : 'View Details',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  static void _ignoreImageError(Object exception, StackTrace? stackTrace) {}
}
