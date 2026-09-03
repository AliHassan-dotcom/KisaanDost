import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/profile_provider.dart';
import '../widgets/kd_app_bar.dart';

class IrrigationScreen extends ConsumerWidget {
  const IrrigationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(profileProvider);

    return Scaffold(
      appBar: const KdAppBar(title: 'Irrigation Advisory'),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Error: $error')),
        data: (profile) {
          final recommendations = <String>[
            'Monitor soil moisture regularly.',
            'Irrigate early morning or late evening to reduce evaporation.',
          ];

          if (profile.irrigationType != null) {
            recommendations.add(
              'Current irrigation type: ${profile.irrigationType}.',
            );
          }
          if (profile.crop != null) {
            recommendations.add(
              'Plan irrigation schedule based on ${profile.crop} growth stage.',
            );
          }

          return Padding(
            padding: const EdgeInsets.all(16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Advisory',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    ...recommendations.map(
                      (r) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            const Text('• '),
                            Expanded(child: Text(r)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
