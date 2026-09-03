import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/agri_gdp.dart';
import 'package:kisaan_dost/models/agri_trade.dart';
import 'package:kisaan_dost/models/land_utilization.dart';
import 'package:kisaan_dost/models/water_availability.dart';
import 'package:kisaan_dost/providers/agri_stats_provider.dart';
import 'package:kisaan_dost/screens/agri_stats_screen.dart';

class _StaticAgriStatsNotifier extends AgriStatsNotifier {
  _StaticAgriStatsNotifier(this._state);

  final AgriStatsState _state;

  @override
  Future<AgriStatsState> build() async {
    return _state;
  }

  @override
  Future<void> selectDistrict(String district) async {}

  @override
  void setTab(int tabIndex) {
    state = AsyncData(_state.copyWith(selectedTab: tabIndex));
  }

  @override
  Future<void> refresh() async {}
}

void main() {
  final sampleLand = LandUtilization(
    district: 'Lahore District',
    totalFarmAreaAcres: 150048.0,
    cultivatedAreaAcres: 147875.0,
    uncultivatedAreaAcres: 2173.0,
    totalCroppedAreaAcres: 260381.0,
    cultivatedSharePct: 98.55,
    croppingIntensityPct: 176.08,
    wheatAreaAcres: 88566.0,
    wheatSharePct: 34.0,
    riceAreaAcres: 76043.0,
    riceSharePct: 29.0,
    cottonAreaAcres: 0.0,
    cottonSharePct: 0.0,
    sugarcaneAreaAcres: 212.0,
    sugarcaneSharePct: 0.0,
    maizeAreaAcres: 5779.0,
    maizeSharePct: 2.0,
    fodderAreaAcres: 73060.0,
    fodderSharePct: 28.0,
    orchardAreaAcres: 1476.0,
    orchardSharePct: 1.0,
    kharifTotalAcres: 120612.0,
    rabiTotalAcres: 139769.0,
    dataSource: 'PBS 2024 Agricultural Census',
    sourceYear: 2024,
  );

  final sampleWater = WaterAvailability(
    district: 'Lahore District',
    totalCultivatedAreaAcres: 147875.0,
    irrigatedAreaAcres: 131726.0,
    unirrigatedAreaAcres: 4.0,
    irrigationCoveragePct: 89.08,
    canalOnlyAcres: 14022.0,
    canalOnlyPct: 10.64,
    canalAndTubewellAcres: 24982.0,
    canalAndTubewellPct: 18.97,
    tubewellOnlyAcres: 92699.0,
    tubewellOnlyPct: 70.37,
    baraniRainfedAcres: 0.0,
    baraniSharePct: 0.0,
    sailabaFloodAcres: 0.0,
    groundwaterReliancePct: 79.85,
    canalSurfaceReliancePct: 20.13,
    primaryIrrigationMode: 'Tubewell (Groundwater)',
    waterSourceClassification: 'Groundwater Dominant',
    provincialAnnualCanalWithdrawalsMaf: 53.5,
    provincialPerCapitaWaterM3Year: 860.0,
    falkenmarkStressCategory: 'Water-Stressed (<1,000 m3/capita)',
    dataSource: 'PBS 2024 Agricultural Census / Pakistan Economic Survey',
    sourceYear: 2024,
  );

  final sampleGdp = <AgriGdp>[
    const AgriGdp(
      fiscalYear: '2023-24',
      region: 'Pakistan',
      agriGdpSharePct: 24.0,
      agriGrowthRatePct: 6.3,
      cropsSubsectorSharePct: 35.4,
      importantCropsSharePct: 22.4,
      otherCropsSharePct: 13.0,
      livestockSubsectorSharePct: 60.8,
      forestrySubsectorSharePct: 2.1,
      fishingSubsectorSharePct: 1.7,
      punjabAgriValueAddSharePct: 63.0,
      dataSource: 'Pakistan Economic Survey',
    ),
  ];

  final sampleExports = <AgriTradeItem>[
    const AgriTradeItem(
      commodityGroup: 'Grains & Cereals',
      commodityName: 'Rice (Basmati)',
      fiscalYear: '2023-24',
      valueMillionUsd: 950.0,
      quantityThousandMt: 850.0,
      shareOfTradePct: 18.1,
      partnerCountries: 'EU, UAE',
      tradeType: 'export',
      dataSource: 'PBS',
    ),
  ];

  final sampleImports = <AgriTradeItem>[
    const AgriTradeItem(
      commodityGroup: 'Edible Oils',
      commodityName: 'Palm Oil',
      fiscalYear: '2023-24',
      valueMillionUsd: 3450.0,
      quantityThousandMt: 3200.0,
      shareOfTradePct: 41.6,
      partnerCountries: 'Indonesia, Malaysia',
      tradeType: 'import',
      dataSource: 'PBS',
    ),
  ];

  final sampleSummary = const AgriTradeSummary(
    fiscalYear: '2023-24',
    totalAgriExportsMillionUsd: 5250.0,
    totalAgriImportsMillionUsd: 8300.0,
    agriTradeBalanceMillionUsd: -3050.0,
    agriShareOfTotalNationalExportsPct: 17.5,
    agriShareOfTotalNationalImportsPct: 15.2,
    topExportCommodity: 'Rice',
    topImportCommodity: 'Palm Oil',
    dataSource: 'Pakistan Economic Survey',
  );

  testWidgets('AgriStatsScreen renders tabs, land, GDP, and trade views', (WidgetTester tester) async {
    final state = AgriStatsState(
      selectedDistrict: 'Lahore District',
      landUtilization: sampleLand,
      waterAvailability: sampleWater,
      gdpSeries: sampleGdp,
      exportsList: sampleExports,
      importsList: sampleImports,
      tradeSummary: sampleSummary,
      selectedTab: 0,
      allDistricts: const ['Lahore District', 'Faisalabad District'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          agriStatsProvider.overrideWith(() => _StaticAgriStatsNotifier(state)),
        ],
        child: const MaterialApp(
          home: AgriStatsScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Agricultural Statistics & Trade'), findsOneWidget);
    expect(find.text('Land & Water'), findsOneWidget);
    expect(find.text('GDP Trends'), findsOneWidget);
    expect(find.text('Trade'), findsOneWidget);

    // Tab 0 Land & Water checks
    expect(find.text('Select District:'), findsOneWidget);
    expect(find.text('Lahore District'), findsWidgets);
    expect(find.text('Land Utilization (Lahore District)'), findsOneWidget);
    expect(find.text('Total Farm Area'), findsOneWidget);
    expect(find.text('Cultivated Area'), findsOneWidget);
    expect(find.text('Major Crops Acreage & Share'), findsOneWidget);
    expect(find.text('Wheat (گندم)'), findsOneWidget);
    expect(find.text('Water & Irrigation Sources'), findsOneWidget);
    expect(find.text('Primary Source: Tubewell (Groundwater)'), findsOneWidget);
  });
}
