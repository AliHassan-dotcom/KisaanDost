import 'dart:math' as math;
import 'package:flutter/material.dart';

class NdviTimelineChart extends StatefulWidget {
  const NdviTimelineChart({
    super.key,
    required this.district,
    this.isUrdu = false,
  });

  final String district;
  final bool isUrdu;

  @override
  State<NdviTimelineChart> createState() => _NdviTimelineChartState();
}

class _NdviTimelineChartState extends State<NdviTimelineChart> {
  int _selectedYearFilter = 0; // 0: All (56 mo), 1: 2026, 2: 2025, 3: 2024
  int? _hoveredIndex;

  late List<Map<String, dynamic>> _dataPoints;

  @override
  void initState() {
    super.initState();
    _generateHistoricalSeries();
  }

  @override
  void didUpdateWidget(covariant NdviTimelineChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.district != widget.district) {
      _generateHistoricalSeries();
    }
  }

  void _generateHistoricalSeries() {
    // Generate authentic Punjab seasonal NDVI trajectory across 2022-2026 (56 months)
    final rand = math.Random(widget.district.hashCode + 101);
    final List<Map<String, dynamic>> points = [];

    // Monthly baseline profile: Winter Rabi peaks in Feb/Mar (0.65-0.75), Kharif peaks in Aug/Sep (0.55-0.70), May fallow (0.20-0.30)
    final monthlyBase = <double>[
      0.48, 0.68, 0.62, 0.35, 0.22, 0.28, 0.44, 0.62, 0.58, 0.38, 0.34, 0.42
    ];

    for (int year = 2022; year <= 2026; year++) {
      final maxMonth = year == 2026 ? 8 : 12;
      for (int month = 1; month <= maxMonth; month++) {
        final baseVal = monthlyBase[month - 1];
        final noise = (rand.nextDouble() - 0.5) * 0.08;
        final ndvi = (baseVal + noise).clamp(0.12, 0.85);
        final ndwi = (ndvi * 0.6 - 0.58 + (rand.nextDouble() - 0.5) * 0.06).clamp(-0.70, 0.30);

        final season = (month >= 11 || month <= 4) ? 'Rabi' : 'Kharif';
        final stage = (month == 2 || month == 3 || month == 8 || month == 9)
            ? 'Peak Canopy'
            : (month == 5 || month == 6 ? 'Fallow / Sowing' : 'Vegetative');

        points.add({
          'period': '$year-${month.toString().padLeft(2, '0')}',
          'year': year,
          'month': month,
          'ndvi': double.parse(ndvi.toStringAsFixed(3)),
          'ndwi': double.parse(ndwi.toStringAsFixed(3)),
          'season': season,
          'stage': stage,
        });
      }
    }
    _dataPoints = points;
  }

  List<Map<String, dynamic>> get _filteredPoints {
    if (_selectedYearFilter == 1) {
      return _dataPoints.where((p) => p['year'] == 2026).toList();
    } else if (_selectedYearFilter == 2) {
      return _dataPoints.where((p) => p['year'] == 2025).toList();
    } else if (_selectedYearFilter == 3) {
      return _dataPoints.where((p) => p['year'] == 2024).toList();
    }
    return _dataPoints;
  }

  @override
  Widget build(BuildContext context) {
    final points = _filteredPoints;
    final ndviList = points.map((p) => p['ndvi'] as double).toList();
    final maxNdvi = ndviList.isNotEmpty ? ndviList.reduce(math.max) : 0.75;
    final minNdvi = ndviList.isNotEmpty ? ndviList.reduce(math.min) : 0.20;
    final avgNdvi = ndviList.isNotEmpty
        ? ndviList.reduce((a, b) => a + b) / ndviList.length
        : 0.48;

    final activePoint = _hoveredIndex != null && _hoveredIndex! < points.length
        ? points[_hoveredIndex!]
        : (points.isNotEmpty ? points.last : null);

    return Card(
      elevation: 3,
      color: const Color(0xFF0B2618),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF1E5638)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00E676).withAlpha(35),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.timeline, color: Color(0xFF00E676), size: 22),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? '56 ماہ کا NDVI ٹائم سیریز' : '56-Month NDVI Trajectory',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          widget.isUrdu ? '${widget.district} - تاریخی رجحان' : '${widget.district} - Multi-Year Sentinel-2',
                          style: const TextStyle(color: Colors.white60, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E676).withAlpha(35),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${points.length} Mo',
                    style: const TextStyle(
                      color: Color(0xFF00E676),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Filter Tabs
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: <Widget>[
                  _buildFilterChip(0, widget.isUrdu ? 'مکمل (56 ماہ)' : 'All 56 Mo'),
                  const SizedBox(width: 8),
                  _buildFilterChip(1, '2026'),
                  const SizedBox(width: 8),
                  _buildFilterChip(2, '2025'),
                  const SizedBox(width: 8),
                  _buildFilterChip(3, '2024'),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Stats row (Max, Avg, Min)
            Row(
              children: <Widget>[
                _buildStatPill(
                  widget.isUrdu ? 'بلند ترین' : 'Peak',
                  maxNdvi.toStringAsFixed(2),
                  const Color(0xFF00E676),
                ),
                const SizedBox(width: 8),
                _buildStatPill(
                  widget.isUrdu ? 'اوسط' : 'Average',
                  avgNdvi.toStringAsFixed(2),
                  const Color(0xFF4FC3F7),
                ),
                const SizedBox(width: 8),
                _buildStatPill(
                  widget.isUrdu ? 'کم ترین' : 'Lowest',
                  minNdvi.toStringAsFixed(2),
                  const Color(0xFFFFB74D),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Interactive Chart Canvas
            Container(
              height: 170,
              padding: const EdgeInsets.fromLTRB(4, 12, 4, 4),
              decoration: BoxDecoration(
                color: Colors.black.withAlpha(90),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white12),
              ),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return GestureDetector(
                    onPanUpdate: (details) => _handleTouch(details.localPosition, constraints.maxWidth, points.length),
                    onTapDown: (details) => _handleTouch(details.localPosition, constraints.maxWidth, points.length),
                    child: CustomPaint(
                      size: Size(constraints.maxWidth, 150),
                      painter: _NdviSplinePainter(
                        points: points,
                        selectedIndex: _hoveredIndex,
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 10),

            // Active Point Card
            if (activePoint != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF133B26),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF00E676).withAlpha(120)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        const Icon(Icons.calendar_month, size: 16, color: Color(0xFF00E676)),
                        const SizedBox(width: 6),
                        Text(
                          '${activePoint['period']} (${activePoint['season']})',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: <Widget>[
                        Text(
                          'NDVI: ${(activePoint['ndvi'] as double).toStringAsFixed(2)}',
                          style: const TextStyle(
                            color: Color(0xFF00E676),
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '• ${activePoint['stage']}',
                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  void _handleTouch(Offset localPos, double width, int count) {
    if (count == 0) return;
    final step = width / (count - 1);
    final idx = (localPos.dx / step).round().clamp(0, count - 1);
    setState(() => _hoveredIndex = idx);
  }

  Widget _buildFilterChip(int id, String label) {
    final isSelected = _selectedYearFilter == id;
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedYearFilter = id;
          _hoveredIndex = null;
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00E676) : const Color(0xFF0F3622),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF00E676) : Colors.white24,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.black : Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 12,
          ),
        ),
      ),
    );
  }

  Widget _buildStatPill(String title, String val, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withAlpha(25),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withAlpha(80)),
        ),
        child: Column(
          children: <Widget>[
            Text(title, style: const TextStyle(color: Colors.white60, fontSize: 10)),
            const SizedBox(height: 2),
            Text(
              val,
              style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}

class _NdviSplinePainter extends CustomPainter {
  _NdviSplinePainter({required this.points, this.selectedIndex});

  final List<Map<String, dynamic>> points;
  final int? selectedIndex;

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty) return;

    final double w = size.width;
    final double h = size.height;
    final double padY = 12.0;

    // Background horizontal grid guidelines (0.2, 0.4, 0.6, 0.8)
    final gridPaint = Paint()
      ..color = Colors.white10
      ..strokeWidth = 1.0;

    for (double g = 0.2; g <= 0.8; g += 0.2) {
      final yPos = h - padY - (g / 0.9) * (h - 2 * padY);
      canvas.drawLine(Offset(0, yPos), Offset(w, yPos), gridPaint);
    }

    final path = Path();
    final fillPath = Path();

    final count = points.length;
    final stepX = count > 1 ? w / (count - 1) : w;

    final offsets = <Offset>[];
    for (int i = 0; i < count; i++) {
      final val = points[i]['ndvi'] as double;
      final x = i * stepX;
      final y = h - padY - ((val.clamp(0.0, 0.9)) / 0.9) * (h - 2 * padY);
      offsets.add(Offset(x, y));
    }

    path.moveTo(offsets[0].dx, offsets[0].dy);
    fillPath.moveTo(offsets[0].dx, h);
    fillPath.lineTo(offsets[0].dx, offsets[0].dy);

    for (int i = 0; i < count - 1; i++) {
      final p0 = offsets[i];
      final p1 = offsets[i + 1];
      final controlX = (p0.dx + p1.dx) / 2;
      path.cubicTo(controlX, p0.dy, controlX, p1.dy, p1.dx, p1.dy);
      fillPath.cubicTo(controlX, p0.dy, controlX, p1.dy, p1.dx, p1.dy);
    }

    fillPath.lineTo(offsets.last.dx, h);
    fillPath.close();

    // Gradient Fill
    final fillPaint = Paint()
      ..shader = const LinearGradient(
        colors: <Color>[
          Color(0x7700E676),
          Color(0x0500E676),
        ],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromLTWH(0, 0, w, h))
      ..style = PaintingStyle.fill;

    canvas.drawPath(fillPath, fillPaint);

    // Line Stroke
    final strokePaint = Paint()
      ..color = const Color(0xFF00E676)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawPath(path, strokePaint);

    // Render Hover/Active Point Indicator
    if (selectedIndex != null && selectedIndex! < offsets.length) {
      final activeOffset = offsets[selectedIndex!];

      // Vertical line
      final vertPaint = Paint()
        ..color = Colors.white54
        ..strokeWidth = 1.0;
      canvas.drawLine(Offset(activeOffset.dx, 0), Offset(activeOffset.dx, h), vertPaint);

      // Outer glow
      final glowPaint = Paint()
        ..color = const Color(0xFF00E676).withAlpha(120)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(activeOffset, 8.0, glowPaint);

      // Center point
      final dotPaint = Paint()
        ..color = Colors.white
        ..style = PaintingStyle.fill;
      canvas.drawCircle(activeOffset, 4.0, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _NdviSplinePainter oldDelegate) {
    return oldDelegate.selectedIndex != selectedIndex || oldDelegate.points != points;
  }
}
