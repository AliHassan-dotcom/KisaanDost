/// Represents a message in the Voice Assistant conversation transcript.
class VoiceChatMessage {
  const VoiceChatMessage({
    required this.id,
    required this.sender,
    required this.text,
    required this.timestamp,
    this.isStreaming = false,
  });

  final String id;
  final String sender; // 'user' or 'assistant'
  final String text;
  final DateTime timestamp;
  final bool isStreaming;

  bool get isUser => sender == 'user';
  bool get isAssistant => sender == 'assistant';

  VoiceChatMessage copyWith({
    String? id,
    String? sender,
    String? text,
    DateTime? timestamp,
    bool? isStreaming,
  }) {
    return VoiceChatMessage(
      id: id ?? this.id,
      sender: sender ?? this.sender,
      text: text ?? this.text,
      timestamp: timestamp ?? this.timestamp,
      isStreaming: isStreaming ?? this.isStreaming,
    );
  }
}
