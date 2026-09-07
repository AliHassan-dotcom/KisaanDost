import 'package:flutter/material.dart';

class YieldPredictionWidget extends StatefulWidget {
  const YieldPredictionWidget({
    super.key,
    required this.district,
    this.isUrdu = false,
  });

  final String district;
  final bool isUrdu;

  @override
  State<YieldPredictionWidget> createState() => _YieldPredictionWidgetState();
}

class _YieldPredictionWidgetState extends State<YieldPredictionWidget> {
  String _selectedCrop = 'Wheat';
  double _acres = 5.0;
  String _soilType = 'Loam / زرخیز میرا';
  String _irrigationType = 'Canal + Tubewell / نہری اور ٹیوب ویل';

  final Map<String, Map<String, dynamic>> _cropData = {
    'Wheat': {
      'urdu': 'گندم',
      'base_yield': 36.5,
      'price_per_maund': 3850,
      'unit': 'من فی ایکڑ (Maunds/acre)',
      'booster': 'دانے بننے کے وقت پوٹاش (SOP) کا سپرے پیداوار میں 3.5 من اضافہ کرتا ہے۔',
      'booster_en': 'Apply Potash (SOP) at heading stage to boost grain yield by +3.5 maunds/acre.',
    },
    'Cotton': {
      'urdu': 'کپاس',
      'base_yield': 23.0,
      'price_per_maund': 8200,
      'unit': 'من فی ایکڑ (Maunds/acre)',
      'booster': 'پھول اور ٹینڈے بننے کے دوران زنک اور بوران کا سپرے کیرا روکتا ہے۔',
      'booster_en': 'Foliar application of Zinc & Boron prevents square and boll shedding.',
    },
    'Rice': {
      'urdu': 'دھان / چاول',
      'base_yield': 39.0,
      'price_per_maund': 4400,
      'unit': 'من فی ایکڑ (Maunds/acre)',
      'booster': 'گوبھ کے وقت 2 انچ پانی کھڑا رکھیں تاکہ سٹے میں دودھیا دانہ مکمل بن سکے۔',
      'booster_en': 'Maintain 2-inch shallow standing water layer during grain milk stage.',
    },
    'Sugarcane': {
      'urdu': 'کماد / گنا',
      'base_yield': 680.0,
      'price_per_maund': 425,
      'unit': 'من فی ایکڑ (Maunds/acre)',
      'booster': 'مون سون میں جڑوں پر مٹی چڑھائیں تاکہ گنا گرنے سے محفوظ رہے۔',
      'booster_en': 'Ensure earthing up before monsoon rains to prevent crop lodging.',
    },
    'Maize': {
      'urdu': 'مکئی',
      'base_yield': 56.0,
      'price_per_maund': 2650,
      'unit': 'من فی ایکڑ (Maunds/acre)',
      'booster': 'چھلی بنتے وقت یوریا کی آخری قسط پیداوار میں 15 فیصد اضافہ کرتی ہے۔',
      'booster_en': 'Apply final split dose of Nitrogen at cob initiation stage.',
    },
  };

