class LandUtilization {
  const LandUtilization({
    required this.district,
    required this.totalFarmAreaAcres,
    required this.cultivatedAreaAcres,
    required this.uncultivatedAreaAcres,
    required this.totalCroppedAreaAcres,
    required this.cultivatedSharePct,
    required this.croppingIntensityPct,
    required this.wheatAreaAcres,
    required this.wheatSharePct,
    required this.riceAreaAcres,
    required this.riceSharePct,
    required this.cottonAreaAcres,
    required this.cottonSharePct,
    required this.sugarcaneAreaAcres,
    required this.sugarcaneSharePct,
    required this.maizeAreaAcres,
    required this.maizeSharePct,
    required this.fodderAreaAcres,
    required this.fodderSharePct,
    required this.orchardAreaAcres,
    required this.orchardSharePct,
    required this.kharifTotalAcres,
    required this.rabiTotalAcres,
    required this.dataSource,
    required this.sourceYear,
  });

  final String district;
  final double totalFarmAreaAcres;
  final double cultivatedAreaAcres;
  final double uncultivatedAreaAcres;
  final double totalCroppedAreaAcres;
  final double cultivatedSharePct;
  final double croppingIntensityPct;
  final double wheatAreaAcres;
  final double wheatSharePct;
  final double riceAreaAcres;
  final double riceSharePct;
  final double cottonAreaAcres;
  final double cottonSharePct;
  final double sugarcaneAreaAcres;
  final double sugarcaneSharePct;
  final double maizeAreaAcres;
  final double maizeSharePct;
  final double fodderAreaAcres;
  final double fodderSharePct;
  final double orchardAreaAcres;
  final double orchardSharePct;
  final double kharifTotalAcres;
  final double rabiTotalAcres;
  final String dataSource;
  final int sourceYear;

  factory LandUtilization.fromJson(Map<String, dynamic> json) {
    return LandUtilization(
      district: (json['district'] as String?) ?? '',
      totalFarmAreaAcres: (json['total_farm_area_acres'] as num?)?.toDouble() ?? 0.0,
      cultivatedAreaAcres: (json['cultivated_area_acres'] as num?)?.toDouble() ?? 0.0,
      uncultivatedAreaAcres: (json['uncultivated_area_acres'] as num?)?.toDouble() ?? 0.0,
      totalCroppedAreaAcres: (json['total_cropped_area_acres'] as num?)?.toDouble() ?? 0.0,
      cultivatedSharePct: (json['cultivated_share_pct'] as num?)?.toDouble() ?? 0.0,
      croppingIntensityPct: (json['cropping_intensity_pct'] as num?)?.toDouble() ?? 0.0,
      wheatAreaAcres: (json['wheat_area_acres'] as num?)?.toDouble() ?? 0.0,
      wheatSharePct: (json['wheat_share_pct'] as num?)?.toDouble() ?? 0.0,
      riceAreaAcres: (json['rice_area_acres'] as num?)?.toDouble() ?? 0.0,
      riceSharePct: (json['rice_share_pct'] as num?)?.toDouble() ?? 0.0,
      cottonAreaAcres: (json['cotton_area_acres'] as num?)?.toDouble() ?? 0.0,
      cottonSharePct: (json['cotton_share_pct'] as num?)?.toDouble() ?? 0.0,
      sugarcaneAreaAcres: (json['sugarcane_area_acres'] as num?)?.toDouble() ?? 0.0,
      sugarcaneSharePct: (json['sugarcane_share_pct'] as num?)?.toDouble() ?? 0.0,
      maizeAreaAcres: (json['maize_area_acres'] as num?)?.toDouble() ?? 0.0,
      maizeSharePct: (json['maize_share_pct'] as num?)?.toDouble() ?? 0.0,
      fodderAreaAcres: (json['fodder_area_acres'] as num?)?.toDouble() ?? 0.0,
      fodderSharePct: (json['fodder_share_pct'] as num?)?.toDouble() ?? 0.0,
      orchardAreaAcres: (json['orchard_area_acres'] as num?)?.toDouble() ?? 0.0,
      orchardSharePct: (json['orchard_share_pct'] as num?)?.toDouble() ?? 0.0,
      kharifTotalAcres: (json['kharif_total_acres'] as num?)?.toDouble() ?? 0.0,
      rabiTotalAcres: (json['rabi_total_acres'] as num?)?.toDouble() ?? 0.0,
      dataSource: (json['data_source'] as String?) ?? 'PBS 2024 Agricultural Census',
      sourceYear: (json['source_year'] as num?)?.toInt() ?? 2024,
    );
  }
}
