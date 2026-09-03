import 'package:flutter/material.dart';

class LanguageToggle extends StatelessWidget {
  const LanguageToggle({
    super.key,
    required this.language,
    required this.onChanged,
  });

  final String language;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<String>(
      segments: const <ButtonSegment<String>>[
        ButtonSegment<String>(value: 'en', label: Text('English')),
        ButtonSegment<String>(value: 'ur', label: Text('اردو')),
      ],
      selected: <String>{language},
      onSelectionChanged: (value) => onChanged(value.first),
    );
  }
}