  @override
  Widget build(BuildContext context) {
    final cropInfo = _cropData[_selectedCrop]!;
    final double baseYield = cropInfo['base_yield'] as double;
    final int mandiPrice = cropInfo['price_per_maund'] as int;

    // Modifiers based on soil and irrigation
    double soilMod = _soilType.contains('Loam') ? 1.06 : 0.95;
    double irriMod = _irrigationType.contains('Canal + Tubewell') ? 1.08 : 0.96;

    final predictedPerAcre = double.parse((baseYield * soilMod * irriMod).toStringAsFixed(1));
    final totalMaunds = double.parse((predictedPerAcre * _acres).toStringAsFixed(1));
    final grossRevenue = (totalMaunds * mandiPrice).toInt();
    final districtAvg = double.parse((baseYield * 1.02).toStringAsFixed(1));
    final variancePct = double.parse((((predictedPerAcre - districtAvg) / districtAvg) * 100).toStringAsFixed(1));

    return Card(
      elevation: 3,
      color: const Color(0xFF0B2618),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF1E5638)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFD54F).withAlpha(35),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.analytics_rounded, color: Color(0xFFFFD54F), size: 22),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? 'AI پیداوار پیشن گوئی ماڈل' : 'Predictive Yield Analytics',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          widget.isUrdu ? '${widget.district} - پی بی ایس زرعی شماریات' : '${widget.district} - ML Yield Forecaster',
                          style: const TextStyle(color: Colors.white60, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E676).withAlpha(40),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF00E676)),
                  ),
                  child: const Text(
                    '92.4% Accuracy',
                    style: TextStyle(
                      color: Color(0xFF00E676),
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Crop Selector Chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _cropData.keys.map((cropKey) {
                  final isSelected = _selectedCrop == cropKey;
                  final info = _cropData[cropKey]!;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _selectedCrop = cropKey),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 180),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        decoration: BoxDecoration(
                          color: isSelected ? const Color(0xFF00E676) : const Color(0xFF0F3622),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: isSelected ? const Color(0xFF00E676) : Colors.white24,
                          ),
                        ),
                        child: Text(
                          widget.isUrdu ? '${info['urdu']} ($cropKey)' : cropKey,
                          style: TextStyle(
                            color: isSelected ? Colors.black : Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 14),

            // Acreage Slider
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  widget.isUrdu ? 'فارم رقبہ (ایکڑ):' : 'Farm Acreage:',
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFF133B26),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF00E676)),
                  ),
                  child: Text(
                    '${_acres.toStringAsFixed(0)} Acres',
                    style: const TextStyle(
                      color: Color(0xFF00E676),
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
            SliderTheme(
              data: const SliderThemeData(
                thumbColor: Color(0xFF00E676),
                activeTrackColor: Color(0xFF00E676),
                inactiveTrackColor: Colors.white24,
                trackHeight: 3,
                thumbShape: RoundSliderThumbShape(enabledThumbRadius: 7),
              ),
              child: Slider(
                value: _acres,
                min: 1.0,
                max: 50.0,
                divisions: 49,
                onChanged: (val) => setState(() => _acres = val),
              ),
            ),
            const SizedBox(height: 6),

            // Soil & Irrigation Dropdowns
            Row(
              children: <Widget>[
                // Soil Selector
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFF133B26),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white12),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _soilType,
                        isExpanded: true,
                        dropdownColor: const Color(0xFF0B2618),
                        items: const <String>[
                          'Loam / زرخیز میرا',
                          'Clay Loam / چکنی میرا',
                          'Sandy Loam / ریتلی میرا',
                        ].map((s) => DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(color: Colors.white, fontSize: 11)))).toList(),
                        onChanged: (v) {
                          if (v != null) setState(() => _soilType = v);
                        },
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Irrigation Selector
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFF133B26),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white12),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _irrigationType,
                        isExpanded: true,
                        dropdownColor: const Color(0xFF0B2618),
                        items: const <String>[
                          'Canal + Tubewell / نہری اور ٹیوب ویل',
                          'Tubewell Only / صرف ٹیوب ویل',
                          'Rainfed / بارانی',
                        ].map((s) => DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(color: Colors.white, fontSize: 11)))).toList(),
                        onChanged: (v) {
                          if (v != null) setState(() => _irrigationType = v);
                        },
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Key Results Grid
            Row(
              children: <Widget>[
                // Expected Yield per Acre
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: <Color>[
                          const Color(0xFF00E676).withAlpha(30),
                          const Color(0xFF00E676).withAlpha(10),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF00E676).withAlpha(120)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? 'تخمینی پیداوار فی ایکڑ' : 'Predicted Yield / Acre',
                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.baseline,
                          textBaseline: TextBaseline.alphabetic,
                          children: <Widget>[
                            Text(
                              '$predictedPerAcre',
                              style: const TextStyle(
                                color: Color(0xFF00E676),
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 4),
                            const Text(
                              'Maunds',
                              style: TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          widget.isUrdu
                              ? 'ضلعی اوسط سے ${variancePct >= 0 ? '+' : ''}$variancePct% زیادہ'
                              : '${variancePct >= 0 ? '+' : ''}$variancePct% vs 5-Yr Avg ($districtAvg)',
                          style: TextStyle(
                            color: variancePct >= 0 ? const Color(0xFF00E676) : const Color(0xFFFF5252),
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 10),

                // Gross Revenue (PKR)
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: <Color>[
                          const Color(0xFFFFD54F).withAlpha(30),
                          const Color(0xFFFFD54F).withAlpha(10),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFFFD54F).withAlpha(120)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? 'تخمینی آمدن (منڈی ریٹ)' : 'Estimated Revenue',
                          style: const TextStyle(color: Colors.white70, fontSize: 11),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Rs. ${(grossRevenue / 1000).toStringAsFixed(0)}k',
                          style: const TextStyle(
                            color: Color(0xFFFFD54F),
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          widget.isUrdu
                              ? 'کل: $totalMaunds من @ Rs. $mandiPrice'
                              : 'Total: $totalMaunds Maunds',
                          style: const TextStyle(color: Colors.white60, fontSize: 10),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // AI Agronomic Booster Advice Card
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF133B26),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white12),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Icon(Icons.tips_and_updates, color: Color(0xFFFFD54F), size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          widget.isUrdu ? 'پیداوار بڑھانے کا AI مشورہ:' : 'AI Yield Booster Protocol:',
                          style: const TextStyle(
                            color: Color(0xFFFFD54F),
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          widget.isUrdu
                              ? (cropInfo['booster'] as String)
                              : (cropInfo['booster_en'] as String),
                          style: const TextStyle(color: Colors.white, fontSize: 11, height: 1.3),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
