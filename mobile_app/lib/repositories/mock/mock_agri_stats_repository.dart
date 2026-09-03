import '../../models/agri_gdp.dart';
import '../../models/agri_trade.dart';
import '../../models/land_utilization.dart';
import '../../models/water_availability.dart';
import '../agri_stats_repository.dart';

class MockAgriStatsRepository implements AgriStatsRepository {
  MockAgriStatsRepository({this.delay = const Duration(milliseconds: 100)});

  final Duration delay;

  @override
  Future<List<LandUtilization>> getLandUtilization({String? district}) async {
    await Future<void>.delayed(delay);
    final dist = district ?? 'Lahore District';
    return <LandUtilization>[
      LandUtilization(
        district: dist,
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
        dataSource: 'PBS 2024 Agricultural Census (Mock)',
        sourceYear: 2024,
      ),
    ];
  }

  @override
  Future<List<WaterAvailability>> getWaterAvailability({String? district}) async {
    await Future<void>.delayed(delay);
    final dist = district ?? 'Lahore District';
    return <WaterAvailability>[
      WaterAvailability(
        district: dist,
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
        dataSource: 'PBS 2024 Agricultural Census / Pakistan Economic Survey (Mock)',
        sourceYear: 2024,
      ),
    ];
  }

  @override
  Future<List<AgriGdp>> getGdp({String? province}) async {
    await Future<void>.delayed(delay);
    return const <AgriGdp>[
      AgriGdp(
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
        dataSource: 'Pakistan Economic Survey (Mock)',
      ),
      AgriGdp(
        fiscalYear: '2024-25',
        region: 'Pakistan',
        agriGdpSharePct: 23.8,
        agriGrowthRatePct: 3.8,
        cropsSubsectorSharePct: 34.6,
        importantCropsSharePct: 21.6,
        otherCropsSharePct: 13.0,
        livestockSubsectorSharePct: 61.5,
        forestrySubsectorSharePct: 2.1,
        fishingSubsectorSharePct: 1.8,
        punjabAgriValueAddSharePct: 62.6,
        dataSource: 'Pakistan Economic Survey (Mock)',
      ),
    ];
  }

  @override
  Future<List<AgriTradeItem>> getExports({String? commodity}) async {
    await Future<void>.delayed(delay);
    return const <AgriTradeItem>[
      AgriTradeItem(
        commodityGroup: 'Grains & Cereals',
        commodityName: 'Rice (Basmati & IRRI)',
        fiscalYear: '2023-24',
        valueMillionUsd: 3880.0,
        quantityThousandMt: 5950.0,
        shareOfTradePct: 73.9,
        partnerCountries: 'EU, UAE, China, Kenya',
        tradeType: 'export',
        dataSource: 'PBS / Economic Survey (Mock)',
      ),
      AgriTradeItem(
        commodityGroup: 'Fibers & Textiles',
        commodityName: 'Raw Cotton & Yarn',
        fiscalYear: '2023-24',
        valueMillionUsd: 480.0,
        quantityThousandMt: 220.0,
        shareOfTradePct: 9.1,
        partnerCountries: 'China, Bangladesh',
        tradeType: 'export',
        dataSource: 'PBS / Economic Survey (Mock)',
      ),
    ];
  }

  @override
  Future<List<AgriTradeItem>> getImports({String? commodity}) async {
    await Future<void>.delayed(delay);
    return const <AgriTradeItem>[
      AgriTradeItem(
        commodityGroup: 'Edible Oils',
        commodityName: 'Palm Oil & Soybean Oil',
        fiscalYear: '2023-24',
        valueMillionUsd: 3450.0,
        quantityThousandMt: 3200.0,
        shareOfTradePct: 41.6,
        partnerCountries: 'Indonesia, Malaysia',
        tradeType: 'import',
        dataSource: 'PBS / Economic Survey (Mock)',
      ),
      AgriTradeItem(
        commodityGroup: 'Food Staples',
        commodityName: 'Pulses & Legumes',
        fiscalYear: '2023-24',
        valueMillionUsd: 720.0,
        quantityThousandMt: 1150.0,
        shareOfTradePct: 8.7,
        partnerCountries: 'Canada, Australia',
        tradeType: 'import',
        dataSource: 'PBS / Economic Survey (Mock)',
      ),
    ];
  }

  @override
  Future<List<AgriTradeSummary>> getTradeSummary() async {
    await Future<void>.delayed(delay);
    return const <AgriTradeSummary>[
      AgriTradeSummary(
        fiscalYear: '2023-24',
        totalAgriExportsMillionUsd: 5250.0,
        totalAgriImportsMillionUsd: 8300.0,
        agriTradeBalanceMillionUsd: -3050.0,
        agriShareOfTotalNationalExportsPct: 17.5,
        agriShareOfTotalNationalImportsPct: 15.2,
        topExportCommodity: 'Rice (All Varieties - \$3,880M)',
        topImportCommodity: 'Palm Oil & Edible Oils (\$3,450M)',
        dataSource: 'Pakistan Economic Survey (Mock)',
      ),
    ];
  }
}

