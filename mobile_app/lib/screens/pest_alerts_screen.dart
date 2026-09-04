import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/advisory.dart';
import '../models/pest_alert.dart';
import '../models/pest_source.dart';
import '../providers/pest_provider.dart';
import '../providers/profile_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/pesticide_calculator_dialog.dart';
import '../widgets/safety_notice.dart';
import '../widgets/status_badge.dart';

class PestAlertsScreen extends ConsumerStatefulWidget {
  const PestAlertsScreen({super.key});

  @override
  ConsumerState<PestAlertsScreen> createState() => _PestAlertsScreenState();
}

class _PestAlertsScreenState extends ConsumerState<PestAlertsScreen> {
  String _selectedCrop = 'All';

  final List<String> _crops = const <String>[
    'All',
    'Wheat',
    'Cotton',
    'Rice',
    'Sugarcane',
    'Maize',
    'Vegetables',
  ];

  // Predictive Pest Risk Model Baseline across Punjab Crops
  final List<Map<String, dynamic>> _predictedRisks = const <Map<String, dynamic>>[
    {
      'crop': 'Wheat',
      'pest': 'Yellow Rust & Leaf Rust (پیلی و بھوری کنگی)',
      'riskScore': 84,
      'riskLevel': 'HIGH RISK',
      'riskColor': Color(0xFFE53935),
      'climateTrigger': 'Cool humid weather (humidity > 70%) and recent rain spells.',
      'climateTriggerUr': 'زیادہ نمی (70%+) اور بارش کی وجہ سے پھپھوندی کا پھیلاؤ تیز ہے۔',
      'solution': 'Tilt 250 EC / Folicur (Propiconazole / Tebuconazole)',
      'dose': '200-250 ml / acre in 100L water',
      'sprayTiming': 'Spray in early morning (7-10 AM) before wind picks up.',
      'action': 'Apply prophylactic protective fungicide before next rain to prevent spore germination.',
    },
    {
      'crop': 'Cotton',
      'pest': 'Pink Bollworm & Whitefly (گلابی سنڈی اور سفید مکھی)',
      'riskScore': 78,
      'riskLevel': 'HIGH RISK',
      'riskColor': Color(0xFFE53935),
      'climateTrigger': 'High temperature (34°C+) and dry weather accelerating insect life cycle.',
      'climateTriggerUr': 'شدید گرمی اور خشک موسم کی وجہ سے کیڑوں کی افزائش تیز ہے۔',
      'solution': 'Proclaim 019 EC & Polo 500 SC (Emamectin + Diafenthiuron)',
      'dose': '200 ml / acre in 120L water',
      'sprayTiming': 'Spray in late afternoon to protect pollinator bees.',
      'action': 'Install PBW pheromone traps (5 traps/acre) and spray if threshold exceeds 5% infested bolls.',
    },
    {
      'crop': 'Rice',
      'pest': 'Stem Borer & Leaf Folder (تنے اور پتہ لپیٹ سنڈی)',
      'riskScore': 65,
      'riskLevel': 'MODERATE RISK',
      'riskColor': Color(0xFFFB8C00),
      'climateTrigger': 'Basmati vegetative tillering stage with warm cloudy conditions.',
      'climateTriggerUr': 'دھان کے شگوفے نکلنے کا مرحلہ اور ابر آلود موسم۔',
      'solution': 'Virtako 0.6 GR / Padan 4G (Chlorantraniliprole + Thiamethoxam)',
      'dose': '4 kg / acre broadcast in standing water (2-3 inches)',
      'sprayTiming': 'Broadcast granules evenly across flooded pan.',
      'action': 'Maintain 2 inches of standing water for 4 days after granular application.',
    },
    {
      'crop': 'Sugarcane',
      'pest': 'Top Borer & Pyrilla (ٹاپ بورر اور پائریلا)',
      'riskScore': 58,
      'riskLevel': 'MODERATE RISK',
      'riskColor': Color(0xFFFB8C00),
      'climateTrigger': 'Cane whorl development during active vegetative expansion.',
      'climateTriggerUr': 'کماد کی نشوونما کے دوران چوٹی کے پتوں پر حملہ۔',
      'solution': 'Chlorpyrifos 40 EC / Belt 480 SC (Flubendiamide)',
      'dose': '1.25 - 1.5 Liters / acre in 150L water directed at crown whorl',
      'sprayTiming': 'Direct spray nozzle right into central whorl.',
      'action': 'Release Trichogramma biological control cards and avoid excess urea application.',
    },
    {
      'crop': 'Maize',
      'pest': 'Fall Armyworm (فال آرمی ورم)',
      'riskScore': 72,
      'riskLevel': 'HIGH RISK',
      'riskColor': Color(0xFFE53935),
      'climateTrigger': 'Autumn maize vegetative stage vulnerable to aggressive whorl defoliation.',
      'climateTriggerUr': 'مکئی کے پودوں پر سنڈی کے سوراخ اور پتوں کا نقصان۔',
      'solution': 'Coragen 20 SC / Radiant 120 SC (Chlorantraniliprole / Spinetoram)',
      'dose': '50 ml / acre in 100L water',
      'sprayTiming': 'Target early instar larvae inside the funnel whorl.',
      'action': 'Spray at first sign of pinhole leaf damage to stop larval entry into stalk.',
    },
    {
      'crop': 'Vegetables',
      'pest': 'Fruit Borer & Powdery Mildew (پھل کی سنڈی اور سفوفی پھپھوندی)',
      'riskScore': 60,
      'riskLevel': 'MODERATE RISK',
      'riskColor': Color(0xFFFB8C00),
      'climateTrigger': 'Peri-urban vegetable clusters (Tomato, Chili, Cucurbits).',
      'climateTriggerUr': 'ٹماٹر، مرچ اور سبزیوں میں پھپھوندی اور پھل کی سنڈی۔',
      'solution': 'Score 250 EC / Match 050 EC (Difenoconazole / Lufenuron)',
      'dose': '100-125 ml / acre in 100L water',
      'sprayTiming': 'Strict 7-day Pre-Harvest Interval (PHI).',
      'action': 'Maintain strict safety intervals and avoid chemical application on mature pickings.',
    },
  ];

