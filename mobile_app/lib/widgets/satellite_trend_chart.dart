import 'package:flutter/material.dart';

import '../models/satellite_record.dart';

class SatelliteTrendChart extends StatelessWidget {
  const SatelliteTrendChart({
    super.key,
    required this.records,
    this.height = 200,
  });

  final List<SatelliteRecord> records;
  final double height;

  @override
  Widget build(BuildContext context) {
    if (records.isEmpty) {
      return const SizedBox(
        height: 120,
        child: Center(
          child: Text('No historical satellite observations available.'),
        ),
      );
    }

    final hasValidData = records.any((r) => r.hasValidMetrics);
    if (!hasValidData) {
      return Container(
        height: 120,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey.shade300),
        ),
        child: const Center(
          child: Text(
            'Zonal time-series unavailable for unmapped boundary polygon.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            _legendItem('NDVI (Canopy Greenness)', Colors.green.shade700),
            const SizedBox(width: 16),
            _legendItem('NDWI (Canopy Moisture)', Colors.blue.shade700),
          ],
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: height,
          child: CustomPaint(
            painter: _SatelliteChartPainter(records: records),
            child: Container(),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const <Widget>[
            Text('2022', style: TextStyle(fontSize: 10, color: Colors.grey)),
            Text('2023', style: TextStyle(fontSize: 10, color: Colors.grey)),
            Text('2024', style: TextStyle(fontSize: 10, color: Colors.grey)),
            Text('2025', style: TextStyle(fontSize: 10, color: Colors.grey)),
          ],
        ),
      ],
    );
  }

  Widget _legendItem(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }
}

class _SatelliteChartPainter extends CustomPainter {
  const _SatelliteChartPainter({required this.records});

  final List<SatelliteRecord> records;

  @override
  void paint(Canvas canvas, Size size) {
    if (records.isEmpty) return;

    final gridPaint = Paint()
      ..color = Colors.grey.shade300
      ..strokeWidth = 0.8;

    final ndviPaint = Paint()
      ..color = Colors.green.shade700
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final ndwiPaint = Paint()
      ..color = Colors.blue.shade700
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final dotPaint = Paint()..style = PaintingStyle.fill;

    // Draw horizontal grid lines for [-0.5, 0.0, 0.5, 1.0]
    // Normalized mapping: value range from -0.8 to +1.0
    const minY = -0.8;
    const maxY = 1.0;
    const rangeY = maxY - minY;

    double getY(double val) {
      final clamped = val.clamp(minY, maxY);
      final norm = (clamped - minY) / rangeY;
      return size.height - (norm * size.height);
    }

    // Grid zero line
    final zeroY = getY(0.0);
    canvas.drawLine(Offset(0, zeroY), Offset(size.width, zeroY), gridPaint);
    canvas.drawLine(Offset(0, getY(0.5)), Offset(size.width, getY(0.5)), gridPaint);
    canvas.drawLine(Offset(0, getY(-0.5)), Offset(size.width, getY(-0.5)), gridPaint);

    final n = records.length;
    if (n < 2) return;
    final stepX = size.width / (n - 1);

    // Draw NDVI line
    Path? ndviPath;
    for (int i = 0; i < n; i++) {
      final r = records[i];
      if (r.ndviMean != null) {
        final x = i * stepX;
        final y = getY(r.ndviMean!);
        if (ndviPath == null) {
          ndviPath = Path()..moveTo(x, y);
        } else {
          ndviPath.lineTo(x, y);
        }
      } else {
        if (ndviPath != null) {
          canvas.drawPath(ndviPath, ndviPaint);
          ndviPath = null;
        }
      }
    }
    if (ndviPath != null) {
      canvas.drawPath(ndviPath, ndviPaint);
    }

    // Draw NDWI line
    Path? ndwiPath;
    for (int i = 0; i < n; i++) {
      final r = records[i];
      if (r.ndwiMean != null) {
        final x = i * stepX;
        final y = getY(r.ndwiMean!);
        if (ndwiPath == null) {
          ndwiPath = Path()..moveTo(x, y);
        } else {
          ndwiPath.lineTo(x, y);
        }
      } else {
        if (ndwiPath != null) {
          canvas.drawPath(ndwiPath, ndwiPaint);
          ndwiPath = null;
        }
      }
    }
    if (ndwiPath != null) {
      canvas.drawPath(ndwiPath, ndwiPaint);
    }

    // Draw dots on data points
    for (int i = 0; i < n; i++) {
      final r = records[i];
      final x = i * stepX;
      if (r.ndviMean != null) {
        dotPaint.color = Colors.green.shade800;
        canvas.drawCircle(Offset(x, getY(r.ndviMean!)), 2.5, dotPaint);
      }
      if (r.ndwiMean != null) {
        dotPaint.color = Colors.blue.shade800;
        canvas.drawCircle(Offset(x, getY(r.ndwiMean!)), 2.5, dotPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SatelliteChartPainter oldDelegate) {
    return oldDelegate.records != records;
  }
}
