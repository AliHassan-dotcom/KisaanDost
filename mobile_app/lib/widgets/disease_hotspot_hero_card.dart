import 'package:flutter/material.dart';

import '../models/risk_assessment.dart';

/// Disease Hotspot (Pakistan) & Crop-Stress Risk Model Card matching Screenshot 3:
/// - Disease outbreak hotspot nodes across Punjab districts with glowing halos
/// - Circular Risk Level Gauge (78% High in Amber/Orange)
class DiseaseHotspotHeroCard extends StatelessWidget {
  const DiseaseHotspotHeroCard({
    super.key,
    required this.riskAssessment,
    required this.isUrdu,
    required this.onTap,
  });

  final RiskAssessment? riskAssessment;
  final bool isUrdu;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final risk = riskAssessment ?? RiskAssessment.mockDefault();
    final riskPercent = risk.riskPercent; // 78%
    final riskLevel = risk.riskLevel; // High

    Color gaugeColor;
    if (riskPercent >= 70) {
      gaugeColor = const Color(0xFFFFA726); // Amber / Orange
    } else if (riskPercent >= 40) {
      gaugeColor = Colors.yellow.shade700;
    } else {
      gaugeColor = const Color(0xFF00E676);
    }

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: Container(
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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'بیماری کے ہاٹ اسپاٹس (پاکستان ماڈل)' : 'Disease Hotspot (Pakistan)',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.red.withAlpha(30),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.red.withAlpha(60)),
                  ),
                  child: const Text(
                    'RISK MODEL',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFFFF5252),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Main Row: Radar Hotspot Canvas (Left) + Circular Risk Level Gauge (Right)
            Row(
              children: <Widget>[
                // Radar / Map Nodes Canvas
                Expanded(
                  child: SizedBox(
                    height: 130,
                    child: CustomPaint(
                      size: const Size(double.infinity, 130),
                      painter: _HotspotMapPainter(),
                    ),
                  ),
                ),

                const SizedBox(width: 14),

                // Circular Risk Level Gauge
                SizedBox(
                  width: 110,
                  height: 110,
                  child: Stack(
                    alignment: Alignment.center,
                    children: <Widget>[
                      // Circular Arc Progress
                      SizedBox(
                        width: 100,
                        height: 100,
                        child: CircularProgressIndicator(
                          value: (riskPercent / 100.0).clamp(0.0, 1.0),
                          strokeWidth: 8,
                          backgroundColor: Colors.white12,
                          valueColor: AlwaysStoppedAnimation<Color>(gaugeColor),
                        ),
                      ),

                      // Center Labels
                      Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: <Widget>[
                          Text(
                            isUrdu ? 'رسک لیول' : 'Risk Level',
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 10,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            '$riskPercent%',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            isUrdu ? (riskLevel == 'High' ? 'زیادہ' : riskLevel) : riskLevel,
                            style: TextStyle(
                              color: gaugeColor,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _HotspotMapPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // Background subtle radar concentric rings
    final center = Offset(w * 0.45, h * 0.5);
    final ringPaint = Paint()
      ..color = Colors.white.withAlpha(12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    canvas.drawCircle(center, 25, ringPaint);
    canvas.drawCircle(center, 50, ringPaint);

    // Outbreak hotspot coordinates matching Punjab districts (Multan, Bahawalpur, Faisalabad)
    final hotspotOffsets = <Offset>[
      Offset(w * 0.25, h * 0.55), // Multan
      Offset(w * 0.38, h * 0.65), // Bahawalpur
      Offset(w * 0.32, h * 0.78), // Rahim Yar Khan
    ];

    final dotPaint = Paint()
      ..color = const Color(0xFFFF4081)
      ..style = PaintingStyle.fill;

    for (final pos in hotspotOffsets) {
      // Outer halo ripple
      final ripplePaint = Paint()
        ..color = const Color(0xFFFF4081).withAlpha(60)
        ..style = PaintingStyle.fill;

      canvas.drawCircle(pos, 10.0, ripplePaint);
      // Inner solid dot
      canvas.drawCircle(pos, 5.0, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
