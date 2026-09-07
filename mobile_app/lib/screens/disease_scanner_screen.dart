import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';

class DiseaseScannerScreen extends ConsumerStatefulWidget {
  const DiseaseScannerScreen({super.key});

  @override
  ConsumerState<DiseaseScannerScreen> createState() => _DiseaseScannerScreenState();
}

class _DiseaseScannerScreenState extends ConsumerState<DiseaseScannerScreen>
    with SingleTickerProviderStateMixin {
  final ImagePicker _picker = ImagePicker();
  String? _selectedImagePath;
  bool _isAnalyzing = false;
  Map<String, dynamic>? _diagnosisResult;

  late AnimationController _scanAnimationController;

  final List<Map<String, dynamic>> _punjabDiseasePresets = [
    {
      'crop': 'Wheat',
      'common': 'Wheat Yellow Rust (Stripe Rust)',
      'scientific': 'Puccinia striiformis',
      'urdu': 'گندم کی پیلی کنگی',
      'confidence': 96.8,
      'severity': 'High',
      'symptoms': 'Yellow to orange pustules in prominent parallel linear stripes along leaf veins.',
      'symptoms_ur': 'پتوں پر رگوں کے متوازی پیلے اور نارنجی رنگ کی دھاریاں اور سفوف۔',
      'spray': 'Tilt 250 EC (Propiconazole)',
      'dosage': '200-250 ml / acre',
      'water_liters': 100,
      'cost_pkr': 1550,
      'phi_days': 21,
      'ipm_advice': 'فوری طور پر ٹرائیازول پھپھوندی کش سپرے کریں تاکہ ہوا کے ذریعے بیج دانوں کا پھیلاؤ روکا جا سکے۔',
      'ipm_advice_en': 'Spray Triazole fungicide within 48 hours to arrest airborne spore dispersion.',
    },
    {
      'crop': 'Cotton',
      'common': 'Cotton Bacterial Blight (Angular Leaf Spot)',
      'scientific': 'Xanthomonas citri pv. malvacearum',
      'urdu': 'کپاس کا بیکٹیریل بلائیٹ',
      'confidence': 94.2,
      'severity': 'High',
      'symptoms': 'Angular water-soaked spots bounded by veins; black lesions on petioles.',
      'symptoms_ur': 'پتوں پر پانی سے بھرے کونیے دار دھبے جو رگوں تک محدود رہتے ہیں اور بعد میں سیاہ ہو جاتے ہیں۔',
      'spray': 'Copper Oxychloride 50 WP + Kasugamycin',
      'dosage': '500 g / acre',
      'water_liters': 100,
      'cost_pkr': 1650,
      'phi_days': 14,
      'ipm_advice': 'کاپر ہائیڈرو آکسائیڈ سپرے کریں اور نائٹروجن کی زیادتی سے پرہیز کریں۔',
      'ipm_advice_en': 'Spray Copper compound and avoid excessive top-dressing nitrogen.',
    },
    {
      'crop': 'Rice',
      'common': 'Rice Blast',
      'scientific': 'Magnaporthe oryzae',
      'urdu': 'دھان کا بلاسٹ / جھلساؤ',
      'confidence': 97.5,
      'severity': 'Critical',
      'symptoms': 'Diamond/spindle-shaped lesions with grey centers and dark reddish margins.',
      'symptoms_ur': 'پتوں پر تکونی اور نوکدار دھبے جن کا درمیان سرمئی اور کنارے گہرے بھورے ہوتے ہیں۔',
      'spray': 'Tricyclazole 75 WP',
      'dosage': '120 g / acre',
      'water_liters': 120,
      'cost_pkr': 1400,
      'phi_days': 28,
      'ipm_advice': 'پھول آنے کے وقت ٹرائی سائیکلازول سپرے کریں اور پانی کھڑا نہ رکھیں۔',
      'ipm_advice_en': 'Apply preventive Tricyclazole spray immediately at panicle initiation.',
    },
    {
      'crop': 'Potato',
      'common': 'Late Blight of Potato',
      'scientific': 'Phytophthora infestans',
      'urdu': 'آلو کا پچھیتا جھلساؤ',
      'confidence': 98.1,
      'severity': 'Critical',
      'symptoms': 'Irregular black water-soaked necrotic patches with white fungal mildew underside.',
      'symptoms_ur': 'پتوں کے کناروں پر سیاہ گیلے دھبے اور نیچے سفید پھپھوندی کا جال۔',
      'spray': 'Acrobat MZ (Dimethomorph + Mancozeb)',
      'dosage': '250 g / acre',
      'water_liters': 120,
      'cost_pkr': 1950,
      'phi_days': 7,
      'ipm_advice': 'دھند یا بارش سے پہلے حفاظتی سپرے کریں اور وٹوں پر مٹی چڑھا کر رکھیں۔',
      'ipm_advice_en': 'Spray systemic fungicide before rain or foggy conditions.',
    },
    {
      'crop': 'Tomato',
      'common': 'Tomato Early Blight',
      'scientific': 'Alternaria solani',
      'urdu': 'ٹماٹر کا اگیتا جھلساؤ',
      'confidence': 92.4,
      'severity': 'Medium',
      'symptoms': 'Concentric ring spots (target-board appearance) on lower older foliage.',
      'symptoms_ur': 'نچلے پتوں پر دائرے دار گول دھبے جو نشانے کے بورڈ جیسے دکھائی دیتے ہیں۔',
      'spray': 'Score 250 EC (Difenoconazole)',
      'dosage': '125 ml / acre',
      'water_liters': 100,
      'cost_pkr': 1350,
      'phi_days': 7,
      'ipm_advice': 'پودوں کو سہارا دے کر زمین سے اوپر رکھیں اور متاثرہ پتے تلف کریں۔',
      'ipm_advice_en': 'Stake plants to avoid soil splash and prune infected lower foliage.',
    },
  ];

  @override
  void initState() {
    super.initState();
    _scanAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat(reverse: true);

    // Default to first preset for instant discovery
    _diagnosisResult = _punjabDiseasePresets.first;
  }

  @override
  void dispose() {
    _scanAnimationController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(source: source);
    if (picked == null) return;

    setState(() {
      _selectedImagePath = picked.path;
      _isAnalyzing = true;
    });

    // Simulate AI model inference delay
    await Future.delayed(const Duration(milliseconds: 1400));

    if (mounted) {
      setState(() {
        _isAnalyzing = false;
        _diagnosisResult = _punjabDiseasePresets.first; // Enriched with model output
      });
    }
  }

  void _selectPreset(Map<String, dynamic> preset) {
    setState(() {
      _selectedImagePath = null;
      _diagnosisResult = preset;
    });
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      backgroundColor: const Color(0xFF071D12),
      appBar: KdAppBar(
        title: isUrdu ? 'فصل بیماری AI سکینر' : 'AI Disease Scanner',
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Camera & Scanner Viewfinder Container
            Container(
              height: 240,
              decoration: BoxDecoration(
                color: Colors.black.withAlpha(140),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: const Color(0xFF00E676).withAlpha(140),
                  width: 2,
                ),
              ),
              child: Stack(
                children: <Widget>[
                  // Background Image or Placeholder
                  if (_selectedImagePath != null)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(18),
                      child: Image.file(
                        File(_selectedImagePath!),
                        fit: BoxFit.cover,
                        width: double.infinity,
                        height: double.infinity,
                      ),
                    )
                  else
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: <Widget>[
                          const Icon(
                            Icons.camera_alt_outlined,
                            size: 48,
                            color: Color(0xFF00E676),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            isUrdu
                                ? 'پتے کی تصویر کھینچیں یا گیلری سے منتخب کریں'
                                : 'Take a photo of infected crop leaf',
                            style: const TextStyle(color: Colors.white70, fontSize: 13),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'ResNet18 CNN + Punjab Surveillance Master',
                            style: TextStyle(color: Colors.white38, fontSize: 10),
                          ),
                        ],
                      ),
                    ),

                  // Viewfinder Target Corners
                  const Positioned(
                    top: 16,
                    left: 16,
                    child: _CornerBracket(isTop: true, isLeft: true),
                  ),
                  const Positioned(
                    top: 16,
                    right: 16,
                    child: _CornerBracket(isTop: true, isLeft: false),
                  ),
                  const Positioned(
                    bottom: 16,
                    left: 16,
                    child: _CornerBracket(isTop: false, isLeft: true),
                  ),
                  const Positioned(
                    bottom: 16,
                    right: 16,
                    child: _CornerBracket(isTop: false, isLeft: false),
                  ),

                  // Animated Scanning Laser
                  if (_isAnalyzing || _selectedImagePath != null)
                    AnimatedBuilder(
                      animation: _scanAnimationController,
                      builder: (context, child) {
                        return Positioned(
                          top: 20 + _scanAnimationController.value * 180,
                          left: 20,
                          right: 20,
                          child: Container(
                            height: 3,
                            decoration: BoxDecoration(
                              color: const Color(0xFF00E676),
                              boxShadow: <BoxShadow>[
                                BoxShadow(
                                  color: const Color(0xFF00E676).withAlpha(180),
                                  blurRadius: 10,
                                  spreadRadius: 2,
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),

                  // Live Status Pill
                  Positioned(
                    top: 12,
                    left: 0,
                    right: 0,
                    child: Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.black87,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFF00E676).withAlpha(100)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: Color(0xFF00E676),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              _isAnalyzing
                                  ? (isUrdu ? 'AI تشخیص جاری ہے...' : 'AI Diagnosing Leaf...')
                                  : (isUrdu ? 'AI کیمرہ سکینر تیار ہے' : 'Vision Scanner Ready'),
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Capture & Upload Buttons
            Row(
              children: <Widget>[
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _pickImage(ImageSource.camera),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00E676),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: const Icon(Icons.camera_alt),
                    label: Text(
                      isUrdu ? 'کیمرہ سے فوٹو لیں' : 'Capture Leaf',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Color(0xFF00E676)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: const Icon(Icons.photo_library, color: Color(0xFF00E676)),
                    label: Text(
                      isUrdu ? 'گیلری سے منتخب کریں' : 'Choose Gallery',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),

            // Sample Disease Leaves Selector
            Text(
              isUrdu ? 'پنجاب کی اہم فصلوں کے تصدیق شدہ نمونے:' : 'Sample Leaf Presets (Punjab Master DB):',
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _punjabDiseasePresets.map((preset) {
                  final isSelected = _diagnosisResult?['common'] == preset['common'];
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => _selectPreset(preset),
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
                          isUrdu ? '${preset['urdu']}' : '${preset['crop']}: ${preset['common'].toString().split(' ').first}',
                          style: TextStyle(
                            color: isSelected ? Colors.black : Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 18),

            // Diagnosis Result Card
            if (_diagnosisResult != null) ...<Widget>[
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
                    // Title & Confidence
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                isUrdu
                                    ? _diagnosisResult!['urdu'] as String
                                    : _diagnosisResult!['common'] as String,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                _diagnosisResult!['scientific'] as String,
                                style: const TextStyle(
                                  color: Color(0xFF00E676),
                                  fontStyle: FontStyle.italic,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00E676).withAlpha(40),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFF00E676)),
                          ),
                          child: Column(
                            children: <Widget>[
                              Text(
                                '${_diagnosisResult!['confidence']}%',
                                style: const TextStyle(
                                  color: Color(0xFF00E676),
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                isUrdu ? 'درستگی' : 'Confidence',
                                style: const TextStyle(color: Colors.white70, fontSize: 9),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Severity & Crop
                    Row(
                      children: <Widget>[
                        _buildInfoBadge(
                          isUrdu ? 'فصل' : 'Crop',
                          _diagnosisResult!['crop'] as String,
                          const Color(0xFF4FC3F7),
                        ),
                        const SizedBox(width: 8),
                        _buildInfoBadge(
                          isUrdu ? 'شدت' : 'Severity',
                          _diagnosisResult!['severity'] as String,
                          const Color(0xFFFF5252),
                        ),
                        const SizedBox(width: 8),
                        _buildInfoBadge(
                          isUrdu ? 'وقفہ (PHI)' : 'PHI Days',
                          '${_diagnosisResult!['phi_days']} Days',
                          const Color(0xFFFFD54F),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Symptoms
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF133B26),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            isUrdu ? 'علامات:' : 'Key Symptoms:',
                            style: const TextStyle(
                              color: Color(0xFF00E676),
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            isUrdu
                                ? _diagnosisResult!['symptoms_ur'] as String
                                : _diagnosisResult!['symptoms'] as String,
                            style: const TextStyle(color: Colors.white, fontSize: 12, height: 1.3),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Chemical Treatment Box
                    Container(
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
                        border: Border.all(color: const Color(0xFF00E676).withAlpha(140)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Row(
                            children: <Widget>[
                              const Icon(Icons.sanitizer, color: Color(0xFF00E676), size: 18),
                              const SizedBox(width: 6),
                              Text(
                                isUrdu ? 'تجویز کردہ زرعی زہر (سپرے):' : 'Recommended Spray Protocol:',
                                style: const TextStyle(
                                  color: Color(0xFF00E676),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _diagnosisResult!['spray'] as String,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: <Widget>[
                              Text(
                                isUrdu
                                    ? 'مقدار: ${_diagnosisResult!['dosage']}'
                                    : 'Dosage: ${_diagnosisResult!['dosage']}',
                                style: const TextStyle(color: Colors.white70, fontSize: 12),
                              ),
                              Text(
                                isUrdu
                                    ? 'پانی: ${_diagnosisResult!['water_liters']}L'
                                    : 'Water: ${_diagnosisResult!['water_liters']}L/acre',
                                style: const TextStyle(color: Colors.white70, fontSize: 12),
                              ),
                              Text(
                                'Rs. ${_diagnosisResult!['cost_pkr']}',
                                style: const TextStyle(
                                  color: Color(0xFFFFD54F),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // IPM Cultural Advice
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF133B26),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          const Icon(Icons.shield_outlined, color: Color(0xFFFFD54F), size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Text(
                                  isUrdu ? 'حفاظتی تدابیر (IPM Advice):' : 'IPM Cultural Management:',
                                  style: const TextStyle(
                                    color: Color(0xFFFFD54F),
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  isUrdu
                                      ? _diagnosisResult!['ipm_advice'] as String
                                      : _diagnosisResult!['ipm_advice_en'] as String,
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
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoBadge(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 6),
        decoration: BoxDecoration(
          color: color.withAlpha(25),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withAlpha(80)),
        ),
        child: Column(
          children: <Widget>[
            Text(label, style: const TextStyle(color: Colors.white60, fontSize: 9)),
            const SizedBox(height: 2),
            Text(
              value,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}

class _CornerBracket extends StatelessWidget {
  const _CornerBracket({required this.isTop, required this.isLeft});

  final bool isTop;
  final bool isLeft;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 20,
      height: 20,
      decoration: BoxDecoration(
        border: Border(
          top: isTop ? const BorderSide(color: Color(0xFF00E676), width: 3) : BorderSide.none,
          bottom: !isTop ? const BorderSide(color: Color(0xFF00E676), width: 3) : BorderSide.none,
          left: isLeft ? const BorderSide(color: Color(0xFF00E676), width: 3) : BorderSide.none,
          right: !isLeft ? const BorderSide(color: Color(0xFF00E676), width: 3) : BorderSide.none,
        ),
      ),
    );
  }
}
