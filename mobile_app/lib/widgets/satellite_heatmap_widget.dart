import 'dart:math' as math;
import 'package:flutter/material.dart';

class SatelliteHeatmapWidget extends StatefulWidget {
  const SatelliteHeatmapWidget({
    super.key,
    required this.district,
    this.isUrdu = false,
    this.meanNdvi = 0.54,
  });

  final String district;
  final bool isUrdu;
  final double meanNdvi;

  @override
  State<SatelliteHeatmapWidget> createState() => _SatelliteHeatmapWidgetState();
}

class _SatelliteHeatmapWidgetState extends State<SatelliteHeatmapWidget> {
  int _selectedMode = 0; // 0: NDVI, 1: NDWI, 2: Thermal Vigor
  int? _tappedRow;
  int? _tappedCol;
  double? _tappedVal;

  late List<List<double>> _grid;
  final int _gridSize = 12;

  @override
  void initState() {
    super.initState();
    _generateGrid();
  }

  @override
  void didUpdateWidget(covariant SatelliteHeatmapWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.district != widget.district || oldWidget.meanNdvi != widget.meanNdvi) {
      _generateGrid();
    }
  }

  void _generateGrid() {
    final rand = math.Random(widget.district.hashCode);
    final base = widget.meanNdvi;
    _grid = List.generate(_gridSize, (r) {
      return List.generate(_gridSize, (c) {
        final distFromCenter = math.sqrt(math.pow(r - 5.5, 2) + math.pow(c - 5.5, 2));
        final kernel = math.exp(-distFromCenter / 4.0);
        final noise = (rand.nextDouble() - 0.5) * 0.12;
        final val = (base * (0.85 + 0.35 * kernel) + noise).clamp(0.08, 0.88);
        return double.parse(val.toStringAsFixed(3));
      });
    });
  }

  Color _getColorForValue(double val) {
    if (_selectedMode == 1) {
      // NDWI Moisture: Amber/Dry -> Cyan/Moist -> Deep Blue
      if (val < 0.25) return const Color(0xFFE65100);
      if (val < 0.45) return const Color(0xFF00ACC1);
      if (val < 0.65) return const Color(0xFF0288D1);
      return const Color(0xFF0D47A1);
    }
    // NDVI: Red -> Orange -> Yellow -> Green -> Emerald
    if (val < 0.20) return const Color(0xFFD32F2F);
    if (val < 0.38) return const Color(0xFFF57C00);
    if (val < 0.55) return const Color(0xFFFBC02D);
    if (val < 0.72) return const Color(0xFF43A047);
    return const Color(0xFF1B5E20);
  }

  String _getClassification(double val) {
    if (widget.isUrdu) {
      if (val < 0.20) return 'خشک / شدید تناؤ (Stressed)';
      if (val < 0.38) return 'کم نباتات (Sparse)';
      if (val < 0.55) return 'معتدل نشوونما (Moderate)';
      if (val < 0.72) return 'صحت مند فصل (Healthy)';
      return 'انتہائی سرسبز (Vibrant)';
    }
    if (val < 0.20) return 'Stressed / Bare Soil';
    if (val < 0.38) return 'Sparse Vegetation';
    if (val < 0.55) return 'Moderate Canopy';
    if (val < 0.72) return 'Healthy Dense Crop';
    return 'Vibrant Lush Canopy';
  }

  @override
  Widget build(BuildContext context) {
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
                      child: const Icon(Icons.grid_view_rounded, color: Color(0xFF00E676), size: 22),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? 'سیٹلائٹ ہیٹ میپ ویژولائزیشن' : 'Satellite NDVI Heatmap',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          widget.isUrdu ? '${widget.district} - 10m ریزولوشن' : '${widget.district} - 10m Sentinel-2 Resolution',
                          style: const TextStyle(color: Colors.white60, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E676).withAlpha(40),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF00E676)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      const Icon(Icons.satellite_alt, size: 14, color: Color(0xFF00E676)),
                      const SizedBox(width: 4),
                      Text(
                        'NDVI ${(widget.meanNdvi).toStringAsFixed(2)}',
                        style: const TextStyle(
                          color: Color(0xFF00E676),
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Mode Selector Pills
            Row(
              children: <Widget>[
                _buildModePill(0, widget.isUrdu ? 'سبزہ (NDVI)' : 'NDVI Green', Icons.grass),
                const SizedBox(width: 8),
                _buildModePill(1, widget.isUrdu ? 'نمی (NDWI)' : 'Moisture', Icons.water_drop),
                const SizedBox(width: 8),
                _buildModePill(2, widget.isUrdu ? 'تپش/حرارت' : 'Thermal', Icons.thermostat),
              ],
            ),
            const SizedBox(height: 14),

            // Heatmap Grid Canvas
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black.withAlpha(80),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white12),
              ),
              child: AspectRatio(
                aspectRatio: 1.0,
                child: GridView.builder(
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: _gridSize,
                    mainAxisSpacing: 2,
                    crossAxisSpacing: 2,
                  ),
                  itemCount: _gridSize * _gridSize,
                  itemBuilder: (context, index) {
                    final r = index ~/ _gridSize;
                    final c = index % _gridSize;
                    final val = _grid[r][c];
                    final isSelected = _tappedRow == r && _tappedCol == c;

                    return GestureDetector(
                      onTap: () {
                        setState(() {
                          _tappedRow = r;
                          _tappedCol = c;
                          _tappedVal = val;
                        });
                      },
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        decoration: BoxDecoration(
                          color: _getColorForValue(val),
                          borderRadius: BorderRadius.circular(3),
                          border: isSelected
                              ? Border.all(color: Colors.white, width: 2)
                              : null,
                          boxShadow: isSelected
                              ? <BoxShadow>[
                                  const BoxShadow(
                                    color: Colors.white70,
                                    blurRadius: 6,
                                    spreadRadius: 1,
                                  )
                                ]
                              : null,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 10),

            // Tapped Pixel Detail Card
            if (_tappedVal != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF133B26),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF00E676).withAlpha(100)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Container(
                          width: 14,
                          height: 14,
                          decoration: BoxDecoration(
                            color: _getColorForValue(_tappedVal!),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          widget.isUrdu
                              ? 'خانہ ($_tappedRow, $_tappedCol): ${_tappedVal!.toStringAsFixed(3)}'
                              : 'Cell ($_tappedRow, $_tappedCol): ${_tappedVal!.toStringAsFixed(3)}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    Text(
                      _getClassification(_tappedVal!),
                      style: const TextStyle(
                        color: Color(0xFF00E676),
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              )
            else
              Text(
                widget.isUrdu
                  ? 'کسی بھی خانے پر کلک کر کے اس کی مخصوص NDVI ویلیو دیکھیں'
                  : 'Tap any pixel above to inspect localized NDVI & vigor',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white54, fontSize: 11),
              ),
            const SizedBox(height: 12),

            // Legend Gradient Bar
            Row(
              children: <Widget>[
                Text(
                  widget.isUrdu ? 'کم' : '0.0 Low',
                  style: const TextStyle(color: Colors.white54, fontSize: 11),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Container(
                    height: 10,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(5),
                      gradient: const LinearGradient(
                        colors: <Color>[
                          Color(0xFFD32F2F), // Red
                          Color(0xFFF57C00), // Orange
                          Color(0xFFFBC02D), // Yellow
                          Color(0xFF43A047), // Light Green
                          Color(0xFF1B5E20), // Dark Emerald
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  widget.isUrdu ? 'اعلیٰ' : '0.8+ Lush',
                  style: const TextStyle(color: Colors.white54, fontSize: 11),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModePill(int id, String label, IconData icon) {
    final isSelected = _selectedMode == id;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() {
            _selectedMode = id;
            _tappedVal = null;
          });
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 6),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF00E676) : const Color(0xFF0F3622),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected ? const Color(0xFF00E676) : Colors.white24,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(icon, size: 14, color: isSelected ? Colors.black : Colors.white70),
              const SizedBox(width: 4),
              Text(
                label,
                style: TextStyle(
                  color: isSelected ? Colors.black : Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