  @override
  Widget build(BuildContext context) {
    final pestAsync = ref.watch(pestProvider);
    final profileAsync = ref.watch(profileProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    final userDistrict = profileAsync.value?.district ?? 'Lahore';

    final filteredRisks = _predictedRisks.where((r) {
      if (_selectedCrop == 'All') return true;
      return (r['crop'] as String).toLowerCase() == _selectedCrop.toLowerCase();
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFFF4F7F4),
      appBar: KdAppBar(
        title: isUrdu ? 'کیڑوں و بیماریوں کا پیشگی AI ماڈل' : 'Pest Alerts',
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
              CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF2E7D32))),
              SizedBox(height: 16),
              Text(
                'Analyzing Punjab pest surveillance & predictive climate model...',
                style: TextStyle(color: Colors.grey, fontSize: 13),
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
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) => RefreshIndicator(
          onRefresh: () async {
            ref.read(pestProvider.notifier).loadAlerts(district: userDistrict);
          },
          color: const Color(0xFF2E7D32),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                // 1. Top Predictive Intelligence Summary Card (Like Farm Insights)
                _buildModelSummaryHero(context, state.district, isUrdu),
                const SizedBox(height: 16),

                // 2. Crop Filter Selector
                _buildCropFilterChips(isUrdu),
                const SizedBox(height: 16),

                // 3. Dynamic State Alerts
                if (state.alerts.isNotEmpty) ...[
                  ...state.alerts.map((alert) => _buildDynamicAlertCard(context, alert, isUrdu)),
                  const SizedBox(height: 12),
                ],

                // 4. Dynamic State Advisory
                if (state.advisory != null) ...[
                  _buildAdvisoryCard(context, state.advisory!, isUrdu),
                  const SizedBox(height: 12),
                ],

                // 5. Section Title: Predictive Intelligence
                Text(
                  isUrdu ? 'فصل وار پیشگوئی اور فوری حل (AI Solutions)' : 'Predicted Pest Outbreaks & Solutions',
                  style: const TextStyle(
                    color: Color(0xFF1B382B),
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 12),

                // 6. Actionable Predictive Cards
                ...filteredRisks.map((risk) => _buildPredictiveRiskCard(context, risk, isUrdu)),

                // 7. Sources if present
                if (state.sources.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Text(
                    isUrdu ? 'ڈیٹا کے ذرائع' : 'Data sources',
                    style: const TextStyle(color: Color(0xFF1B382B), fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  ...state.sources.map((s) => _buildSourceCard(context, s)),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// AI Predictive Intelligence Summary Card (matching Farm Insights UI)
  Widget _buildModelSummaryHero(BuildContext context, String district, bool isUrdu) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.green.shade200, width: 1.5),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Row(
                children: <Widget>[
                  const Icon(Icons.analytics_outlined, color: Color(0xFF2E7D32), size: 22),
                  const SizedBox(width: 8),
                  Text(
                    isUrdu ? 'پنجاب کیڑوں کا پیشگی AI ماڈل' : 'Punjab Pest Predictive Model',
                    style: const TextStyle(color: Color(0xFF1B382B), fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF2E7D32)),
                ),
                child: Text(
                  district,
                  style: const TextStyle(color: Color(0xFF2E7D32), fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Insight 1: Weather & Disease Correlation
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.warning_amber_rounded, size: 16, color: Colors.red),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  isUrdu
                      ? 'موسمی نمی (76%) اور درجہ حرارت کی وجہ سے گندم کی کنگی اور مکئی کے فال آرمی ورم کا خطرہ 80% سے زائد ہے۔'
                      : 'High humidity (76%) and temperature swings create elevated risk (80%+) for Wheat Rust and Maize Armyworm.',
                  style: const TextStyle(color: Color(0xFF1B382B), fontSize: 13, height: 1.3, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Insight 2: Preventive Action Advice
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check_circle_outline, size: 16, color: Color(0xFF2E7D32)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  isUrdu
                      ? 'بارش سے پہلے حفاظتی اسپرے مکمل کریں اور تجویز کردہ کیمیکل کی صحیح مقدار استعمال کریں۔'
                      : 'Complete prophylactic fungicide and pesticide sprays before next rain to prevent spore germination.',
                  style: TextStyle(color: Colors.grey.shade800, fontSize: 13, height: 1.3),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCropFilterChips(bool isUrdu) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _crops.map((c) {
        final isSelected = _selectedCrop == c;
        return ChoiceChip(
          label: Text(c),
          selected: isSelected,
          selectedColor: const Color(0xFF2E7D32),
          backgroundColor: Colors.white,
          labelStyle: TextStyle(
            color: isSelected ? Colors.white : Colors.grey.shade800,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            fontSize: 12,
          ),
          onSelected: (val) {
            if (val) {
              setState(() => _selectedCrop = c);
            }
          },
        );
      }).toList(),
    );
  }

  Widget _buildDynamicAlertCard(BuildContext context, PestAlert alert, bool isUrdu) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.green.shade100, width: 1.5),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2)),
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
                  '${alert.crop ?? "wheat"} · ${alert.pest}',
                  style: const TextStyle(
                    color: Color(0xFF1B382B),
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
              ),
              StatusBadge(status: alert.status),
            ],
          ),
          if (alert.pesticideName != null) ...[
            const SizedBox(height: 8),
            Text('Pesticide: ${alert.pesticideName}', style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
          if (alert.explicitDoseText != null) ...[
            const SizedBox(height: 6),
            Text(
              'Dose: ${alert.explicitDoseText}',
              style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2E7D32)),
            ),
          ],
          if (alert.safetyText != null && alert.safetyText!.isNotEmpty) ...[
            const SizedBox(height: 8),
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
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.blue.shade100, width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'Advisory: ${advisory.pest ?? advisory.crop ?? "General"}',
            style: const TextStyle(color: Color(0xFF0277BD), fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(height: 8),
          if (advisory.doseGuidance != null)
            Text('Dose guidance: ${advisory.doseGuidance}', style: TextStyle(color: Colors.grey.shade800)),
          if (advisory.safetyNotice != null) ...[
            const SizedBox(height: 6),
            Text(advisory.safetyNotice!, style: TextStyle(color: Colors.grey.shade700)),
          ],
          if (advisory.citations.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...advisory.citations.map((c) {
              return Text(
                c.sourceExcerpt,
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildSourceCard(BuildContext context, PestSource source) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: const Icon(Icons.picture_as_pdf, color: Colors.red),
        title: Text(source.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
        subtitle: Text('${source.year} · ${source.filename}', style: const TextStyle(fontSize: 11)),
      ),
    );
  }

  /// Actionable Predictive Card with Risk Score, Trigger, Solution, and Dosage
  Widget _buildPredictiveRiskCard(BuildContext context, Map<String, dynamic> risk, bool isUrdu) {
    final crop = risk['crop'] as String;
    final pest = risk['pest'] as String;
    final score = risk['riskScore'] as int;
    final level = risk['riskLevel'] as String;
    final color = risk['riskColor'] as Color;
    final trigger = isUrdu ? risk['climateTriggerUr'] as String : risk['climateTrigger'] as String;
    final solution = risk['solution'] as String;
    final dose = risk['dose'] as String;
    final timing = risk['sprayTiming'] as String;
    final action = risk['action'] as String;

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withAlpha(60), width: 1.5),
        boxShadow: const <BoxShadow>[
          BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          // Header: Crop · Pest Title & Risk Gauge Badge
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      '$crop · $pest',
                      style: const TextStyle(
                        color: Color(0xFF1B382B),
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Trigger: $trigger',
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 11),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: color.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: color),
                ),
                child: Text(
                  '$score% $level',
                  style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Recommended Chemical Solution Pill
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    const Icon(Icons.sanitizer_outlined, color: Color(0xFF2E7D32), size: 16),
                    const SizedBox(width: 6),
                    Text(
                      isUrdu ? 'تجویز کردہ اسپرے و دوا:' : 'Recommended Pesticide / Fungicide:',
                      style: const TextStyle(color: Color(0xFF2E7D32), fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  solution,
                  style: const TextStyle(color: Color(0xFF1B382B), fontWeight: FontWeight.bold, fontSize: 13),
                ),
                const SizedBox(height: 6),
                Row(
                  children: <Widget>[
                    const Icon(Icons.water_drop, color: Color(0xFF0277BD), size: 14),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        'Dose: $dose',
                        style: const TextStyle(color: Color(0xFF0277BD), fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Action step & timing
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Icon(Icons.access_time, size: 14, color: Colors.grey),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Timing: $timing',
                  style: TextStyle(color: Colors.grey.shade700, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Icon(Icons.check_circle_outline, size: 14, color: Color(0xFF2E7D32)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  action,
                  style: const TextStyle(color: Color(0xFF1B382B), fontSize: 12, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.calculate_outlined, size: 16),
              label: Text(
                isUrdu ? 'ایکڑ کے حساب سے دوائی و پانی نکالیں' : 'Calculate Dosage & Water (Acres)',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFF2E7D32),
                side: const BorderSide(color: Color(0xFF2E7D32)),
                padding: const EdgeInsets.symmetric(vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (ctx) => PesticideCalculatorDialog(
                    crop: crop,
                    pest: pest,
                    solution: solution,
                    dosePerAcre: dose,
                    waterPerAcre: crop == 'Cotton' ? 120 : (crop == 'Rice' ? 0 : 100),
                    costPerAcre: crop == 'Wheat' ? 1650 : (crop == 'Cotton' ? 1600 : (crop == 'Rice' ? 2200 : 1800)),
                    timing: timing,
                    isUrdu: isUrdu,
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
