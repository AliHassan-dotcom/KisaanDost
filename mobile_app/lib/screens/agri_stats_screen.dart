import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/agri_gdp.dart';
import '../models/agri_trade.dart';
import '../models/land_utilization.dart';
import '../models/water_availability.dart';
import '../providers/agri_stats_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';

class AgriStatsScreen extends ConsumerWidget {
  const AgriStatsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(agriStatsProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'زرعی شماریات اور تجارت' : 'Agricultural Statistics & Trade',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(agriStatsProvider.notifier).refresh(),
          ),
        ],
      ),
      body: statsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Icon(Icons.analytics_outlined, size: 48, color: Colors.grey),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'ڈیٹا لوڈ نہیں ہو سکا' : 'Failed to load agricultural statistics',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text('$err', textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(agriStatsProvider.notifier).refresh(),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) => RefreshIndicator(
          onRefresh: () => ref.read(agriStatsProvider.notifier).refresh(),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                // Section Selector Tabs
                SegmentedButton<int>(
                  segments: <ButtonSegment<int>>[
                    ButtonSegment<int>(
                      value: 0,
                      label: Text(isUrdu ? 'زمین اور پانی' : 'Land & Water'),
                      icon: const Icon(Icons.landscape),
                    ),
                    ButtonSegment<int>(
                      value: 1,
                      label: Text(isUrdu ? 'جی ڈی پی' : 'GDP Trends'),
                      icon: const Icon(Icons.show_chart),
                    ),
                    ButtonSegment<int>(
                      value: 2,
                      label: Text(isUrdu ? 'تجارت' : 'Trade'),
                      icon: const Icon(Icons.import_export),
                    ),
                  ],
                  selected: <int>{state.selectedTab},
                  onSelectionChanged: (set) {
                    if (set.isNotEmpty) {
                      ref.read(agriStatsProvider.notifier).setTab(set.first);
                    }
                  },
                ),
                const SizedBox(height: 16),

                // Tab 0: Land & Water
                if (state.selectedTab == 0) ...<Widget>[
                  // District Selector
                  Card(
                    elevation: 1,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: <Widget>[
                          Text(
                            isUrdu ? 'ضلع منتخب کریں:' : 'Select District:',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          DropdownButton<String>(
                            value: state.selectedDistrict,
                            underline: const SizedBox(),
                            items: state.allDistricts.map((d) {
                              return DropdownMenuItem<String>(
                                value: d,
                                child: Text(d),
                              );
                            }).toList(),
                            onChanged: (val) {
                              if (val != null) {
                                ref.read(agriStatsProvider.notifier).selectDistrict(val);
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  if (state.landUtilization != null)
                    _buildLandUtilizationCard(context, state.landUtilization!, isUrdu),
                  const SizedBox(height: 16),

                  if (state.landUtilization != null)
                    _buildCropAcreageCard(context, state.landUtilization!, isUrdu),
                  const SizedBox(height: 16),

                  if (state.waterAvailability != null)
                    _buildWaterAvailabilityCard(context, state.waterAvailability!, isUrdu),
                ],

                // Tab 1: GDP Trends
                if (state.selectedTab == 1) ...<Widget>[
                  _buildGdpTrendsCard(context, state.gdpSeries, isUrdu),
                ],

                // Tab 2: Trade
                if (state.selectedTab == 2) ...<Widget>[
                  if (state.tradeSummary != null)
                    _buildTradeSummaryCard(context, state.tradeSummary!, isUrdu),
                  const SizedBox(height: 16),
                  _buildExportsCard(context, state.exportsList, isUrdu),
                  const SizedBox(height: 16),
                  _buildImportsCard(context, state.importsList, isUrdu),
                ],

                const SizedBox(height: 16),
                _buildSourceAttributionCard(context, isUrdu),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLandUtilizationCard(BuildContext context, LandUtilization land, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.landscape_outlined, color: Colors.green.shade800),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'زمین کا استعمال (${land.district})' : 'Land Utilization (${land.district})',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: <Widget>[
                _buildStatMetric(
                  context,
                  isUrdu ? 'کل فارم رقبہ' : 'Total Farm Area',
                  '${_formatAcres(land.totalFarmAreaAcres)} ac',
                ),
                _buildStatMetric(
                  context,
                  isUrdu ? 'کاشت شدہ رقبہ' : 'Cultivated Area',
                  '${_formatAcres(land.cultivatedAreaAcres)} ac',
                  highlight: true,
                ),
                _buildStatMetric(
                  context,
                  isUrdu ? 'غیر کاشت شدہ' : 'Uncultivated',
                  '${_formatAcres(land.uncultivatedAreaAcres)} ac',
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'کاشت کی شرح (Cultivated Share):' : 'Cultivated Share of Farm Area:',
                  style: const TextStyle(fontSize: 12),
                ),
                Text(
                  '${land.cultivatedSharePct.toStringAsFixed(1)}%',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 4),
            LinearProgressIndicator(
              value: (land.cultivatedSharePct / 100.0).clamp(0.0, 1.0),
              backgroundColor: Colors.grey.shade200,
              color: Colors.green.shade700,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'فصلوں کی شدت (Cropping Intensity):' : 'Cropping Intensity Ratio:',
                  style: const TextStyle(fontSize: 12),
                ),
                Text(
                  '${land.croppingIntensityPct.toStringAsFixed(1)}%',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.green.shade900),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCropAcreageCard(BuildContext context, LandUtilization land, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.grass_outlined, color: Colors.amber.shade900),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'اہم فصلوں کا رقبہ (Acreage & Share)' : 'Major Crops Acreage & Share',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            _buildCropRow('Wheat (گندم)', land.wheatAreaAcres, land.wheatSharePct, Colors.amber.shade800),
            _buildCropRow('Rice / Paddy (چاول)', land.riceAreaAcres, land.riceSharePct, Colors.teal.shade700),
            _buildCropRow('Cotton (کپاس)', land.cottonAreaAcres, land.cottonSharePct, Colors.blue.shade700),
            _buildCropRow('Sugarcane (کماد)', land.sugarcaneAreaAcres, land.sugarcaneSharePct, Colors.purple.shade700),
            _buildCropRow('Maize (مکئی)', land.maizeAreaAcres, land.maizeSharePct, Colors.orange.shade800),
            _buildCropRow('Fodders (چارہ جات)', land.fodderAreaAcres, land.fodderSharePct, Colors.lightGreen.shade700),
            _buildCropRow('Orchards (باغات)', land.orchardAreaAcres, land.orchardSharePct, Colors.green.shade800),
          ],
        ),
      ),
    );
  }

  Widget _buildCropRow(String name, double acres, double sharePct, Color color) {
    if (acres <= 0 && sharePct <= 0) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: <Widget>[
          Expanded(
            flex: 4,
            child: Text(name, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
          ),
          Expanded(
            flex: 3,
            child: Text('${_formatAcres(acres)} ac', textAlign: TextAlign.right, style: const TextStyle(fontSize: 12)),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '${sharePct.toStringAsFixed(0)}%',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWaterAvailabilityCard(BuildContext context, WaterAvailability water, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.water_drop, color: Colors.blue.shade800),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'آبپاشی اور پانی کی صورتحال' : 'Water & Irrigation Sources',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Row(
                children: <Widget>[
                  Icon(Icons.waves, color: Colors.blue.shade900, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'بنیادی ذریعہ: ${water.primaryIrrigationMode}' : 'Primary Source: ${water.primaryIrrigationMode}',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.blue.shade900),
                        ),
                        Text(
                          isUrdu ? 'درجہ بندی: ${water.waterSourceClassification}' : 'Classification: ${water.waterSourceClassification}',
                          style: TextStyle(fontSize: 11, color: Colors.blue.shade800),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: <Widget>[
                _buildStatMetric(context, isUrdu ? 'آبپاشی کوریج' : 'Irrigated Ratio', '${water.irrigationCoveragePct.toStringAsFixed(1)}%', highlight: true),
                _buildStatMetric(context, isUrdu ? 'نہر فقط (Canal)' : 'Canal Only', '${water.canalOnlyPct.toStringAsFixed(1)}%'),
                _buildStatMetric(context, isUrdu ? 'ٹیوب ویل (TW)' : 'Tubewell Only', '${water.tubewellOnlyPct.toStringAsFixed(1)}%'),
                _buildStatMetric(context, isUrdu ? 'بارانی (Rainfed)' : 'Rainfed', '${water.baraniSharePct.toStringAsFixed(1)}%'),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'زیر زمین پانی کا انحصار (Groundwater):' : 'Groundwater Reliance Ratio:',
                  style: const TextStyle(fontSize: 12),
                ),
                Text(
                  '${water.groundwaterReliancePct.toStringAsFixed(1)}%',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 4),
            LinearProgressIndicator(
              value: (water.groundwaterReliancePct / 100.0).clamp(0.0, 1.0),
              backgroundColor: Colors.blue.shade100,
              color: Colors.indigo.shade700,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const Divider(height: 24),
            Text(
              isUrdu ? 'صوبائی اور قومی تناظر:' : 'Provincial & National Water Context:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
            ),
            const SizedBox(height: 6),
            Text(
              '• Punjab Annual Canal Withdrawals: ${water.provincialAnnualCanalWithdrawalsMaf} MAF\n'
              '• National Per-Capita Water Availability: ${water.provincialPerCapitaWaterM3Year.toStringAsFixed(0)} m³/year\n'
              '• Falkenmark Index Benchmark: ${water.falkenmarkStressCategory}',
              style: TextStyle(fontSize: 11, color: Colors.grey.shade800, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGdpTrendsCard(BuildContext context, List<AgriGdp> gdpList, bool isUrdu) {
    final latest = gdpList.isNotEmpty ? gdpList.first : null;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.pie_chart_outline, color: Colors.teal.shade800),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'قومی جی ڈی پی میں زراعت کا حصہ' : 'Agriculture in National GDP',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            if (latest != null) ...<Widget>[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: <Widget>[
                  _buildStatMetric(context, isUrdu ? 'جی ڈی پی حصہ (${latest.fiscalYear})' : 'Agri GDP Share (${latest.fiscalYear})', '${latest.agriGdpSharePct.toStringAsFixed(1)}%', highlight: true),
                  _buildStatMetric(context, isUrdu ? 'زرعی شرح نمو' : 'Growth Rate', '${latest.agriGrowthRatePct.toStringAsFixed(1)}%'),
                  _buildStatMetric(context, isUrdu ? 'پنجاب کا حصہ' : 'Punjab Share', '${latest.punjabAgriValueAddSharePct.toStringAsFixed(0)}%'),
                ],
              ),
              const SizedBox(height: 16),
              Text(
                isUrdu ? 'زرعی شعبوں کی تقسیم (Sub-sector Breakdown):' : 'Agri Sub-sector Contribution Breakdown:',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
              ),
              const SizedBox(height: 8),
              _buildSubsectorRow('Livestock (مویشی)', latest.livestockSubsectorSharePct, Colors.brown.shade700),
              _buildSubsectorRow('Important Crops (اہم فصلیں)', latest.importantCropsSharePct, Colors.green.shade800),
              _buildSubsectorRow('Other Crops (دیگر فصلیں)', latest.otherCropsSharePct, Colors.teal.shade700),
              _buildSubsectorRow('Forestry (جنگلات)', latest.forestrySubsectorSharePct, Colors.lightGreen.shade800),
              _buildSubsectorRow('Fisheries (ماہی پروری)', latest.fishingSubsectorSharePct, Colors.blue.shade700),
            ],
            const Divider(height: 24),
            Text(
              isUrdu ? 'تاریخی جی ڈی پی رجحان (Historical GDP Series):' : 'Historical GDP Share Series (Pakistan):',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
            ),
            const SizedBox(height: 8),
            ...gdpList.map((g) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Text('FY ${g.fiscalYear} (${g.region})', style: const TextStyle(fontSize: 12)),
                  Text('${g.agriGdpSharePct.toStringAsFixed(1)}% (Growth: ${g.agriGrowthRatePct > 0 ? "+" : ""}${g.agriGrowthRatePct.toStringAsFixed(1)}%)', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildSubsectorRow(String name, double pct, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Text(name, style: const TextStyle(fontSize: 12)),
              Text('${pct.toStringAsFixed(1)}%', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
            ],
          ),
          const SizedBox(height: 2),
          LinearProgressIndicator(
            value: (pct / 100.0).clamp(0.0, 1.0),
            backgroundColor: Colors.grey.shade200,
            color: color,
            minHeight: 6,
            borderRadius: BorderRadius.circular(3),
          ),
        ],
      ),
    );
  }

  Widget _buildTradeSummaryCard(BuildContext context, AgriTradeSummary summary, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.balance, color: Colors.indigo.shade800),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'زرعی تجارتی توازن (${summary.fiscalYear})' : 'Agri Trade Balance (${summary.fiscalYear})',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: <Widget>[
                _buildStatMetric(context, isUrdu ? 'کل برآمدات' : 'Agri Exports', '\$${summary.totalAgriExportsMillionUsd.toStringAsFixed(0)}M', highlight: true),
                _buildStatMetric(context, isUrdu ? 'کل درآمدات' : 'Agri Imports', '\$${summary.totalAgriImportsMillionUsd.toStringAsFixed(0)}M'),
                _buildStatMetric(
                  context,
                  isUrdu ? 'تجارتی خسارہ' : 'Trade Balance',
                  '\$${summary.agriTradeBalanceMillionUsd.toStringAsFixed(0)}M',
                  highlight: true,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              '• National Export Share: ${summary.agriShareOfTotalNationalExportsPct.toStringAsFixed(1)}% of Pakistan Total\n'
              '• Top Export: ${summary.topExportCommodity}\n'
              '• Top Import: ${summary.topImportCommodity}',
              style: TextStyle(fontSize: 11, color: Colors.grey.shade800, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExportsCard(BuildContext context, List<AgriTradeItem> exports, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.arrow_upward, color: Colors.green.shade800),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'اہم زرعی برآمدات (Top Exports)' : 'Major Agricultural Exports',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            ...exports.map((e) => _buildTradeItemRow(e, Colors.green.shade800)),
          ],
        ),
      ),
    );
  }

  Widget _buildImportsCard(BuildContext context, List<AgriTradeItem> imports, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.arrow_downward, color: Colors.red.shade800),
                const SizedBox(width: 8),
                Text(
                  isUrdu ? 'اہم زرعی درآمدات (Top Imports)' : 'Major Agricultural Imports',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 20),
            ...imports.map((i) => _buildTradeItemRow(i, Colors.red.shade800)),
          ],
        ),
      ),
    );
  }

  Widget _buildTradeItemRow(AgriTradeItem item, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: <Widget>[
          Expanded(
            flex: 4,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(item.commodityName, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                Text(item.partnerCountries, style: TextStyle(fontSize: 10, color: Colors.grey.shade600)),
              ],
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              '\$${item.valueMillionUsd.toStringAsFixed(0)}M',
              textAlign: TextAlign.right,
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              '${item.shareOfTradePct.toStringAsFixed(0)}%',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatMetric(BuildContext context, String label, String value, {bool highlight = false}) {
    return Column(
      children: <Widget>[
        Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: highlight ? FontWeight.bold : FontWeight.w600,
            color: highlight ? Colors.green.shade800 : Colors.black87,
          ),
        ),
      ],
    );
  }

  Widget _buildSourceAttributionCard(BuildContext context, bool isUrdu) {
    return Card(
      elevation: 0,
      color: Colors.grey.shade50,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              isUrdu ? 'سرکاری ذرائع اور تصدیق:' : 'Official Data Sources & Provenance:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
            ),
            const SizedBox(height: 4),
            Text(
              '• Pakistan Bureau of Statistics (PBS) 2024 Agricultural Census & Foreign Trade Statistics\n'
              '• Pakistan Economic Survey (Chapters 2: Agriculture & 8: Trade and Payments)\n'
              '• Indus River System Authority (IRSA) & State Bank of Pakistan (SBP)',
              style: TextStyle(fontSize: 11, color: Colors.grey.shade700, height: 1.3),
            ),
          ],
        ),
      ),
    );
  }

  String _formatAcres(double val) {
    if (val >= 1000000) {
      return '${(val / 1000000.0).toStringAsFixed(2)}M';
    } else if (val >= 1000) {
      return '${(val / 1000.0).toStringAsFixed(1)}k';
    }
    return val.toStringAsFixed(0);
  }
}
