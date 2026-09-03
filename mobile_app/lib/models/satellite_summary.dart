import 'api_data_status.dart';

class SatelliteSummary {
  const SatelliteSummary({
    required this.district,
    required this.crop,
    required this.status,
    this.normalizedDistrict,
    this.reason,
    this.ndvi,
    this.ndwi,
    this.ndviMedian,
    this.ndwiMedian,
    this.cloudCoverPercent,
    this.validPixelCount,
    this.observationCount,
    this.satelliteSource,
    this.productId,
    this.spatialScaleM,
    this.periodStart,
    this.periodEnd,
    this.lastClearScene,
    this.healthTrend = 'normal_observation',
    this.attentionEvidence,
    this.noCoverageFlag = false,
    this.qualityFlag,
    this.updatedAt,
  });

  final String district;
  final String? normalizedDistrict;
  final String crop;
  final ApiDataStatus status;
  final String? reason;
  final double? ndvi;
  final double? ndwi;
  final double? ndviMedian;
  final double? ndwiMedian;
  final double? cloudCoverPercent;
  final int? validPixelCount;
  final int? observationCount;
  final String? satelliteSource;
  final String? productId;
  final int? spatialScaleM;
  final String? periodStart;
  final String? periodEnd;
  final String? lastClearScene;
  final String healthTrend;
  final String? attentionEvidence;
  final bool noCoverageFlag;
  final String? qualityFlag;
  final String? updatedAt;

  bool get isBoundaryUnavailable =>
      healthTrend == 'boundary_unavailable' ||
      reason == 'missing_authoritative_arcgis_polygon';

  bool get isCloudMasked =>
      healthTrend == 'insufficient_satellite_data' ||
      reason == 'cloud_masked_no_valid_pixels';

  factory SatelliteSummary.fromJson(Map<String, dynamic> json) {
    return SatelliteSummary(
      district: (json['district'] as String?) ?? 'Lahore',
      normalizedDistrict: json['normalized_district'] as String?,
      crop: (json['crop'] as String?) ?? 'wheat',
      status: ApiDataStatus.fromJson(json['status'] as String? ?? json['data_status'] as String?),
      reason: json['reason'] as String? ?? json['quality_flag'] as String?,
      ndvi: (json['ndvi'] as num?)?.toDouble() ?? (json['ndvi_mean'] as num?)?.toDouble(),
      ndwi: (json['ndwi'] as num?)?.toDouble() ?? (json['ndwi_mean'] as num?)?.toDouble(),
      ndviMedian: (json['ndvi_median'] as num?)?.toDouble(),
      ndwiMedian: (json['ndwi_median'] as num?)?.toDouble(),
      cloudCoverPercent: (json['cloud_cover_percent'] as num?)?.toDouble() ??
          ((json['cloud_or_quality_fraction'] as num?)?.toDouble() != null
              ? (json['cloud_or_quality_fraction'] as num).toDouble() * 100
              : null),
      validPixelCount: (json['valid_pixel_count'] as num?)?.toInt(),
      observationCount: (json['observation_count'] as num?)?.toInt(),
      satelliteSource: json['satellite_source'] as String?,
      productId: json['product_id'] as String?,
      spatialScaleM: (json['spatial_scale_m'] as num?)?.toInt(),
      periodStart: json['period_start'] as String?,
      periodEnd: json['period_end'] as String?,
      lastClearScene: json['last_clear_scene'] as String? ?? json['period_end'] as String?,
      healthTrend: json['health_trend'] as String? ?? json['attention_status'] as String? ?? 'normal_observation',
      attentionEvidence: json['attention_evidence'] as String?,
      noCoverageFlag: (json['no_coverage_flag'] as bool?) ?? false,
      qualityFlag: json['quality_flag'] as String?,
      updatedAt: json['updated_at'] as String? ?? json['source_processing_timestamp'] as String?,
    );
  }
}
