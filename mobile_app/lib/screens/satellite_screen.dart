import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/satellite_summary.dart';
import '../providers/satellite_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/satellite_trend_chart.dart';
import '../widgets/status_badge.dart';

class SatelliteScreen extends ConsumerWidget {
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
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(satelliteNotifierProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    final districts = state.districts.isNotEmpty ? state.districts : defaultDistricts;
    final summary = state.summary;

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
          ? const Center(child: CircularProgressIndicator())
          : state.errorMessage != null && summary == null
              ? _buildErrorView(context, ref, state.errorMessage!, isUrdu)
              : RefreshIndicator(
                  onRefresh: () => ref.read(satelliteNotifierProvider.notifier).refresh(),
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        // District selector
                        _buildDistrictSelector(context, ref, state.selectedDistrict, districts, isUrdu),
                        const SizedBox(height: 16),

                        if (summary != null) ...<Widget>[
                          // Source & Metadata banner
                          _buildSourceBanner(context, summary, isUrdu),
                          const SizedBox(height: 12),

                          // Explainable Attention Card
                          _buildAttentionCard(context, summary, isUrdu),
                          const SizedBox(height: 12),

                          // Boundary Unavailable Warning if applicable
                          if (summary.isBoundaryUnavailable)
                            _buildBoundaryWarning(context, summary, isUrdu)
                          else if (summary.isCloudMasked)
                            _buildCloudMaskWarning(context, summary, isUrdu)
                          else ...<Widget>[
                            // Metric Cards (NDVI & NDWI)
                            _buildMetricsRow(context, summary, isUrdu),
                            const SizedBox(height: 16),

                            // Monthly Trend Chart Card
                            _buildTrendChartCard(context, state, isUrdu),
                          ],
                        ],
                      ],
                    ),
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
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: Row(
          children: <Widget>[
            Icon(Icons.location_on, color: Theme.of(context).primaryColor),
            const SizedBox(width: 8),
            Text(
              isUrdu ? 'ضلع:' : 'District:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: districts.contains(selectedDistrict) ? selectedDistrict : districts.first,
                  isExpanded: true,
                  items: districts.map((String d) {
                    final isMissing = {'Bhakkar', 'Jhang', 'Layyah', 'Muzaffargarh', 'Okara'}.contains(d);
                    return DropdownMenuItem<String>(
                      value: d,
                      child: Text(
                        isMissing ? '$d (No boundary)' : d,
                        style: TextStyle(
                          color: isMissing ? Colors.grey.shade700 : Colors.black87,
                          fontStyle: isMissing ? FontStyle.italic : FontStyle.normal,
                        ),
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

  Widget _buildSourceBanner(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.blue.shade200),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(Icons.satellite_alt, size: 18, color: Colors.blue.shade800),
              const SizedBox(width: 6),
              Text(
                summary.satelliteSource ?? 'Sentinel-2 MSI Level-2A',
                style: TextStyle(fontSize: 12, color: Colors.blue.shade900, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          StatusBadge(status: summary.status),
        ],
      ),
    );
  }

  Widget _buildAttentionCard(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    Color cardColor;
    Color iconColor;
    IconData icon;
    String statusTitle;

    switch (summary.healthTrend) {
      case 'vegetation_attention':
        cardColor = Colors.amber.shade50;
        iconColor = Colors.amber.shade900;
        icon = Icons.warning_amber_rounded;
        statusTitle = isUrdu ? 'پودوں کی سبزی مائل توجہ' : 'Vegetation Attention';
        break;
      case 'water_attention':
        cardColor = Colors.blue.shade50;
        iconColor = Colors.blue.shade800;
        icon = Icons.water_drop_outlined;
        statusTitle = isUrdu ? 'نمی میں تبدیلی کی توجہ' : 'Water / Moisture Attention';
        break;
      case 'boundary_unavailable':
        cardColor = Colors.grey.shade100;
        iconColor = Colors.grey.shade800;
        icon = Icons.map_outlined;
        statusTitle = isUrdu ? 'حدود دستیاب نہیں' : 'Boundary Unavailable';
        break;
      case 'insufficient_satellite_data':
        cardColor = Colors.orange.shade50;
        iconColor = Colors.orange.shade800;
        icon = Icons.cloud_off_outlined;
        statusTitle = isUrdu ? 'سیٹلائٹ ڈیٹا دستیاب نہیں' : 'Cloud Masked / No Pixels';
        break;
      case 'normal_observation':
      default:
        cardColor = Colors.green.shade50;
        iconColor = Colors.green.shade800;
        icon = Icons.check_circle_outline;
        statusTitle = isUrdu ? 'معمول کا مشاہدہ' : 'Normal Satellite Observation';
        break;
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: iconColor.withAlpha(80)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(icon, color: iconColor, size: 20),
              const SizedBox(width: 8),
              Text(
                statusTitle,
                style: TextStyle(fontWeight: FontWeight.bold, color: iconColor, fontSize: 14),
              ),
            ],
          ),
          if (summary.attentionEvidence != null) ...<Widget>[
            const SizedBox(height: 6),
            Text(
              summary.attentionEvidence!,
              style: TextStyle(fontSize: 12, color: Colors.grey.shade900, height: 1.3),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBoundaryWarning(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.amber.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.amber.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(Icons.info_outline, color: Colors.amber.shade900),
              const SizedBox(width: 8),
              Text(
                isUrdu ? 'سرکاری باؤنڈری پولیگون موجود نہیں' : 'Missing Authoritative Boundary Polygon',
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.amber.shade900),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            isUrdu
                ? 'اس ضلع کے لیے سرکاری نقشہ سازی ریکارڈز میں پولیگون کی عدم موجودگی کی وجہ سے سیٹلائٹ انڈیکس کا تخمینہ نہیں لگایا گیا۔ غلط اندازوں سے بچنے کے لیے ڈیٹا کو خالی رکھا گیا ہے۔'
                : 'Zonal satellite aggregation is not performed because an authoritative boundary polygon is absent in the provincial GIS dataset. To prevent false approximations, metrics are safely withheld as null.',
            style: const TextStyle(fontSize: 13, height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _buildCloudMaskWarning(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: const <Widget>[
              Icon(Icons.cloud_queue, color: Colors.grey),
              SizedBox(width: 8),
              Text(
                'Complete Optical Cloud / Fog Masking',
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Heavy cloud cover or atmospheric fog obscured optical sensor acquisitions for this month. No cloud-free pixels were available.',
            style: TextStyle(fontSize: 13, height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricsRow(BuildContext context, SatelliteSummary summary, bool isUrdu) {
    return Row(
      children: <Widget>[
        Expanded(
          child: _metricCard(
            context,
            title: 'NDVI (Canopy Greenness)',
            value: summary.ndvi != null ? summary.ndvi!.toStringAsFixed(2) : '--',
            median: summary.ndviMedian != null ? summary.ndviMedian!.toStringAsFixed(2) : '--',
            color: Colors.green.shade700,
            icon: Icons.eco_outlined,
            isUrdu: isUrdu,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _metricCard(
            context,
            title: 'NDWI (Canopy Moisture)',
            value: summary.ndwi != null ? summary.ndwi!.toStringAsFixed(2) : '--',
            median: summary.ndwiMedian != null ? summary.ndwiMedian!.toStringAsFixed(2) : '--',
            color: Colors.blue.shade700,
            icon: Icons.water_drop_outlined,
            isUrdu: isUrdu,
          ),
        ),
      ],
    );
  }

  Widget _metricCard(
    BuildContext context, {
    required String title,
    required String value,
    required String median,
    required Color color,
    required IconData icon,
    required bool isUrdu,
  }) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(icon, size: 16, color: color),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 4),
            Text(
              'Median: $median',
              style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrendChartCard(BuildContext context, SatelliteState state, bool isUrdu) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'ماہانہ سیٹلائٹ رجحان (2022–2025)' : 'Monthly Satellite Trend (2022–2025)',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                ),
                Text(
                  '${state.history.length} mos',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SatelliteTrendChart(records: state.history),
            const SizedBox(height: 8),
            Text(
              isUrdu
                  ? 'نوٹ: یہ ڈیٹا تاریخی ماحولیاتی مانیٹرنگ کے لیے ہے۔ یہ فصل کی بیماری کی تشخیص نہیں ہے۔'
                  : 'Note: Historical satellite baseline for regional monitoring. Not a crop disease diagnosis.',
              style: TextStyle(fontSize: 10, color: Colors.grey.shade600, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorView(BuildContext context, WidgetRef ref, String error, bool isUrdu) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              isUrdu ? 'سیٹلائٹ ڈیٹا لوڈ نہیں ہو سکا' : 'Could not load satellite data',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              error,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.read(satelliteNotifierProvider.notifier).refresh(),
              child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
