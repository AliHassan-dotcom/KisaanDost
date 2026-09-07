import 'dart:math' as math;
import 'package:flutter/material.dart';

class Field3DViewer extends StatefulWidget {
  const Field3DViewer({
    super.key,
    required this.district,
    this.isUrdu = false,
    this.meanNdvi = 0.54,
  });

  final String district;
  final bool isUrdu;
  final double meanNdvi;

  @override
  State<Field3DViewer> createState() => _Field3DViewerState();
}

class _Field3DViewerState extends State<Field3DViewer>
    with SingleTickerProviderStateMixin {
  double _azimuthAngle = 45.0; // Rotation angle in degrees
  double _elevationAngle = 35.0; // Tilt angle in degrees
  bool _isAutoRotating = true;
  int _activeLayer = 0; // 0: 3D Canopy, 1: Moisture Topo, 2: Risk Pins

  late AnimationController _rotationController;
  late List<List<double>> _heightMesh;
  final int _gridSize = 12;

  @override
  void initState() {
    super.initState();
    _generateHeightMesh();

    _rotationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 16),
    )..addListener(() {
        if (_isAutoRotating) {
          setState(() {
            _azimuthAngle = (_azimuthAngle + 0.35) % 360.0;
          });
        }
      });

    _rotationController.repeat();
  }

  @override
  void didUpdateWidget(covariant Field3DViewer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.district != widget.district || oldWidget.meanNdvi != widget.meanNdvi) {
      _generateHeightMesh();
    }
  }

  @override
  void dispose() {
    _rotationController.dispose();
    super.dispose();
  }

  void _generateHeightMesh() {
    final rand = math.Random(widget.district.hashCode + 77);
    final base = widget.meanNdvi;
    _heightMesh = List.generate(_gridSize, (r) {
      return List.generate(_gridSize, (c) {
        final dist = math.sqrt(math.pow(r - 5.5, 2) + math.pow(c - 5.5, 2));
        final canopyKernel = math.exp(-dist / 3.8);
        final terrainNoise = (rand.nextDouble() - 0.5) * 0.15;
        final h = (base * (0.8 + 0.45 * canopyKernel) + terrainNoise).clamp(0.1, 0.95);
        return double.parse(h.toStringAsFixed(3));
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      color: const Color(0xFF071D12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF1B5E20)),
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
                      child: const Icon(Icons.view_in_ar, color: Color(0xFF00E676), size: 22),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? '3D فیلڈ کینوپی ٹوپوگرافی' : '3D Field Health Topography',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          widget.isUrdu ? '${widget.district} - تھری ڈی ماڈل' : '${widget.district} - Isometric Elevation Mesh',
                          style: const TextStyle(color: Colors.white60, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
                IconButton(
                  tooltip: widget.isUrdu ? 'آٹو روٹیشن آن/آف' : 'Toggle Rotation',
                  icon: Icon(
                    _isAutoRotating ? Icons.sync : Icons.sync_disabled,
                    color: _isAutoRotating ? const Color(0xFF00E676) : Colors.white54,
                  ),
                  onPressed: () {
                    setState(() => _isAutoRotating = !_isAutoRotating);
                  },
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Layer Selector
            Row(
              children: <Widget>[
                _buildLayerChip(0, widget.isUrdu ? 'کینوپی بلندی (NDVI)' : '3D Canopy Height'),
                const SizedBox(width: 8),
                _buildLayerChip(1, widget.isUrdu ? 'نمی گرڈ' : 'Moisture Saturation'),
                const SizedBox(width: 8),
                _buildLayerChip(2, widget.isUrdu ? 'رسک نوڈز' : 'Risk Hotspots'),
              ],
            ),
            const SizedBox(height: 12),

            // 3D Canvas
            GestureDetector(
              onPanUpdate: (details) {
                setState(() {
                  _isAutoRotating = false;
                  _azimuthAngle = (_azimuthAngle + details.delta.dx * 0.8) % 360.0;
                  _elevationAngle = (_elevationAngle - details.delta.dy * 0.4).clamp(15.0, 75.0);
                });
              },
              child: Container(
                height: 230,
                decoration: BoxDecoration(
                  color: Colors.black.withAlpha(120),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white12),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: CustomPaint(
                    size: const Size(double.infinity, 230),
                    painter: _Field3DMeshPainter(
                      mesh: _heightMesh,
                      azimuth: _azimuthAngle,
                      elevation: _elevationAngle,
                      layerMode: _activeLayer,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),

            // Tilt and Rotation Controls
            Row(
              children: <Widget>[
                const Icon(Icons.rotate_90_degrees_ccw, size: 16, color: Colors.white54),
                const SizedBox(width: 6),
                Text(
                  '${_azimuthAngle.toStringAsFixed(0)}°',
                  style: const TextStyle(color: Colors.white70, fontSize: 11),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.height, size: 16, color: Colors.white54),
                const SizedBox(width: 4),
                Text(
                  widget.isUrdu ? 'جھکاؤ:' : 'Tilt:',
                  style: const TextStyle(color: Colors.white54, fontSize: 11),
                ),
                Expanded(
                  child: SliderTheme(
                    data: const SliderThemeData(
                      thumbColor: Color(0xFF00E676),
                      activeTrackColor: Color(0xFF00E676),
                      inactiveTrackColor: Colors.white24,
                      trackHeight: 2,
                      thumbShape: RoundSliderThumbShape(enabledThumbRadius: 6),
                    ),
                    child: Slider(
                      value: _elevationAngle,
                      min: 15.0,
                      max: 75.0,
                      onChanged: (val) {
                        setState(() {
                          _isAutoRotating = false;
                          _elevationAngle = val;
                        });
                      },
                    ),
                  ),
                ),
                Text(
                  '${_elevationAngle.toStringAsFixed(0)}°',
                  style: const TextStyle(color: Colors.white70, fontSize: 11),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLayerChip(int id, String label) {
    final isSelected = _activeLayer == id;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _activeLayer = id),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 6),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF00E676) : const Color(0xFF0F3622),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected ? const Color(0xFF00E676) : Colors.white12,
            ),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: isSelected ? Colors.black : Colors.white70,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}

class _Field3DMeshPainter extends CustomPainter {
  _Field3DMeshPainter({
    required this.mesh,
    required this.azimuth,
    required this.elevation,
    required this.layerMode,
  });

  final List<List<double>> mesh;
  final double azimuth;
  final double elevation;
  final int layerMode;

  @override
  void paint(Canvas canvas, Size size) {
    final int rows = mesh.length;
    final int cols = mesh[0].length;

    final double cx = size.width / 2;
    final double cy = size.height / 2 + 15;

    final double radAz = azimuth * (math.pi / 180.0);
    final double radEl = elevation * (math.pi / 180.0);

    final double cosAz = math.cos(radAz);
    final double sinAz = math.sin(radAz);
    final double cosEl = math.cos(radEl);
    final double sinEl = math.sin(radEl);

    final double scale = size.width * 0.048;
    final double heightScale = 45.0;

    // Transform 3D grid point to 2D screen coordinate
    Offset project(double x, double y, double z) {
      final double centeredX = x - (cols / 2);
      final double centeredY = y - (rows / 2);

      // Rotate around Z axis (Azimuth)
      final double rotX = centeredX * cosAz - centeredY * sinAz;
      final double rotY = centeredX * sinAz + centeredY * cosAz;

      // Rotate around X axis (Elevation / Tilt)
      final double projX = rotX;
      final double projY = rotY * sinEl - (z * heightScale / scale) * cosEl;

      return Offset(cx + projX * scale, cy + projY * scale);
    }

    // Sort isometric polygon quads from back to front for proper painter's algorithm
    final List<_Quad> quads = [];

    for (int r = 0; r < rows - 1; r++) {
      for (int c = 0; c < cols - 1; c++) {
        final z0 = mesh[r][c];
        final z1 = mesh[r][c + 1];
        final z2 = mesh[r + 1][c + 1];
        final z3 = mesh[r + 1][c];

        final p0 = project(c.toDouble(), r.toDouble(), z0);
        final p1 = project((c + 1).toDouble(), r.toDouble(), z1);
        final p2 = project((c + 1).toDouble(), (r + 1).toDouble(), z2);
        final p3 = project(c.toDouble(), (r + 1).toDouble(), z3);

        // Compute depth distance from camera
        final centeredX = (c + 0.5) - (cols / 2);
        final centeredY = (r + 0.5) - (rows / 2);
        final depth = centeredX * sinAz + centeredY * cosAz;
        final avgZ = (z0 + z1 + z2 + z3) / 4.0;

        quads.add(_Quad(p0: p0, p1: p1, p2: p2, p3: p3, depth: depth, avgZ: avgZ));
      }
    }

    // Sort by depth (farthest first)
    quads.sort((a, b) => a.depth.compareTo(b.depth));

    // Render Quads
    for (final quad in quads) {
      final path = Path()
        ..moveTo(quad.p0.dx, quad.p0.dy)
        ..lineTo(quad.p1.dx, quad.p1.dy)
        ..lineTo(quad.p2.dx, quad.p2.dy)
        ..lineTo(quad.p3.dx, quad.p3.dy)
        ..close();

      Color fillColor;
      if (layerMode == 1) {
        // Moisture Saturation (Cyan -> Deep Blue)
        fillColor = Color.lerp(
          const Color(0xFF00ACC1),
          const Color(0xFF0D47A1),
          quad.avgZ.clamp(0.0, 1.0),
        )!.withAlpha(200);
      } else {
        // Canopy Elevation NDVI (Soil Brown -> Amber -> Emerald Green)
        if (quad.avgZ < 0.35) {
          fillColor = Color.lerp(
            const Color(0xFF4E342E),
            const Color(0xFFF57C00),
            quad.avgZ / 0.35,
          )!.withAlpha(220);
        } else {
          fillColor = Color.lerp(
            const Color(0xFFFBC02D),
            const Color(0xFF00E676),
            (quad.avgZ - 0.35) / 0.65,
          )!.withAlpha(235);
        }
      }

      final fillPaint = Paint()
        ..color = fillColor
        ..style = PaintingStyle.fill;
      canvas.drawPath(path, fillPaint);

      final linePaint = Paint()
        ..color = Colors.white.withAlpha(40)
        ..strokeWidth = 0.8
        ..style = PaintingStyle.stroke;
      canvas.drawPath(path, linePaint);
    }

    // Render Risk Hotspots / Sensor Pins if layer 2 active
    if (layerMode == 2) {
      final pin1Pos = project(3.0, 4.0, mesh[4][3] + 0.15);
      final pin2Pos = project(9.0, 8.0, mesh[8][9] + 0.15);

      _drawSensorPin(canvas, pin1Pos, 'Moisture Deficit', const Color(0xFFFF5252));
      _drawSensorPin(canvas, pin2Pos, 'Peak Canopy Vigor', const Color(0xFF00E676));
    }
  }

  void _drawSensorPin(Canvas canvas, Offset pos, String label, Color color) {
    // Pin shaft
    final linePaint = Paint()
      ..color = color
      ..strokeWidth = 2.0;
    canvas.drawLine(pos, Offset(pos.dx, pos.dy - 18), linePaint);

    // Glowing head
    final glowPaint = Paint()
      ..color = color.withAlpha(120)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(pos.dx, pos.dy - 18), 7.0, glowPaint);

    final dotPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(pos.dx, pos.dy - 18), 3.5, dotPaint);
  }

  @override
  bool shouldRepaint(covariant _Field3DMeshPainter oldDelegate) {
    return oldDelegate.azimuth != azimuth ||
        oldDelegate.elevation != elevation ||
        oldDelegate.layerMode != layerMode ||
        oldDelegate.mesh != mesh;
  }
}

class _Quad {
  _Quad({
    required this.p0,
    required this.p1,
    required this.p2,
    required this.p3,
    required this.depth,
    required this.avgZ,
  });

  final Offset p0, p1, p2, p3;
  final double depth;
  final double avgZ;
}
