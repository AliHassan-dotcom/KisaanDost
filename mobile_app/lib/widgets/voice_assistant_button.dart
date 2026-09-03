import 'package:flutter/material.dart';

class VoiceAssistantButton extends StatelessWidget {
  const VoiceAssistantButton({super.key, this.onPressed});

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton.extended(
      onPressed: onPressed,
      icon: const Icon(Icons.mic),
      label: const Text('Ask Kisaan Dost'),
    );
  }
}
