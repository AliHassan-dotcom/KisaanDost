class WaterAvailability {
  const WaterAvailability({
    required this.district,
    required this.totalCultivatedAreaAcres,
    required this.irrigatedAreaAcres,
    required this.unirrigatedAreaAcres,
    required this.irrigationCoveragePct,
    required this.canalOnlyAcres,
    required this.canalOnlyPct,
    required this.canalAndTubewellAcres,
    required this.canalAndTubewellPct,
    required this.tubewellOnlyAcres,
    required this.tubewellOnlyPct,
    required this.baraniRainfedAcres,
    required this.baraniSharePct,
    required this.sailabaFloodAcres,
    required this.groundwaterReliancePct,
    required this.canalSurfaceReliancePct,
    required this.primaryIrrigationMode,
    required this.waterSourceClassification,
    required this.provincialAnnualCanalWithdrawalsMaf,
    required this.provincialPerCapitaWaterM3Year,
    required this.falkenmarkStressCategory,
    required this.dataSource,
    required this.sourceYear,
  });

  final String district;
  final double totalCultivatedAreaAcres;
  final double irrigatedAreaAcres;
  final double unirrigatedAreaAcres;
  final double irrigationCoveragePct;
  final double canalOnlyAcres;
  final double canalOnlyPct;
  final double canalAndTubewellAcres;
  final double canalAndTubewellPct;
  final double tubewellOnlyAcres;
  final double tubewellOnlyPct;
  final double baraniRainfedAcres;
  final double baraniSharePct;
  final double sailabaFloodAcres;
  final double groundwaterReliancePct;
  final double canalSurfaceReliancePct;
  final String primaryIrrigationMode;
  final String waterSourceClassification;
  final double provincialAnnualCanalWithdrawalsMaf;
  final double provincialPerCapitaWaterM3Year;
  final String falkenmarkStressCategory;
  final String dataSource;
  final int sourceYear;

  factory WaterAvailability.fromJson(Map<String, dynamic> json) {
    return WaterAvailability(
      district: (json['district'] as String?) ?? '',
      totalCultivatedAreaAcres: (json['total_cultivated_area_acres'] as num?)?.toDouble() ?? 0.0,
      irrigatedAreaAcres: (json['irrigated_area_acres'] as num?)?.toDouble() ?? 0.0,
      unirrigatedAreaAcres: (json['unirrigated_area_acres'] as num?)?.toDouble() ?? 0.0,
      irrigationCoveragePct: (json['irrigation_coverage_pct'] as num?)?.toDouble() ?? 0.0,
      canalOnlyAcres: (json['canal_only_acres'] as num?)?.toDouble() ?? 0.0,
      canalOnlyPct: (json['canal_only_pct'] as num?)?.toDouble() ?? 0.0,
      canalAndTubewellAcres: (json['canal_and_tubewell_acres'] as num?)?.toDouble() ?? 0.0,
      canalAndTubewellPct: (json['canal_and_tubewell_pct'] as num?)?.toDouble() ?? 0.0,
      tubewellOnlyAcres: (json['tubewell_only_acres'] as num?)?.toDouble() ?? 0.0,
      tubewellOnlyPct: (json['tubewell_only_pct'] as num?)?.toDouble() ?? 0.0,
      baraniRainfedAcres: (json['barani_rainfed_acres'] as num?)?.toDouble() ?? 0.0,
      baraniSharePct: (json['barani_share_pct'] as num?)?.toDouble() ?? 0.0,
      sailabaFloodAcres: (json['sailaba_flood_acres'] as num?)?.toDouble() ?? 0.0,
      groundwaterReliancePct: (json['groundwater_reliance_pct'] as num?)?.toDouble() ?? 0.0,
      canalSurfaceReliancePct: (json['canal_surface_reliance_pct'] as num?)?.toDouble() ?? 0.0,
      primaryIrrigationMode: (json['primary_irrigation_mode'] as String?) ?? 'Canal & Tubewell (Conjunctive)',
      waterSourceClassification: (json['water_source_classification'] as String?) ?? 'Conjunctive Irrigation System',
      provincialAnnualCanalWithdrawalsMaf: (json['provincial_annual_canal_withdrawals_maf'] as num?)?.toDouble() ?? 53.5,
      provincialPerCapitaWaterM3Year: (json['provincial_per_capita_water_m3_year'] as num?)?.toDouble() ?? 860.0,
      falkenmarkStressCategory: (json['falkenmark_stress_category'] as String?) ?? 'Water-Stressed (<1,000 m3/capita)',
      dataSource: (json['data_source'] as String?) ?? 'PBS 2024 Agricultural Census / Pakistan Economic Survey',
      sourceYear: (json['source_year'] as num?)?.toInt() ?? 2024,
    );
  }
}
