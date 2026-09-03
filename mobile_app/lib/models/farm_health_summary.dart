class FarmHealthSummary {
  const FarmHealthSummary({
    this.status,
    this.confidence,
    this.uncertain = false,
    this.modelVersion,
    this.lastScannedAt,
  });

  final String? status;
  final double? confidence;
  final bool uncertain;
  final String? modelVersion;
  final String? lastScannedAt;

  factory FarmHealthSummary.fromJson(Map<String, dynamic> json) {
    return FarmHealthSummary(
      status: json['status'] as String?,
      confidence: (json['confidence'] as num?)?.toDouble(),
      uncertain: json['uncertain'] as bool? ?? false,
      modelVersion: json['model_version'] as String?,
      lastScannedAt: json['last_scanned_at'] as String?,
    );
  }
}
