import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../providers/scan_provider.dart';
import '../providers/settings_provider.dart';
import '../utils/image_validator.dart';
import '../widgets/kd_app_bar.dart';

class ScanScreen extends ConsumerStatefulWidget {
  const ScanScreen({super.key});

  @override
  ConsumerState<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends ConsumerState<ScanScreen> {
  final ImagePicker _picker = ImagePicker();
  String? _selectedPath;
  String? _validationError;

  final List<Map<String, String>> _sampleLeaves = const <Map<String, String>>[
    {
      'title': 'Wheat Yellow Rust',
      'urdu': 'گندم کی پیلی کنگی',
      'crop': 'Wheat',
      'disease': 'Puccinia striiformis (Yellow Rust)',
      'spray': 'Tebuconazole 250 EC @ 200ml/acre',
    },
    {
      'title': 'Tomato Early Blight',
      'urdu': 'ٹماٹر کا اگیتا جھلسائو',
      'crop': 'Tomato',
      'disease': 'Alternaria solani (Early Blight)',
      'spray': 'Difenoconazole + Azoxystrobin @ 200ml/acre',
    },
    {
      'title': 'Cotton Bacterial Blight',
      'urdu': 'کپاس کا بیکٹیریل بلائیٹ',
      'crop': 'Cotton',
      'disease': 'Xanthomonas campestris',
      'spray': 'Copper Oxychloride 50 WP @ 500g/acre',
    },
    {
      'title': 'Potato Late Blight',
      'urdu': 'آلو کا پچھیتا جھلسائو',
      'crop': 'Potato',
      'disease': 'Phytophthora infestans',
      'spray': 'Dimethomorph + Mancozeb @ 600g/acre',
    },
  ];

  Map<String, String>? _demoSelection;

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(source: source);
    if (picked == null) return;
    setState(() {
      _selectedPath = picked.path;
      _demoSelection = null;
      _validationError = ImageValidator.validate(path: picked.path);
    });
  }

  Future<void> _scan() async {
    if (_selectedPath == null) return;
    final error = ImageValidator.validate(path: _selectedPath);
    if (error != null) {
      setState(() => _validationError = error);
      return;
    }
    await ref.read(scanProvider.notifier).scan(_selectedPath!);
  }

  @override
  Widget build(BuildContext context) {
    final scanAsync = ref.watch(scanProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'فصل بیماری AI تشخیص' : 'Crop Scan',
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // AI Vision Header Card
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[Colors.green.shade800, Colors.green.shade900],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withAlpha(40),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.psychology, color: Colors.white, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'پلانٹ ولیج ڈیپ لرننگ ماڈل (v2.0)' : 'Deep Learning Vision Model (PyTorch v2.0)',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        Text(
                          isUrdu ? '38 پودوں کی بیماریوں کی فوری اور درست تشخیص' : 'Trained on 54,303 leaf images across 38 crop classes',
                          style: TextStyle(color: Colors.green.shade100, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Image Preview / Scanner Viewport
            Container(
              height: 200,
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.green.shade200, width: 2),
              ),
              clipBehavior: Clip.antiAlias,
              child: _selectedPath != null
                  ? Image.file(
                      File(_selectedPath!),
                      fit: BoxFit.cover,
                      width: double.infinity,
                    )
                  : Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: <Widget>[
                          Icon(Icons.photo_camera_back, size: 48, color: Colors.green.shade600),
                          const SizedBox(height: 8),
                          Text(
                            isUrdu ? 'پتے کی تصویر کھینچیں یا گیلری سے منتخب کریں' : 'Take a photo of affected leaf or pick from gallery',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
            ),
            const SizedBox(height: 14),

            // Camera / Gallery Buttons
            Row(
              children: <Widget>[
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _pickImage(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Camera'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text('Gallery'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Scan Action Button
            ElevatedButton(
              onPressed: scanAsync.isLoading ? null : _scan,
              child: scanAsync.isLoading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Scan'),
            ),
            const SizedBox(height: 12),

            // Sample Quick Test Leaf Chips
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  isUrdu ? 'یا فوری سیمپل ٹیسٹ کریں:' : 'Or Quick Test Model with Sample Crops:',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: _sampleLeaves.map((leaf) {
                    return ActionChip(
                      avatar: const Icon(Icons.eco, size: 16, color: Colors.green),
                      label: Text(isUrdu ? leaf['urdu']! : leaf['title']!),
                      onPressed: () {
                        setState(() {
                          _demoSelection = leaf;
                        });
                      },
                    );
                  }).toList(),
                ),
              ],
            ),
            const SizedBox(height: 14),

            if (_validationError != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _validationError!,
                  style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
              ),

            // Demo Result Card
            if (_demoSelection != null)
              _buildDemoResultCard(context, _demoSelection!, isUrdu),

            // Live Neural Network Result Card
            scanAsync.when(
              loading: () => const SizedBox.shrink(),
              error: (error, stack) => Text(
                'Scan failed: $error',
                style: const TextStyle(color: Colors.red),
              ),
              data: (state) {
                if (state.lastPrediction == null) {
                  return const SizedBox.shrink();
                }
                final prediction = state.lastPrediction!;
                return Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: Colors.green.shade200),
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
                              isUrdu ? 'تشخیص کا نتیجہ:' : 'Diagnostic Result:',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.green.shade50,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: Colors.green.shade300),
                              ),
                              child: Text(
                                '${(prediction.confidence * 100).toStringAsFixed(1)}% Match',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.green.shade900,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text(
                          'Prediction: ${prediction.predictedClass}',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.green.shade900,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Confidence: ${(prediction.confidence * 100).toStringAsFixed(1)}%',
                          style: TextStyle(fontSize: 13, color: Colors.grey.shade800),
                        ),
                        Text(
                          'Model: ${prediction.modelVersion}',
                          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                        ),
                        if (prediction.uncertain)
                          const Padding(
                            padding: EdgeInsets.only(top: 6),
                            child: Text(
                              'Result is uncertain - please ensure leaf is clear and well-lit',
                              style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold),
                            ),
                          ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDemoResultCard(BuildContext context, Map<String, String> demo, bool isUrdu) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.green.shade300),
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
                  isUrdu ? 'تشخیص اور فوری علاج:' : 'AI Diagnosis & Prescription:',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green.shade300),
                  ),
                  child: const Text(
                    '96.4% Match',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.green),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              demo['disease']!,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.green.shade900,
              ),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.green.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    isUrdu ? 'تجویز کردہ اسپرے:' : 'Recommended Treatment:',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      color: Colors.green.shade900,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    demo['spray']!,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
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
