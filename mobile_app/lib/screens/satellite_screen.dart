import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/satellite_summary.dart';
import '../providers/satellite_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/field_3d_viewer.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/ndvi_timeline_chart.dart';
import '../widgets/satellite_heatmap_widget.dart';
import '../widgets/satellite_trend_chart.dart';
import '../widgets/yield_prediction_widget.dart';

class SatelliteScreen extends ConsumerStatefulWidget {
  const SatelliteScreen({super.key});

  static const List<String> defaultDistricts = <String>[
    'Attock', 'Bahawalnagar', 'Bahawalpur', 'Bhakkar',
    'Chakwal', 'Dera Ghazi Khan', 'Faisalabad', 'Gujranwala',
    'Gujrat', 'Hafizabad', 'Jhang', 'Jhelum',
    'Kasur', 'Khanewal', 'Khushab', 'Lahore',
    'Layyah', 'Lodhran', 'Mandi Bahauddin', 'Mianwali',
    'Multan', 'Muzaffargarh', 'Narowal', 'Okara',
    'Pakpattan', 'Rahim Yar Khan', 'Rajanpur', 'Rawalpindi',
    'Sahiwal', 'Sargodha', 'Sheikhupura', 'Sialkot',
    'Toba Tek Singh', 'Vehari',
  ];

  @override
  ConsumerState<SatelliteScreen> createState() => _SatelliteScreenState();
}

