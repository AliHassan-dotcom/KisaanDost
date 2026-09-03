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
      backgroundColor: const Color(0xFF071D12),
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
              CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00E676))),
              SizedBox(height: 16),
              Text(
                'Analyzing Punjab pest surveillance & chemical advisory...',
                style: TextStyle(color: Colors.white70, fontSize: 13),
              ),
            ],
          ),
        ),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Icon(Icons.pest_control, size: 48, color: Color(0xFFFFA726)),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'ایڈوائزری لوڈ نہیں ہو سکی' : 'Failed to load pest advisory',
                  style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  '$error',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white60, fontSize: 12),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(pestProvider.notifier).loadAlerts(district: userDistrict),
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00E676), foregroundColor: Colors.black),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) {
          final alerts = state.alerts.where((a) {
            // Filter out corrupted rows
            if (a.pest == '.' || (a.pest.trim().length <= 1 && a.pesticideName == null)) {
              return false;
            }
            if (_selectedCropFilter == 'All') return true;
            final crop = a.crop?.toLowerCase() ?? '';
            return crop.contains(_selectedCropFilter.toLowerCase());
          }).toList();

          return RefreshIndicator(
            onRefresh: () async {
              ref.read(pestProvider.notifier).loadAlerts(district: userDistrict);
            },
            color: const Color(0xFF00E676),
            backgroundColor: const Color(0xFF0F2E1E),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  // District Header Badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F2E1E),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: Colors.green.withAlpha(50)),
                    ),
                    child: Row(
                      children: <Widget>[
                        const Icon(Icons.location_on, color: Color(0xFF00E676), size: 18),
                        const SizedBox(width: 8),
                        Text(
                          isUrdu ? 'ضلع: ${state.district} (پنجاب)' : 'District: ${state.district} (Punjab)',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                      ],
                    ),
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
                        selectedColor: const Color(0xFF00E676),
                        backgroundColor: const Color(0xFF0F2E1E),
                        labelStyle: TextStyle(
                          color: isSelected ? Colors.black : Colors.white70,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          fontSize: 12,
                        ),
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
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F2E1E),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Text(
                        'No active pest alerts for your selected filter.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white70),
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
                      isUrdu ? 'ڈیٹا کے ذرائع' : 'Data sources',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
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
    final cropName = alert.crop != null && alert.crop!.isNotEmpty ? alert.crop! : 'General';
    final pestTitle = alert.pest != '.' && alert.pest.isNotEmpty ? alert.pest : (alert.pesticideName ?? 'Pest Alert');

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F2E1E),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.green.withAlpha(50)),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Colors.black26, blurRadius: 6, offset: Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Expanded(
                child: Text(
                  '$cropName · $pestTitle',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
              ),
              StatusBadge(status: alert.status),
            ],
          ),
          if (alert.pesticideName != null || alert.activeIngredient != null) ...[
            const SizedBox(height: 10),
            if (alert.pesticideName != null && alert.pesticideName!.isNotEmpty)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text('Pesticide: ', style: TextStyle(color: Color(0xFF00E676), fontWeight: FontWeight.bold, fontSize: 12)),
                  Expanded(
                    child: Text(
                      alert.pesticideName!,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ],
              ),
            if (alert.activeIngredient != null && alert.activeIngredient!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text('Active ingredient: ', style: TextStyle(color: Colors.white70, fontSize: 11)),
                  Expanded(
                    child: Text(
                      alert.activeIngredient!,
                      style: const TextStyle(color: Colors.white, fontSize: 11),
                    ),
                  ),
                ],
              ),
            ],
          ],
          if (alert.explicitDoseText != null && alert.explicitDoseText!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF00E676).withAlpha(25),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF00E676).withAlpha(80)),
              ),
              child: Row(
                children: <Widget>[
                  const Icon(Icons.water_drop, size: 14, color: Color(0xFF00E676)),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Dose: ${alert.explicitDoseText}',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF00E676), fontSize: 11),
                    ),
                  ),
                ],
              ),
            ),
          ],
          if (alert.safetyText != null && alert.safetyText!.isNotEmpty) ...[
            const SizedBox(height: 10),
            SafetyNotice(text: alert.safetyText!),
          ],
        ],
      ),
    );
  }

  Widget _buildAdvisoryCard(BuildContext context, Advisory advisory, bool isUrdu) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0C2417),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.blue.withAlpha(80)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'Advisory: ${advisory.pest ?? advisory.crop ?? "Punjab Crop Protection"}',
            style: const TextStyle(color: Color(0xFF00E5FF), fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(height: 8),
          if (advisory.doseGuidance != null)
            Text(
              'Dose guidance: ${advisory.doseGuidance}',
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
          if (advisory.safetyNotice != null) ...[
            const SizedBox(height: 6),
            Text(advisory.safetyNotice!, style: const TextStyle(color: Colors.white70, fontSize: 11)),
          ],
          if (advisory.citations.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...advisory.citations.map((c) {
              return Text(
                c.sourceExcerpt,
                style: const TextStyle(fontSize: 11, color: Colors.white60),
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildSourceCard(BuildContext context, PestSource source) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0F2E1E),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white12),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.picture_as_pdf, color: Colors.redAccent, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  source.title,
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                ),
                Text(
                  '${source.year} · ${source.filename}',
                  style: const TextStyle(color: Colors.white60, fontSize: 10),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
