import 'package:flutter/material.dart';

class GreetingHeader extends StatelessWidget {
  const GreetingHeader({super.key, this.name, this.district, this.crop});

  final String? name;
  final String? district;
  final String? crop;

  String get _greeting {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          '$_greeting, ${name ?? 'Farmer'}',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        if (district != null || crop != null)
          Text(
            '${district ?? ''}${district != null && crop != null ? ' · ' : ''}${crop ?? ''}',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
      ],
    );
  }
}
