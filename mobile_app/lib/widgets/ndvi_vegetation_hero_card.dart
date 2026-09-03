import 'package:flutter/material.dart';

import '../models/satellite_summary.dart';

/// NDVI (Vegetation Health) Card matching Screenshot 3:
/// - 3D field canopy visual with glowing green polygon overlay
/// - Floating Legend: "🟢 High  🟠 Medium  🔴 Low"
class NdviVegetationHeroCard extends StatelessWidget {
  const NdviVegetationHeroCard({
    super.key,
    required this.satellite,
    required this.isUrdu,
    required this.onTap,
  });

  final SatelliteSummary satellite;
  final bool isUrdu;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
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
            Text(
              isUrdu ? 'سیٹلائٹ ہریالی (NDVI ویجیٹیشن)' : 'NDVI (Vegetation Health)',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 14),

            // 3D Perspective Field Canopy Visual Container
            Container(
              height: 150,
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                gradient: LinearGradient(
                  colors: <Color>[
                    Colors.cyan.shade900,
                    Colors.teal.shade900,
                    Colors.amber.shade900,
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
                boxShadow: const <BoxShadow>[
                  BoxShadow(
                    color: Colors.black45,
                    blurRadius: 8,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Stack(
                alignment: Alignment.center,
                children: <Widget>[
                  // 3D Polygon Perspective Canopy Shader/Painter
                  CustomPaint(
                    size: const Size(double.infinity, 150),
                    painter: _FieldCanopyPainter(),
                  ),

                  // Sun flare glow
                  Positioned(
                    bottom: 40,
                    child: Container(
                      width: 30,
                      height: 30,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF00E5FF).withAlpha(180),
                        boxShadow: const <BoxShadow>[
                          BoxShadow(
                            color: Color(0xFF00E676),
                            blurRadius: 30,
                            spreadRadius: 10,
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Bottom Legend Pill
                  Positioned(
                    bottom: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.black.withAlpha(180),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white24),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: <Widget>[
                          _LegendDot(color: Color(0xFF00E676), label: 'High'),
                          SizedBox(width: 10),
                          _LegendDot(color: Color(0xFFFFA726), label: 'Medium'),
                          SizedBox(width: 10),
                          _LegendDot(color: Color(0xFFFF5252), label: 'Low'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: 7,
          height: 7,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }
}

class _FieldCanopyPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // Draw glowing green agricultural trapezoid polygon in 3D perspective
    final polygonPath = Path()
      ..moveTo(w * 0.28, h * 0.18)
      ..lineTo(w * 0.88, h * 0.18)
      ..lineTo(w * 0.95, h * 0.72)
      ..lineTo(w * 0.12, h * 0.72)
      ..close();

    final fillPaint = Paint()
      ..shader = const LinearGradient(
        colors: <Color>[
          Color(0xEE00E676),
          Color(0xCC00C853),
          Color(0x9969F0AE),
        ],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromLTWH(0, 0, w, h));

    canvas.drawPath(polygonPath, fillPaint);

    // Subtle grid scan lines across polygon
    final gridPaint = Paint()
      ..color = Colors.white.withAlpha(40)
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;

    canvas.drawLine(Offset(w * 0.45, h * 0.18), Offset(w * 0.38, h * 0.72), gridPaint);
    canvas.drawLine(Offset(w * 0.65, h * 0.18), Offset(w * 0.65, h * 0.72), gridPaint);
    canvas.drawLine(Offset(w * 0.20, h * 0.45), Offset(w * 0.91, h * 0.45), gridPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
