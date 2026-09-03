import 'api_data_status.dart';

class DiseasePrediction {
  const DiseasePrediction({
    required this.scanId,
    required this.predictedClass,
    required this.confidence,
    required this.modelVersion,
    this.uncertain = false,
    this.warning,
    this.status = ApiDataStatus.live,
    this.createdAt,
  });

  final String scanId;
  final String predictedClass;
  final double confidence;
  final String modelVersion;
  final bool uncertain;
  final String? warning;
  final ApiDataStatus status;
  final String? createdAt;

  factory DiseasePrediction.fromJson(Map<String, dynamic> json) {
    final data = json['data'] as Map<String, dynamic>? ?? json;
    final rawStatus = data['status'] as String?;
    return DiseasePrediction(
      scanId: data['scan_id'] as String? ?? '',
      predictedClass: data['predicted_class'] as String? ?? 'unknown',
      confidence: (data['confidence'] as num?)?.toDouble() ?? 0.0,
      modelVersion: data['model_version'] as String? ?? 'unknown',
      uncertain: data['uncertain'] as bool? ?? false,
      warning: data['warning'] as String?,
      status: rawStatus != null
          ? ApiDataStatus.fromJson(rawStatus)
          : (data['predicted_class'] != null && data['predicted_class'] != 'unknown'
              ? ApiDataStatus.live
              : ApiDataStatus.unavailable),
      createdAt: (data['created_at'] ?? data['scanned_at']) as String?,
    );
  }
}
