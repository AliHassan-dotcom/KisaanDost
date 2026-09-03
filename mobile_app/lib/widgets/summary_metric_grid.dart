import 'package:flutter/material.dart';

import '../models/farm_health_summary.dart';
import '../models/market_price.dart';
import '../models/satellite_summary.dart';
import '../models/weather_summary.dart';

/// 2x2 Metric Grid matching Screenshot 1:
/// - Farm Health Score (92% Excellent with Circular Ring Gauge)
/// - Weather Now (32.5°C Partly Cloudy with Location)
/// - Market Summary (Rs. 3,850 Wheat with Sparkline & +12%)
/// - Satellite Status (0.685 Good Vegetation with Radar Telemetry)
class SummaryMetricGrid extends StatelessWidget {
  const SummaryMetricGrid({
    super.key,
    required this.farmHealth,
    required this.weather,
    required this.market,
    required this.satellite,
    required this.isUrdu,
    required this.onFarmHealthTap,
    required this.onWeatherTap,
    required this.onMarketTap,
    required this.onSatelliteTap,
  });

  final FarmHealthSummary farmHealth;
  final WeatherSummary weather;
  final MarketPrice market;
  final SatelliteSummary satellite;
  final bool isUrdu;
  final VoidCallback onFarmHealthTap;
  final VoidCallback onWeatherTap;
  final VoidCallback onMarketTap;
  final VoidCallback onSatelliteTap;

  @override
  Widget build(BuildContext context) {

    return Column(
      children: <Widget>[
        Row(
          children: <Widget>[
            // 1. Farm Health Score Card
            Expanded(
              child: _buildMetricCard(
                onTap: onFarmHealthTap,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'فصل کی صحت کا اسکور' : 'Farm Health Score',
                      style: TextStyle(color: Colors.green.shade300, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: <Widget>[
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            const Text(
                              '92%',
                              style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                            ),
                            Text(
                              isUrdu ? 'بہترین' : 'Excellent',
                              style: const TextStyle(color: Color(0xFF00E676), fontSize: 11, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        // Ring gauge with leaf inside
                        SizedBox(
                          width: 44,
                          height: 44,
                          child: Stack(
                            alignment: Alignment.center,
                            children: <Widget>[
                              CircularProgressIndicator(
                                value: 0.92,
                                strokeWidth: 4,
                                backgroundColor: Colors.white.withAlpha(20),
                                valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF00E676)),
                              ),
                              const Icon(Icons.eco, color: Color(0xFF00E676), size: 18),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      isUrdu ? 'بہترین حالت میں ہے! ↗' : 'Keep it up! ↗',
                      style: const TextStyle(color: Colors.white60, fontSize: 10),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 12),

            // 2. Weather Now Card
            Expanded(
              child: _buildMetricCard(
                onTap: onWeatherTap,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'موجودہ موسم' : 'Weather Now',
                      style: TextStyle(color: Colors.green.shade300, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: <Widget>[
                        Text(
                          '${(weather.temperatureC ?? 32.5).toStringAsFixed(1)}°C',
                          style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                        ),
                        const Text('⛅', style: TextStyle(fontSize: 26)),
                      ],
                    ),
                    Text(
                      isUrdu ? 'جزوی ابر آلود' : 'Partly Cloudy',
                      style: const TextStyle(color: Colors.white70, fontSize: 11),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: <Widget>[
                        const Icon(Icons.location_on, size: 11, color: Color(0xFF00E676)),
                        const SizedBox(width: 3),
                        Flexible(
                          child: Text(
                            '${weather.district}, Punjab',
                            style: const TextStyle(color: Colors.white60, fontSize: 10),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: <Widget>[
            // 3. Market Summary Card
            Expanded(
              child: _buildMetricCard(
                onTap: onMarketTap,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'منڈی خلاصہ' : 'Market Summary',
                      style: TextStyle(color: Colors.green.shade300, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Rs. 3,850',
                      style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'گندم (40 کلو)' : 'Wheat (40kg)',
                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                        // Mini Sparkline Graph
                        CustomPaint(
                          size: const Size(36, 16),
                          painter: _MiniSparklinePainter(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      isUrdu ? '↗ 12% پچھلے ہفتے سے زیادہ' : '↗ 12% vs last week',
                      style: const TextStyle(color: Color(0xFF00E676), fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 12),

            // 4. Satellite Status Card
            Expanded(
              child: _buildMetricCard(
                onTap: onSatelliteTap,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'سیٹلائٹ اسٹیٹس' : 'Satellite Status',
                      style: TextStyle(color: Colors.green.shade300, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(
                          (satellite.ndvi ?? 0.685).toStringAsFixed(3),
                          style: const TextStyle(color: Color(0xFF00E5FF), fontSize: 22, fontWeight: FontWeight.bold),
                        ),
                        const Icon(Icons.radar, color: Color(0xFF00E5FF), size: 24),
                      ],
                    ),
                    Text(
                      isUrdu ? 'اچھی فصل (ہریالی)' : 'Good Vegetation',
                      style: const TextStyle(color: Colors.white70, fontSize: 11),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      isUrdu ? 'تازہ ترین: صبح 10:30' : 'Updated 10:30 AM',
                      style: const TextStyle(color: Colors.white60, fontSize: 10),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildMetricCard({required Widget child, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        height: 128,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF0F2E1E),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.green.withAlpha(50), width: 1),
          boxShadow: const <BoxShadow>[
            BoxShadow(
              color: Colors.black26,
              blurRadius: 8,
              offset: Offset(0, 3),
            ),
          ],
        ),
        child: child,
      ),
    );
  }
}

class _MiniSparklinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF00E676)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final path = Path();
    path.moveTo(0, size.height * 0.8);
    path.lineTo(size.width * 0.35, size.height * 0.6);
    path.lineTo(size.width * 0.7, size.height * 0.7);
    path.lineTo(size.width, size.height * 0.1);

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
