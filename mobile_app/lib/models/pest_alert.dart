import 'api_data_status.dart';

class PestAlert {
  const PestAlert({
    required this.id,
    required this.crop,
    required this.pest,
    required this.status,
    this.category,
    this.district,
    this.dateOrPeriod,
    this.advisoryText,
    this.pesticideName,
    this.activeIngredient,
    this.formulation,
    this.explicitDoseText,
    this.safetyText,
    this.qualityControlStatus,
    this.sourcePage = 0,
    this.sourceSection,
    this.sourceExcerpt,
    this.confidence = 0.0,
    this.reviewed = false,
    this.severity,
    this.reason,
    this.recommendations = const <String>[],
    this.updatedAt,
  });

  final String id;
  final String? crop;
  final String pest;
  final ApiDataStatus status;
  final String? category;
  final String? district;
  final String? dateOrPeriod;
  final String? advisoryText;
  final String? pesticideName;
  final String? activeIngredient;
  final String? formulation;
  final String? explicitDoseText;
  final String? safetyText;
  final String? qualityControlStatus;
  final int sourcePage;
  final String? sourceSection;
  final String? sourceExcerpt;
  final double confidence;
  final bool reviewed;
  final String? severity;
  final String? reason;
  final List<String> recommendations;
  final String? updatedAt;

  factory PestAlert.fromJson(Map<String, dynamic> json) {
    return PestAlert(
      id: json['fact_id'] as String? ??
          json['id'] as String? ??
          json['scan_id'] as String? ??
          '',
      crop: json['crop'] as String? ?? 'general',
      pest: json['pest_or_disease'] as String? ??
          json['pest'] as String? ??
          'general',
      status: ApiDataStatus.fromJson(json['source_status'] as String? ??
          json['status'] as String?),
      category: json['category'] as String?,
      district: json['district'] as String?,
      dateOrPeriod: json['date_or_period'] as String?,
      advisoryText: json['advisory_text'] as String?,
      pesticideName: json['pesticide_name'] as String?,
      activeIngredient: json['active_ingredient'] as String?,
      formulation: json['formulation'] as String?,
      explicitDoseText: json['explicit_dose_text'] as String?,
      safetyText: json['safety_text'] as String?,
      qualityControlStatus: json['quality_control_status'] as String?,
      sourcePage: (json['source_page'] as num?)?.toInt() ?? 0,
      sourceSection: json['source_section'] as String?,
      sourceExcerpt: json['source_excerpt'] as String?,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      reviewed: json['reviewed'] as bool? ?? false,
      severity: json['severity'] as String?,
      reason: json['reason'] as String?,
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const <String>[],
      updatedAt: json['updated_at'] as String?,
    );
  }
}
