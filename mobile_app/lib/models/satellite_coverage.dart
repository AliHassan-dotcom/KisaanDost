class SatelliteCoverage {
  const SatelliteCoverage({
    required this.district,
    required this.normalizedDistrict,
    required this.hasAuthoritativePolygon,
    required this.totalExpectedMonths,
    required this.monthsWithSatelliteData,
    required this.coveragePercentage,
    required this.dataStatus,
    required this.polygonSource,
    required this.notes,
  });

  final String district;
  final String normalizedDistrict;
  final bool hasAuthoritativePolygon;
  final int totalExpectedMonths;
  final int monthsWithSatelliteData;
  final String coveragePercentage;
  final String dataStatus;
  final String polygonSource;
  final String notes;

  factory SatelliteCoverage.fromJson(Map<String, dynamic> json) {
    return SatelliteCoverage(
      district: json['district'] as String,
      normalizedDistrict: json['normalized_district'] as String,
      hasAuthoritativePolygon: (json['has_authoritative_polygon'] as bool?) ?? false,
      totalExpectedMonths: (json['total_expected_months'] as num).toInt(),
      monthsWithSatelliteData: (json['months_with_satellite_data'] as num).toInt(),
      coveragePercentage: json['coverage_percentage'] as String,
      dataStatus: json['data_status'] as String,
      polygonSource: json['polygon_source'] as String,
      notes: json['notes'] as String,
    );
  }
}
