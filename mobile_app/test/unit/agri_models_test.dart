import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/land_utilization.dart';
import 'package:kisaan_dost/models/water_availability.dart';
import 'package:kisaan_dost/repositories/mock/mock_agri_stats_repository.dart';

void main() {
  group('LandUtilization', () {
    test('parses LandUtilization JSON correctly', () {
      final json = <String, dynamic>{
        'district': 'Lahore District',
        'total_farm_area_acres': 150048.0,
        'cultivated_area_acres': 147875.0,
        'uncultivated_area_acres': 2173.0,
        'total_cropped_area_acres': 260381.0,
        'cultivated_share_pct': 98.55,
        'cropping_intensity_pct': 176.08,
        'wheat_area_acres': 88566.0,
        'wheat_share_pct': 34.0,
        'rice_area_acres': 76043.0,
        'rice_share_pct': 29.0,
        'cotton_area_acres': 0.0,
        'cotton_share_pct': 0.0,
        'sugarcane_area_acres': 212.0,
        'sugarcane_share_pct': 0.0,
        'maize_area_acres': 5779.0,
        'maize_share_pct': 2.0,
        'fodder_area_acres': 73060.0,
        'fodder_share_pct': 28.0,
        'orchard_area_acres': 1476.0,
        'orchard_share_pct': 1.0,
        'kharif_total_acres': 120612.0,
        'rabi_total_acres': 139769.0,
        'data_source': 'PBS 2024 Agricultural Census',
        'source_year': 2024,
      };

      final land = LandUtilization.fromJson(json);
      expect(land.district, 'Lahore District');
      expect(land.totalFarmAreaAcres, 150048.0);
      expect(land.cultivatedAreaAcres, 147875.0);
      expect(land.wheatAreaAcres, 88566.0);
      expect(land.cultivatedSharePct, 98.55);
      expect(land.sourceYear, 2024);
    });
  });

  group('WaterAvailability', () {
    test('parses WaterAvailability JSON correctly', () {
      final json = <String, dynamic>{
        'district': 'Lahore District',
        'total_cultivated_area_acres': 147875.0,
        'irrigated_area_acres': 131726.0,
        'unirrigated_area_acres': 4.0,
        'irrigation_coverage_pct': 89.08,
        'canal_only_acres': 14022.0,
        'canal_only_pct': 10.64,
        'canal_and_tubewell_acres': 24982.0,
        'canal_and_tubewell_pct': 18.97,
        'tubewell_only_acres': 92699.0,
        'tubewell_only_pct': 70.37,
        'barani_rainfed_acres': 0.0,
        'barani_share_pct': 0.0,
        'sailaba_flood_acres': 0.0,
        'groundwater_reliance_pct': 79.85,
        'canal_surface_reliance_pct': 20.13,
        'primary_irrigation_mode': 'Tubewell (Groundwater)',
        'water_source_classification': 'Groundwater Dominant',
        'provincial_annual_canal_withdrawals_maf': 53.5,
        'provincial_per_capita_water_m3_year': 860.0,
        'falkenmark_stress_category': 'Water-Stressed (<1,000 m3/capita)',
        'data_source': 'PBS 2024 Agricultural Census / Pakistan Economic Survey',
        'source_year': 2024,
      };

      final water = WaterAvailability.fromJson(json);
      expect(water.district, 'Lahore District');
      expect(water.irrigationCoveragePct, 89.08);
      expect(water.tubewellOnlyPct, 70.37);
      expect(water.groundwaterReliancePct, 79.85);
      expect(water.provincialAnnualCanalWithdrawalsMaf, 53.5);
    });
  });

  group('MockAgriStatsRepository', () {
    test('returns mock LandUtilization and WaterAvailability for district', () async {
      final repo = MockAgriStatsRepository(delay: Duration.zero);
      final land = await repo.getLandUtilization(district: 'Lahore District');
      expect(land.length, 1);
      expect(land.first.district, 'Lahore District');
      expect(land.first.cultivatedSharePct, 98.55);

      final water = await repo.getWaterAvailability(district: 'Lahore District');
      expect(water.length, 1);
      expect(water.first.district, 'Lahore District');
      expect(water.first.primaryIrrigationMode, 'Tubewell (Groundwater)');

      final gdp = await repo.getGdp();
      expect(gdp.length, 2);
      expect(gdp.first.agriGdpSharePct, 24.0);

      final exports = await repo.getExports();
      expect(exports.length, 2);
      expect(exports.first.valueMillionUsd, 3880.0);

      final imports = await repo.getImports();
      expect(imports.length, 2);
      expect(imports.first.valueMillionUsd, 3450.0);

      final summary = await repo.getTradeSummary();
      expect(summary.length, 1);
      expect(summary.first.agriTradeBalanceMillionUsd, -3050.0);
    });
  });
}

