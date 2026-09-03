class AgriGdp {
  const AgriGdp({
    required this.fiscalYear,
    required this.region,
    required this.agriGdpSharePct,
    required this.agriGrowthRatePct,
    required this.cropsSubsectorSharePct,
    required this.importantCropsSharePct,
    required this.otherCropsSharePct,
    required this.livestockSubsectorSharePct,
    required this.forestrySubsectorSharePct,
    required this.fishingSubsectorSharePct,
    required this.punjabAgriValueAddSharePct,
    required this.dataSource,
  });

  final String fiscalYear;
  final String region;
  final double agriGdpSharePct;
  final double agriGrowthRatePct;
  final double cropsSubsectorSharePct;
  final double importantCropsSharePct;
  final double otherCropsSharePct;
  final double livestockSubsectorSharePct;
  final double forestrySubsectorSharePct;
  final double fishingSubsectorSharePct;
  final double punjabAgriValueAddSharePct;
  final String dataSource;

  factory AgriGdp.fromJson(Map<String, dynamic> json) {
    return AgriGdp(
      fiscalYear: (json['fiscal_year'] as String?) ?? '',
      region: (json['region'] as String?) ?? 'Pakistan',
      agriGdpSharePct: (json['agri_gdp_share_pct'] as num?)?.toDouble() ?? 0.0,
      agriGrowthRatePct: (json['agri_growth_rate_pct'] as num?)?.toDouble() ?? 0.0,
      cropsSubsectorSharePct: (json['crops_subsector_share_pct'] as num?)?.toDouble() ?? 0.0,
      importantCropsSharePct: (json['important_crops_share_pct'] as num?)?.toDouble() ?? 0.0,
      otherCropsSharePct: (json['other_crops_share_pct'] as num?)?.toDouble() ?? 0.0,
      livestockSubsectorSharePct: (json['livestock_subsector_share_pct'] as num?)?.toDouble() ?? 0.0,
      forestrySubsectorSharePct: (json['forestry_subsector_share_pct'] as num?)?.toDouble() ?? 0.0,
      fishingSubsectorSharePct: (json['fishing_subsector_share_pct'] as num?)?.toDouble() ?? 0.0,
      punjabAgriValueAddSharePct: (json['punjab_agri_value_add_share_pct'] as num?)?.toDouble() ?? 0.0,
      dataSource: (json['data_source'] as String?) ?? 'Pakistan Economic Survey',
    );
  }
}
