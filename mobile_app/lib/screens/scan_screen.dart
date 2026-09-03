import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../providers/scan_provider.dart';
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

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(source: source);
    if (picked == null) return;
    setState(() {
      _selectedPath = picked.path;
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

    return Scaffold(
      appBar: const KdAppBar(title: 'Crop Scan'),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            if (_selectedPath != null)
              Expanded(
                child: Image.file(
                  File(_selectedPath!),
                  fit: BoxFit.cover,
                ),
              )
            else
              Expanded(
                child: Container(
                  color: Colors.grey.shade200,
                  child: const Center(child: Text('No image selected')),
                ),
              ),
            const SizedBox(height: 16),
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
                  child: ElevatedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text('Gallery'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (_validationError != null)
              Text(
                _validationError!,
                style: const TextStyle(color: Colors.red),
                textAlign: TextAlign.center,
              ),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: scanAsync.isLoading ? null : _scan,
              child: scanAsync.isLoading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Scan'),
            ),
            const SizedBox(height: 16),
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
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Prediction: ${prediction.predictedClass}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Text(
                          'Confidence: ${(prediction.confidence * 100).toStringAsFixed(1)}%',
                        ),
                        Text('Model: ${prediction.modelVersion}'),
                        if (prediction.uncertain)
                          const Text(
                            'Uncertain result',
                            style: TextStyle(color: Colors.orange),
                          ),
                        if (prediction.warning != null)
                          Text('Warning: ${prediction.warning}'),
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
}
