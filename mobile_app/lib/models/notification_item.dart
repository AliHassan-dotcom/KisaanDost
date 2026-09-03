class NotificationItem {
  const NotificationItem({
    required this.id,
    required this.userId,
    required this.type,
    required this.title,
    required this.titleUr,
    required this.message,
    required this.messageUr,
    required this.severity,
    required this.createdAtUtc,
    required this.isRead,
    required this.sourceAttribution,
    this.metadata = const <String, dynamic>{},
  });

  final String id;
  final String userId;
  final String type; // "weather_alert", "market_mover", "advisory_reminder"
  final String title;
  final String titleUr;
  final String message;
  final String messageUr;
  final String severity; // "info", "warning", "critical"
  final String createdAtUtc;
  final bool isRead;
  final String sourceAttribution;
  final Map<String, dynamic> metadata;

  NotificationItem copyWith({
    String? id,
    String? userId,
    String? type,
    String? title,
    String? titleUr,
    String? message,
    String? messageUr,
    String? severity,
    String? createdAtUtc,
    bool? isRead,
    String? sourceAttribution,
    Map<String, dynamic>? metadata,
  }) {
    return NotificationItem(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      type: type ?? this.type,
      title: title ?? this.title,
      titleUr: titleUr ?? this.titleUr,
      message: message ?? this.message,
      messageUr: messageUr ?? this.messageUr,
      severity: severity ?? this.severity,
      createdAtUtc: createdAtUtc ?? this.createdAtUtc,
      isRead: isRead ?? this.isRead,
      sourceAttribution: sourceAttribution ?? this.sourceAttribution,
      metadata: metadata ?? this.metadata,
    );
  }

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    return NotificationItem(
      id: (json['id'] as String?) ?? '',
      userId: (json['user_id'] as String?) ?? 'default_farmer',
      type: (json['type'] as String?) ?? 'advisory_reminder',
      title: (json['title'] as String?) ?? '',
      titleUr: (json['title_ur'] as String?) ?? '',
      message: (json['message'] as String?) ?? '',
      messageUr: (json['message_ur'] as String?) ?? '',
      severity: (json['severity'] as String?) ?? 'info',
      createdAtUtc: (json['created_at_utc'] as String?) ?? '',
      isRead: (json['is_read'] as bool?) ?? false,
      sourceAttribution: (json['source_attribution'] as String?) ?? 'Official Public Source',
      metadata: (json['metadata'] as Map<String, dynamic>?) ?? const <String, dynamic>{},
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'user_id': userId,
      'type': type,
      'title': title,
      'title_ur': titleUr,
      'message': message,
      'message_ur': messageUr,
      'severity': severity,
      'created_at_utc': createdAtUtc,
      'is_read': isRead,
      'source_attribution': sourceAttribution,
      'metadata': metadata,
    };
  }
}
