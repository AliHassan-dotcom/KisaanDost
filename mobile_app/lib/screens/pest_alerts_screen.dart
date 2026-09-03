import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/advisory.dart';
import '../models/pest_alert.dart';
import '../models/pest_source.dart';
import '../providers/pest_provider.dart';
import '../providers/profile_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/safety_notice.dart';
import '../widgets/status_badge.dart';

class PestAlertsScreen extends ConsumerStatefulWidget {
  const PestAlertsScreen({super.key});

  @override
  ConsumerState<PestAlertsScreen> createState() => _PestAlertsScreenState();
}

class _PestAlertsScreenState extends ConsumerState<PestAlertsScreen> {
  String _selectedCropFilter = 'All';

  final List<String> _crops = const <String>[
    'All',
    'Wheat',
    'Cotton',
    'Rice',
    'Sugarcane',
    'Maize',
    'Vegetables',
  ];

  @override
  Widget build(BuildContext context) {
    final pestAsync = ref.watch(pestProvider);
    final profileAsync = ref.watch(profileProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    final userDistrict = profileAsync.value?.district ?? 'Lahore';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'کیڑے مار ادویات و ایڈوائزری' : 'Pest Alerts',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(pestProvider.notifier).loadAlerts(district: userDistrict);
            },
          ),
        ],
      ),
      body: pestAsync.when(
        loading: () => const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Analyzing Punjab pest surveillance & chemical advisory...'),
            ],
          ),
        ),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Icon(Icons.pest_control, size: 48, color: Colors.orange),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'ایڈوائزری لوڈ نہیں ہو سکی' : 'Failed to load pest advisory',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  '$error',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(pestProvider.notifier).loadAlerts(district: userDistrict),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) {
          final alerts = state.alerts.where((a) {
            if (_selectedCropFilter == 'All') return true;
            final crop = a.crop?.toLowerCase() ?? '';
            return crop.contains(_selectedCropFilter.toLowerCase());
          }).toList();

          return RefreshIndicator(
            onRefresh: () async {
              ref.read(pestProvider.notifier).loadAlerts(district: userDistrict);
            },
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  // District Header
                  Row(
                    children: <Widget>[
                      Icon(Icons.location_on, color: Theme.of(context).colorScheme.primary),
                      const SizedBox(width: 8),
                      Text(
                        'District: ${state.district}',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Crop Filter Chips
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: _crops.map((c) {
                      final isSelected = _selectedCropFilter == c;
                      return ChoiceChip(
                        label: Text(c),
                        selected: isSelected,
                        onSelected: (val) {
                          if (val) {
                            setState(() => _selectedCropFilter = c);
                          }
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),

                  // Advisory & Alert Cards
                  if (alerts.isEmpty && state.advisory == null)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          'No active pest alerts for your district. Reports will appear here once the pesticide data is ingested.',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    )
                  else ...[
                    ...alerts.map((alert) => _buildAlertCard(context, alert, isUrdu)),
                    if (state.advisory != null)
                      _buildAdvisoryCard(context, state.advisory!, isUrdu),
                  ],

                  if (state.sources.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    Text(
                      'Data sources',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    ...state.sources.map((s) => _buildSourceCard(context, s)),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildAlertCard(BuildContext context, PestAlert alert, bool isUrdu) {
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.deepOrange.shade100),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Expanded(
                  child: Text(
                    '${alert.crop ?? "General"} · ${alert.pest}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                StatusBadge(status: alert.status),
              ],
            ),
            if (alert.pesticideName != null || alert.activeIngredient != null) ...[
              const SizedBox(height: 8),
              if (alert.pesticideName != null)
                Text('Pesticide: ${alert.pesticideName}', style: const TextStyle(fontWeight: FontWeight.bold)),
              if (alert.activeIngredient != null)
                Text('Active ingredient: ${alert.activeIngredient}'),
            ],
            if (alert.explicitDoseText != null) ...[
              const SizedBox(height: 6),
              Text(
                'Dose: ${alert.explicitDoseText}',
                style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green),
              ),
            ],
            if (alert.safetyText != null && alert.safetyText!.isNotEmpty) ...[
              const SizedBox(height: 8),
              SafetyNotice(text: alert.safetyText!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAdvisoryCard(BuildContext context, Advisory advisory, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.blue.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Advisory: ${advisory.pest ?? advisory.crop ?? "General"}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            if (advisory.doseGuidance != null)
              Text('Dose guidance: ${advisory.doseGuidance}'),
            if (advisory.safetyNotice != null) ...[
              const SizedBox(height: 6),
              Text(advisory.safetyNotice!),
            ],
            if (advisory.citations.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...advisory.citations.map((c) {
                return Text(
                  c.sourceExcerpt,
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSourceCard(BuildContext context, PestSource source) {
    return Card(
      elevation: 1,
      child: ListTile(
        leading: const Icon(Icons.picture_as_pdf, color: Colors.red),
        title: Text(source.title),
        subtitle: Text('${source.year} · ${source.filename}'),
      ),
    );
  }
}
