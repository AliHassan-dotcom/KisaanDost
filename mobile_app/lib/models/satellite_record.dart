class SatelliteRecord {
  const SatelliteRecord({
    required this.year,
    required this.month,
    required this.district,
    required this.normalizedDistrict,
    this.ndviMean,
    this.ndviMedian,
    this.ndwiMean,
    this.ndwiMedian,
    this.validPixelCount,
    this.observationCount,
    this.cloudOrQualityFraction,
    required this.satelliteSource,
    required this.productId,
    required this.spatialScaleM,
    required this.periodStart,
    required this.periodEnd,
    required this.dataStatus,
    required this.noCoverageFlag,
    required this.qualityFlag,
    required this.sourceProcessingTimestamp,
    required this.attentionStatus,
    required this.attentionEvidence,
  });

  final int year;
  final int month;
  final String district;
  final String normalizedDistrict;
  final double? ndviMean;
  final double? ndviMedian;
  final double? ndwiMean;
  final double? ndwiMedian;
  final int? validPixelCount;
  final int? observationCount;
  final double? cloudOrQualityFraction;
  final String satelliteSource;
  final String productId;
  final int spatialScaleM;
  final String periodStart;
  final String periodEnd;
  final String dataStatus;
  final bool noCoverageFlag;
  final String qualityFlag;
  final String sourceProcessingTimestamp;
  final String attentionStatus;
  final String attentionEvidence;

  String get label => '$year-${month.toString().padLeft(2, '0')}';

  bool get hasValidMetrics => ndviMean != null && ndwiMean != null;

  factory SatelliteRecord.fromJson(Map<String, dynamic> json) {
    return SatelliteRecord(
      year: (json['year'] as num).toInt(),
      month: (json['month'] as num).toInt(),
      district: json['district'] as String,
      normalizedDistrict: json['normalized_district'] as String,
      ndviMean: (json['ndvi_mean'] as num?)?.toDouble(),
      ndviMedian: (json['ndvi_median'] as num?)?.toDouble(),
      ndwiMean: (json['ndwi_mean'] as num?)?.toDouble(),
      ndwiMedian: (json['ndwi_median'] as num?)?.toDouble(),
      validPixelCount: (json['valid_pixel_count'] as num?)?.toInt(),
      observationCount: (json['observation_count'] as num?)?.toInt(),
      cloudOrQualityFraction: (json['cloud_or_quality_fraction'] as num?)?.toDouble(),
      satelliteSource: json['satellite_source'] as String,
      productId: json['product_id'] as String,
      spatialScaleM: (json['spatial_scale_m'] as num).toInt(),
      periodStart: json['period_start'] as String,
      periodEnd: json['period_end'] as String,
      dataStatus: json['data_status'] as String,
      noCoverageFlag: (json['no_coverage_flag'] as bool?) ?? false,
      qualityFlag: json['quality_flag'] as String,
      sourceProcessingTimestamp: json['source_processing_timestamp'] as String,
      attentionStatus: json['attention_status'] as String,
      attentionEvidence: json['attention_evidence'] as String,
    );
  }
}
