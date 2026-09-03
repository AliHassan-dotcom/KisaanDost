import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/profile_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';

class IrrigationScreen extends ConsumerWidget {
  const IrrigationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(profileProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    final cropName = profileAsync.value?.crop ?? 'Wheat';
    final districtName = profileAsync.value?.district ?? 'Lahore';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'سمارٹ آبپاشی شیڈول' : 'Smart Irrigation Advisor',
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Irrigation Telemetry Header Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[Colors.blue.shade700, Colors.blue.shade900],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: Colors.blue.shade900.withAlpha(50),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
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
                          const Icon(Icons.water_drop, color: Colors.white, size: 24),
                          const SizedBox(width: 8),
                          Text(
                            isUrdu ? 'آبپاشی شیڈول ماڈل' : 'FAO-56 Evapotranspiration Model',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.white.withAlpha(50),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'Optimal Health',
                          style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${cropName.toUpperCase()} · $districtName',
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isUrdu
                        ? 'موسم اور مٹی کی نمی کے مطابق خودکار پانی کا شیڈول'
                        : 'Dynamic water balance computed using live weather & root depth',
                    style: TextStyle(color: Colors.blue.shade100, fontSize: 12),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Soil Moisture Gauge Card
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: Colors.blue.shade100),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'مٹی میں نمی کا تناسب' : 'Soil Moisture Level (Root Zone)',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        Text(
                          '68%',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                            color: Colors.blue.shade900,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: 0.68,
                        minHeight: 10,
                        backgroundColor: Colors.grey.shade200,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.blue.shade600),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'خشک مٹی' : 'Wilting Point (30%)',
                          style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                        ),
                        Text(
                          isUrdu ? 'مناسب نمی (60-80%)' : 'Optimal Capacity',
                          style: TextStyle(fontSize: 11, color: Colors.green.shade800, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          isUrdu ? 'سیراب (100%)' : 'Field Capacity',
                          style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Next Watering Recommendation Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.green.shade300),
              ),
              child: Row(
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.green.shade100,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(Icons.alarm_on, color: Colors.green.shade900, size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'اگلی آبپاشی کی تجویز:' : 'Next Watering Recommendation:',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                            color: Colors.green.shade900,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          isUrdu ? '2 دن بعد (35 ملی میٹر / 3 انچ)' : 'In 2 Days (~35 mm / 3 acre-inches)',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                            color: Colors.green.shade900,
                          ),
                        ),
                        Text(
                          isUrdu
                              ? 'صبح یا شام کے وقت پانی لگائیں تاکہ بخارات کم بنیں۔'
                              : 'Apply in early morning or late evening for max absorption.',
                          style: TextStyle(fontSize: 11, color: Colors.green.shade800),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Agronomic Evapotranspiration Metrics
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: Colors.grey.shade200),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      isUrdu ? 'پانی کے اخراج کے سائنسی اعدادوشمار' : 'Agronomic Water Parameters',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    const SizedBox(height: 12),
                    _buildParamRow(
                      context,
                      label: isUrdu ? 'حوالہ بخارات (ET₀):' : 'Reference Evapotranspiration (ET₀):',
                      value: '4.8 mm/day',
                    ),
                    _buildParamRow(
                      context,
                      label: isUrdu ? 'فصل کا فیکٹر (Kc):' : 'Crop Coefficient (Kc):',
                      value: '0.85 (Mid-Season)',
                    ),
                    _buildParamRow(
                      context,
                      label: isUrdu ? 'فصل کی روزانہ ضرورت (ETc):' : 'Daily Crop Water Need (ETc):',
                      value: '4.1 mm/day',
                    ),
                    _buildParamRow(
                      context,
                      label: isUrdu ? 'جڑوں کی گہرائی:' : 'Effective Root Zone Depth:',
                      value: '45 - 60 cm',
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildParamRow(BuildContext context, {required String label, required String value}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Text(label, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
          Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
