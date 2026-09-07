import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';

class WhatIfAnalysisScreen extends ConsumerStatefulWidget {
  const WhatIfAnalysisScreen({super.key});

  @override
  ConsumerState<WhatIfAnalysisScreen> createState() => _WhatIfAnalysisScreenState();
}

class _WhatIfAnalysisScreenState extends ConsumerState<WhatIfAnalysisScreen> {
  String _district = 'Lahore';
  String _crop = 'Wheat';
  double _acres = 5.0;

  double _tempDelta = 0.0; // -4 to +5 deg C
  double _rainfallDelta = 0.0; // -40 to +60 mm
  double _humidityDelta = 0.0; // -25 to +25 %
  double _sowingShift = 0.0; // -15 to +30 days
  double _irrigationRatio = 1.0; // 0.6 to 1.4

  void _applyPreset(String name) {
    setState(() {
      if (name == 'heatwave') {
        _tempDelta = 3.5;
        _rainfallDelta = -25.0;
        _humidityDelta = -15.0;
        _sowingShift = 0.0;
        _irrigationRatio = 0.8;
      } else if (name == 'monsoon') {
        _tempDelta = -1.0;
        _rainfallDelta = 45.0;
        _humidityDelta = 20.0;
        _sowingShift = 0.0;
        _irrigationRatio = 1.2;
      } else if (name == 'late_sowing') {
        _tempDelta = 1.5;
        _rainfallDelta = 0.0;
        _humidityDelta = 10.0;
        _sowingShift = 20.0;
        _irrigationRatio = 1.0;
      } else {
        // Reset
        _tempDelta = 0.0;
        _rainfallDelta = 0.0;
        _humidityDelta = 0.0;
        _sowingShift = 0.0;
        _irrigationRatio = 1.0;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    // Real-time dynamic simulation calculations
    final double basePestRisk = 62.0;
    double simPestRisk = basePestRisk;
    if (_crop == 'Wheat') {
      if (_humidityDelta > 0 && _tempDelta <= 2.0) {
        simPestRisk += _humidityDelta * 0.7 + (_rainfallDelta / 10.0) * 2.2;
      } else if (_tempDelta > 2.5) {
        simPestRisk -= _tempDelta * 2.5;
      }
    } else {
      if (_tempDelta > 0 && _humidityDelta > 0) {
        simPestRisk += _tempDelta * 2.2 + _humidityDelta * 0.5;
      }
    }
    simPestRisk = simPestRisk.clamp(12.0, 96.0);
    final double pestDelta = double.parse((simPestRisk - basePestRisk).toStringAsFixed(1));

    // Yield Calculations
    final double baseYield = _crop == 'Wheat' ? 36.5 : (_crop == 'Cotton' ? 22.8 : 39.0);
    final int mandiPrice = _crop == 'Wheat' ? 3850 : (_crop == 'Cotton' ? 8200 : 4400);

    final double tempPenalty = -_tempDelta.abs() * 0.032;
    final double rainPenalty = (_rainfallDelta / 100.0) * 0.06;
    final double sowingPenalty = -(_sowingShift / 30.0) * 0.12;
    final double irriEffect = (_irrigationRatio - 1.0) * 0.18;
    final double pestPenalty = -(simPestRisk > 70 ? (simPestRisk - 70) * 0.006 : 0.0);

    final double totalFactor = 1.0 + tempPenalty + rainPenalty + sowingPenalty + irriEffect + pestPenalty;
    final double simYield = double.parse((baseYield * totalFactor.clamp(0.4, 1.4)).toStringAsFixed(1));
    final double yieldDiffPct = double.parse((((simYield - baseYield) / baseYield) * 100).toStringAsFixed(1));

    final int baseRev = (baseYield * _acres * mandiPrice).toInt();
    final int simRev = (simYield * _acres * mandiPrice).toInt();
    final int revDelta = simRev - baseRev;

    return Scaffold(
      backgroundColor: const Color(0xFF071D12),
      appBar: KdAppBar(
        title: isUrdu ? 'موسمیاتی منظر نامہ (What-If)' : 'What-If Scenario Analysis',
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 36),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Hero Intro Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    const Color(0xFF1B5E20),
                    const Color(0xFF071D12),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF00E676).withAlpha(120)),
              ),
              child: Row(
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00E676).withAlpha(40),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.tune, color: Color(0xFF00E676), size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'AI اسمارٹ اسکرین سمولیشن' : 'AI Scenario Simulator',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          isUrdu
                              ? '$_district · $_crop (${_acres.toStringAsFixed(0)} ایکڑ) - موسم اور آبپاشی بدل کر اثرات دیکھیں'
                              : '$_district · $_crop (${_acres.toStringAsFixed(0)} Acres) - Climate & Farm Adjustment Simulator',
                          style: const TextStyle(color: Colors.white70, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Crop & District Selector Row
            Row(
              children: <Widget>[
                // District Dropdown
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F3622),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF1E5638)),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: _district,
                      dropdownColor: const Color(0xFF0B2618),
                      items: <String>[
                        'Lahore', 'Faisalabad', 'Multan', 'Gujranwala', 'Sahiwal',
                        'Bahawalpur', 'Rahim Yar Khan', 'Sargodha', 'Sheikhupura', 'Rawalpindi'
                      ].map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(color: Colors.white, fontSize: 12)))).toList(),
                      onChanged: (v) {
                        if (v != null) setState(() => _district = v);
                      },
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Acreage Chip
                ActionChip(
                  avatar: const Icon(Icons.crop_square, size: 14, color: Color(0xFF00E676)),
                  label: Text('${_acres.toStringAsFixed(0)} Acres', style: const TextStyle(color: Colors.white, fontSize: 12)),
                  backgroundColor: const Color(0xFF0F3622),
                  side: const BorderSide(color: Color(0xFF1E5638)),
                  onPressed: () {
                    setState(() {
                      _acres = _acres >= 25.0 ? 5.0 : _acres + 5.0;
                    });
                  },
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Crop Selector Chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: <String>['Wheat', 'Cotton', 'Rice', 'Sugarcane', 'Maize'].map((c) {
                  final isSelected = _crop == c;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(
                        isUrdu ? (c == 'Wheat' ? 'گندم' : (c == 'Cotton' ? 'کپاس' : (c == 'Rice' ? 'دھان' : (c == 'Sugarcane' ? 'کماد' : 'مکئی')))) : c,
                        style: TextStyle(
                          color: isSelected ? Colors.black : Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: const Color(0xFF00E676),
                      backgroundColor: const Color(0xFF0F3622),
                      onSelected: (selected) {
                        if (selected) setState(() => _crop = c);
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 14),

            // Quick Scenario Presets
            Text(
              isUrdu ? 'پری سیٹ منظر نامے:' : 'Simulated Scenario Presets:',
              style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: <Widget>[
                  _buildPresetChip('reset', isUrdu ? 'نارمل موسم' : 'Baseline Weather', Icons.restore),
                  const SizedBox(width: 8),
                  _buildPresetChip('heatwave', isUrdu ? 'شدید گرمی و خشک سالی' : 'Heatwave & Drought', Icons.whatshot),
                  const SizedBox(width: 8),
                  _buildPresetChip('monsoon', isUrdu ? 'زیادہ بارشیں و نمی' : 'Heavy Monsoon', Icons.thunderstorm),
                  const SizedBox(width: 8),
                  _buildPresetChip('late_sowing', isUrdu ? 'تاخیر سے کاشت' : 'Late Sowing Shift', Icons.schedule),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // Sliders Section Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0B2618),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF1E5638)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    isUrdu ? 'موسمیاتی اور فارم کنٹرول سلائیڈرز:' : 'Environmental & Management Sliders:',
                    style: const TextStyle(
                      color: Color(0xFF00E676),
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Temperature Slider
                  _buildSliderRow(
                    label: isUrdu ? 'درجہ حرارت میں تبدیلی' : 'Temperature Delta',
                    valueStr: '${_tempDelta >= 0 ? '+' : ''}${_tempDelta.toStringAsFixed(1)}°C',
                    value: _tempDelta,
                    min: -4.0,
                    max: 5.0,
                    divisions: 18,
                    onChanged: (v) => setState(() => _tempDelta = v),
                    color: _tempDelta > 2.0 ? const Color(0xFFFF5252) : const Color(0xFF00E676),
                  ),
                  const Divider(color: Colors.white12, height: 16),

                  // Rainfall Slider
                  _buildSliderRow(
                    label: isUrdu ? 'بارش میں کمی / بیشی' : 'Rainfall Variation',
                    valueStr: '${_rainfallDelta >= 0 ? '+' : ''}${_rainfallDelta.toStringAsFixed(0)} mm',
                    value: _rainfallDelta,
                    min: -40.0,
                    max: 60.0,
                    divisions: 20,
                    onChanged: (v) => setState(() => _rainfallDelta = v),
                    color: const Color(0xFF4FC3F7),
                  ),
                  const Divider(color: Colors.white12, height: 16),

                  // Humidity Slider
                  _buildSliderRow(
                    label: isUrdu ? 'ہوا میں نمی کا تناسب' : 'Relative Humidity Delta',
                    valueStr: '${_humidityDelta >= 0 ? '+' : ''}${_humidityDelta.toStringAsFixed(0)}%',
                    value: _humidityDelta,
                    min: -25.0,
                    max: 25.0,
                    divisions: 20,
                    onChanged: (v) => setState(() => _humidityDelta = v),
                    color: const Color(0xFFFFD54F),
                  ),
                  const Divider(color: Colors.white12, height: 16),

                  // Sowing Date Shift Slider
                  _buildSliderRow(
                    label: isUrdu ? 'کاشت میں تاخیر (دن)' : 'Sowing Date Shift',
                    valueStr: '${_sowingShift >= 0 ? '+' : ''}${_sowingShift.toStringAsFixed(0)} Days',
                    value: _sowingShift,
                    min: -15.0,
                    max: 30.0,
                    divisions: 9,
                    onChanged: (v) => setState(() => _sowingShift = v),
                    color: const Color(0xFFAB47BC),
                  ),
                  const Divider(color: Colors.white12, height: 16),

                  // Irrigation Ratio Slider
                  _buildSliderRow(
                    label: isUrdu ? 'پانی کی فراہمی' : 'Irrigation Supply Ratio',
                    valueStr: '${(_irrigationRatio * 100).toStringAsFixed(0)}%',
                    value: _irrigationRatio,
                    min: 0.6,
                    max: 1.4,
                    divisions: 8,
                    onChanged: (v) => setState(() => _irrigationRatio = v),
                    color: const Color(0xFF26A69A),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // Simulation Impact Projection Dashboard
            Text(
              isUrdu ? 'سمولیشن کے متوقع نتائج:' : 'Simulated Impact Projections:',
              style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),

            Row(
              children: <Widget>[
                // Pest Outbreak Probability
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0B2618),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: simPestRisk > 75 ? const Color(0xFFFF5252) : const Color(0xFF1E5638),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'کیڑوں کا خطرہ' : 'Pest Outbreak Risk',
                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: <Widget>[
                            Text(
                              '${simPestRisk.toStringAsFixed(1)}%',
                              style: TextStyle(
                                color: simPestRisk > 75 ? const Color(0xFFFF5252) : const Color(0xFF00E676),
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${pestDelta >= 0 ? '+' : ''}$pestDelta% vs Base',
                          style: TextStyle(
                            color: pestDelta > 0 ? const Color(0xFFFF5252) : const Color(0xFF00E676),
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Projected Yield Impact
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0B2618),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: yieldDiffPct < -5 ? const Color(0xFFFF5252) : const Color(0xFF1E5638),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'پیداوار پر اثر' : 'Projected Yield',
                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$simYield Maunds',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${yieldDiffPct >= 0 ? '+' : ''}$yieldDiffPct% ($simYield vs $baseYield)',
                          style: TextStyle(
                            color: yieldDiffPct >= 0 ? const Color(0xFF00E676) : const Color(0xFFFF5252),
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Financial Impact Card
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF133B26),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.white12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        isUrdu ? 'مالی اثرات (5 ایکڑ فارم):' : 'Estimated Farm Revenue Delta (5 Acres):',
                        style: const TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Total: Rs. ${(simRev / 1000).toStringAsFixed(0)}k PKR',
                        style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: revDelta >= 0 ? const Color(0xFF00E676).withAlpha(35) : const Color(0xFFFF5252).withAlpha(35),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: revDelta >= 0 ? const Color(0xFF00E676) : const Color(0xFFFF5252),
                      ),
                    ),
                    child: Text(
                      '${revDelta >= 0 ? '+' : ''}Rs. ${(revDelta / 1000).toStringAsFixed(0)}k',
                      style: TextStyle(
                        color: revDelta >= 0 ? const Color(0xFF00E676) : const Color(0xFFFF5252),
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Mitigation Playbook Card
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF0B2618),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFFFD54F).withAlpha(120)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      const Icon(Icons.security, color: Color(0xFFFFD54F), size: 18),
                      const SizedBox(width: 8),
                      Text(
                        isUrdu ? 'اس منظر نامے کے لیے حفاظتی حکمت عملی:' : 'Agri-Mitigation Action Playbook:',
                        style: const TextStyle(
                          color: Color(0xFFFFD54F),
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (pestDelta > 10.0)
                    _buildMitigationItem(
                      isUrdu
                          ? 'پھپھوندی کے حملے کا خطرہ زیادہ ہے: بارش سے قبل حفاظتی فنجی سائیڈ سپرے مکمل کریں۔'
                          : 'High disease outbreak potential: Apply preventive fungicide spray before rainfall.',
                    ),
                  if (_tempDelta > 2.0)
                    _buildMitigationItem(
                      isUrdu
                          ? 'تپش اور گرمی کا تناؤ: ہلکی اور بار بار آبپاشی کریں تاکہ زمین کی نمی برقرار رہے۔'
                          : 'Heat stress warning: Provide light, frequent irrigation to maintain soil turgor.',
                    ),
                  if (_rainfallDelta < -20.0 || _irrigationRatio < 0.85)
                    _buildMitigationItem(
                      isUrdu
                          ? 'خشک سالی کی صورت میں ملچنگ کریں اور دانہ بنتے وقت پانی لازمی دیں۔'
                          : 'Moisture deficit: Apply soil mulching and prioritize water at grain formation.',
                    ),
                  if (_sowingShift > 10.0)
                    _buildMitigationItem(
                      isUrdu
                          ? 'تاخیر سے کاشت کا ازالہ: بیج کی شرح 10-15 فیصد بڑھائیں اور نائٹروجن کی خوراک تقسیم کریں۔'
                          : 'Late sowing offset: Increase seed rate by 12% and split fertilizer application.',
                    ),
                  if (pestDelta <= 10.0 && _tempDelta <= 2.0 && _rainfallDelta >= -20.0 && _sowingShift <= 10.0)
                    _buildMitigationItem(
                      isUrdu
                          ? 'موسمی حالات سازگار ہیں: معمول کی کھاد اور اسپرے کا شیڈول جاری رکھیں۔'
                          : 'Favorable seasonal baseline: Maintain standard fertilization and pest scouting.',
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPresetChip(String key, String label, IconData icon) {
    return GestureDetector(
      onTap: () => _applyPreset(key),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: const Color(0xFF0F3622),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF1E5638)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 15, color: const Color(0xFF00E676)),
            const SizedBox(width: 6),
            Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  Widget _buildSliderRow({
    required String label,
    required String valueStr,
    required double value,
    required double min,
    required double max,
    required int divisions,
    required ValueChanged<double> onChanged,
    required Color color,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: <Widget>[
            Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: color.withAlpha(25),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: color.withAlpha(100)),
              ),
              child: Text(
                valueStr,
                style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ),
          ],
        ),
        SliderTheme(
          data: SliderThemeData(
            thumbColor: color,
            activeTrackColor: color,
            inactiveTrackColor: Colors.white12,
            trackHeight: 2,
            thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
          ),
          child: Slider(
            value: value,
            min: min,
            max: max,
            divisions: divisions,
            onChanged: onChanged,
          ),
        ),
      ],
    );
  }

  Widget _buildMitigationItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text('• ', style: TextStyle(color: Color(0xFFFFD54F), fontSize: 14)),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: Colors.white, fontSize: 12, height: 1.3),
            ),
          ),
        ],
      ),
    );
  }
}
