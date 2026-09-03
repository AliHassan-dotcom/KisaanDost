class PestSource {
  const PestSource({
    required this.title,
    required this.year,
    required this.filename,
    this.ingestionTimestamp,
    required this.pageCount,
    required this.numFacts,
    required this.numReviewQueue,
    required this.numChunks,
    required this.status,
  });

  final String title;
  final String year;
  final String filename;
  final String? ingestionTimestamp;
  final int pageCount;
  final int numFacts;
  final int numReviewQueue;
  final int numChunks;
  final String status;

  factory PestSource.fromJson(Map<String, dynamic> json) {
    return PestSource(
      title: json['title'] as String? ?? '',
      year: json['year'] as String? ?? '',
      filename: json['filename'] as String? ?? '',
      ingestionTimestamp: json['ingestion_timestamp'] as String?,
      pageCount: (json['page_count'] as num?)?.toInt() ?? 0,
      numFacts: (json['num_facts'] as num?)?.toInt() ?? 0,
      numReviewQueue: (json['num_review_queue'] as num?)?.toInt() ?? 0,
      numChunks: (json['num_chunks'] as num?)?.toInt() ?? 0,
      status: json['status'] as String? ?? 'missing',
    );
  }
}