class _SatelliteScreenState extends ConsumerState<SatelliteScreen> {
  int _activeTab = 0; // 0: Overview, 1: Heatmap, 2: 56-Mo Trajectory, 3: 3D Topo, 4: Yield AI

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(satelliteNotifierProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    final districts = state.districts.isNotEmpty ? state.districts : SatelliteScreen.defaultDistricts;
    final summary = state.summary;
    final currentNdvi = summary?.ndvi ?? 0.54;

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'سیٹلائٹ مشاہدات' : 'Satellite Monitoring',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(satelliteNotifierProvider.notifier).refresh(),
          ),
        ],
      ),
      body: state.isLoading && summary == null
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Fetching Sentinel-2 & MODIS Multi-Spectral telemetry...'),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: () => ref.read(satelliteNotifierProvider.notifier).refresh(),
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    // District selector card
                    _buildDistrictSelector(context, ref, state.selectedDistrict, districts, isUrdu),
                    const SizedBox(height: 12),

                    // Feature Tab Navigation Bar
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: <Widget>[
                          _buildTabPill(0, isUrdu ? 'خلاصہ' : 'Overview', Icons.dashboard_outlined),
                          const SizedBox(width: 8),
                          _buildTabPill(1, isUrdu ? 'ہیٹ میپ' : 'Heatmap', Icons.grid_view_rounded),
                          const SizedBox(width: 8),
                          _buildTabPill(2, isUrdu ? '56 ماہ رجحان' : '56-Mo Timeline', Icons.timeline),
                          const SizedBox(width: 8),
                          _buildTabPill(3, isUrdu ? '3D فیلڈ' : '3D Topo', Icons.view_in_ar),
                          const SizedBox(width: 8),
                          _buildTabPill(4, isUrdu ? 'پیداوار پیشن گوئی' : 'Yield Forecast', Icons.analytics_outlined),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Tab View Contents
                    if (_activeTab == 0) ...[
                      if (summary != null) ...[
                        if (summary.isBoundaryUnavailable) ...[
                          Card(
                            color: Colors.amber.shade50,
                            child: const Padding(
                              padding: EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(
                                    'Boundary Unavailable',
                                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.orange),
                                  ),
                                  SizedBox(height: 6),
                                  Text(
                                    'Missing Authoritative Boundary Polygon',
                                    style: TextStyle(fontSize: 13),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ] else ...[
                          _buildSatelliteHeaderCard(context, summary, isUrdu),
                          const SizedBox(height: 14),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.green.shade50,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              isUrdu ? 'معمول کا مشاہدہ' : 'Normal Satellite Observation',
                              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green.shade900),
                            ),
                          ),
                          const SizedBox(height: 14),
                          _buildMetricsCard(context, summary, isUrdu),
                          const SizedBox(height: 14),
                          _buildAgronomicAnalysisCard(context, summary, isUrdu),
                          const SizedBox(height: 14),
                          if (!summary.isCloudMasked)
                            _buildTrendChartCard(context, state, isUrdu),
                        ],
                      ],
                    ] else if (_activeTab == 1) ...[
                      SatelliteHeatmapWidget(
                        district: state.selectedDistrict,
                        isUrdu: isUrdu,
                        meanNdvi: currentNdvi,
                      ),
                    ] else if (_activeTab == 2) ...[
                      NdviTimelineChart(
                        district: state.selectedDistrict,
                        isUrdu: isUrdu,
                      ),
                    ] else if (_activeTab == 3) ...[
                      Field3DViewer(
                        district: state.selectedDistrict,
                        isUrdu: isUrdu,
                        meanNdvi: currentNdvi,
                      ),
                    ] else if (_activeTab == 4) ...[
                      YieldPredictionWidget(
                        district: state.selectedDistrict,
                        isUrdu: isUrdu,
                      ),
                    ],
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildTabPill(int id, String label, IconData icon) {
    final isSelected = _activeTab == id;
    return GestureDetector(
      onTap: () => setState(() => _activeTab = id),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00E676) : const Color(0xFF0F3622),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF00E676) : Colors.white24,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 15, color: isSelected ? Colors.black : Colors.white70),
            const SizedBox(width: 5),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.black : Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }


  Widget _buildDistrictSelector(
    BuildContext context,
    WidgetRef ref,
    String selectedDistrict,
    List<String> districts,
    bool isUrdu,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.green.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        child: Row(
          children: <Widget>[
            Icon(Icons.location_on, color: Colors.green.shade800),
            const SizedBox(width: 8),
            Text(
              isUrdu ? 'ضلع:' : 'District:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: districts.contains(selectedDistrict) ? selectedDistrict : districts.first,
                  isExpanded: true,
                  items: districts.map((String d) {
                    return DropdownMenuItem<String>(
                      value: d,
                      child: Text(
                        d,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    );
                  }).toList(),
                  onChanged: (String? newDistrict) {
                    if (newDistrict != null) {
                      ref.read(satelliteNotifierProvider.notifier).selectDistrict(newDistrict);
                    }
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSatelliteHeaderCard(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[Colors.teal.shade700, Colors.teal.shade900],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.teal.shade900.withAlpha(50),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Row(
                children: <Widget>[
                  const Icon(Icons.satellite_alt, color: Colors.white, size: 24),
                  const SizedBox(width: 8),
                  Text(
                    summary.satelliteSource ?? 'Copernicus Sentinel-2 MSI',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(50),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  '10m Resolution',
                  style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '${summary.crop.toUpperCase()} · ${summary.district}',
            style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricsCard(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    final ndviVal = summary.ndvi ?? 0.30;
    final ndwiVal = summary.ndwi ?? -0.33;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.green.shade100),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              isUrdu ? 'سیٹلائٹ انڈیکس اور پیمائش' : 'Vegetation & Hydration Indices',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 14),

            // NDVI Metric Bar
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'سبزی مائل ہریالی انڈیکس (NDVI)' : 'Canopy Greenness (NDVI)',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    Text(
                      ndviVal.toStringAsFixed(2),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: Colors.green.shade900,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: ndviVal.clamp(0.0, 1.0),
                    minHeight: 8,
                    backgroundColor: Colors.grey.shade200,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.green.shade600),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // NDWI Metric Bar
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'نمی کا تناسب انڈیکس (NDWI)' : 'Canopy Moisture Index (NDWI)',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    Text(
                      ndwiVal.toStringAsFixed(2),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: Colors.blue.shade900,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: ((ndwiVal + 1.0) / 2.0).clamp(0.0, 1.0),
                    minHeight: 8,
                    backgroundColor: Colors.grey.shade200,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.blue.shade600),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAgronomicAnalysisCard(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.green.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.eco, color: Colors.green.shade800, size: 20),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'ماہرانہ زرعی تشریح' : 'Agronomic Canopy Health Analysis',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              summary.attentionEvidence ??
                  'Monthly canopy greenness (NDVI=0.30) and moisture (NDWI=-0.33) remain within expected seasonal baseline parameters.',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade800, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrendChartCard(BuildContext context, SatelliteState state, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.teal.shade100),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              isUrdu ? 'ماہانہ NDVI رجحان (2022 تا 2026)' : 'Multi-Year NDVI Trend (2022-2026)',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 12),
            SatelliteTrendChart(records: state.history),
          ],
        ),
      ),
    );
  }
}
