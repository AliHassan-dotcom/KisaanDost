import 'api_data_status.dart';
import 'pest_citation.dart';

class Advisory {
  const Advisory({
    this.crop,
    this.pest,
    this.district,
    required this.status,
    required this.sourceStatus,
    this.matched = false,
    this.reason,
    this.recommendations = const <String>[],
    this.doseGuidance,
    this.safetyNotice,
    this.citations = const <PestCitation>[],
    this.updatedAt,
  });

  final String? crop;
  final String? pest;
  final String? district;
  final ApiDataStatus status;
  final ApiDataStatus sourceStatus;
  final bool matched;
  final String? reason;
  final List<String> recommendations;
  final String? doseGuidance;
  final String? safetyNotice;
  final List<PestCitation> citations;
  final String? updatedAt;

  /// Legacy display field derived from [pest] for existing screens.
  String get topic => pest ?? crop ?? district ?? 'general';

  factory Advisory.fromJson(Map<String, dynamic> json) {
    return Advisory(
      crop: json['crop'] as String?,
      pest: json['pest'] as String?,
      district: json['district'] as String?,
      status: ApiDataStatus.fromJson(json['status'] as String?),
      sourceStatus:
          ApiDataStatus.fromJson(json['source_status'] as String?),
      matched: json['matched'] as bool? ?? false,
      reason: json['reason'] as String?,
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const <String>[],
      doseGuidance: json['dose_guidance'] as String?,
      safetyNotice: json['safety_notice'] as String?,
      citations: (json['citations'] as List<dynamic>?)
              ?.whereType<Map<String, dynamic>>()
              .map(PestCitation.fromJson)
              .toList(growable: false) ??
          const <PestCitation>[],
      updatedAt: json['updated_at'] as String?,
    );
  }
}
