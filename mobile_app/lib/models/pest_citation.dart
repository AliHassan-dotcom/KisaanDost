class PestCitation {
  const PestCitation({
    required this.factId,
    required this.category,
    required this.sourcePage,
    required this.sourceSection,
    required this.sourceExcerpt,
  });

  final String factId;
  final String category;
  final int sourcePage;
  final String sourceSection;
  final String sourceExcerpt;

  factory PestCitation.fromJson(Map<String, dynamic> json) {
    return PestCitation(
      factId: json['fact_id'] as String? ?? '',
      category: json['category'] as String? ?? '',
      sourcePage: (json['source_page'] as num?)?.toInt() ?? 0,
      sourceSection: json['source_section'] as String? ?? '',
      sourceExcerpt: json['source_excerpt'] as String? ?? '',
    );
  }
}
