import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/profile_provider.dart';
import '../providers/settings_provider.dart';
import '../utils/validators.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/language_toggle.dart';

class ProfileSetupScreen extends ConsumerStatefulWidget {
  const ProfileSetupScreen({super.key});

  @override
  ConsumerState<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends ConsumerState<ProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _districtController = TextEditingController();
  final _cropController = TextEditingController();
  final _farmSizeController = TextEditingController();
  final _irrigationController = TextEditingController();
  String _language = 'en';
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _language = ref.read(settingsProvider).language;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _districtController.dispose();
    _cropController.dispose();
    _farmSizeController.dispose();
    _irrigationController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    final updates = <String, dynamic>{
      'name': _nameController.text.trim(),
      if (_emailController.text.trim().isNotEmpty)
        'email': _emailController.text.trim(),
      if (_districtController.text.trim().isNotEmpty)
        'district': _districtController.text.trim(),
      if (_cropController.text.trim().isNotEmpty)
        'crop': _cropController.text.trim(),
      if (_farmSizeController.text.trim().isNotEmpty)
        'farm_size_acres': double.tryParse(_farmSizeController.text.trim()),
      if (_irrigationController.text.trim().isNotEmpty)
        'irrigation_type': _irrigationController.text.trim(),
      'language': _language,
    };

    await ref.read(profileProvider.notifier).updateProfile(updates);
    await ref.read(settingsProvider.notifier).setLanguage(_language);
    if (mounted) context.pop();
  }

  @override
  Widget build(BuildContext context) {
    final profileAsync = ref.watch(profileProvider);
    final isUrdu = _language == 'ur';

    return Scaffold(
      appBar: KdAppBar(title: isUrdu ? 'پروفائل اور ترجیحات' : 'Profile'),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              const Text('Failed to load profile'),
              ElevatedButton(
                onPressed: () => ref.read(profileProvider.notifier).refresh(),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (profile) {
          if (!_initialized) {
            _nameController.text = profile.name;
            _emailController.text = profile.email ?? '';
            _districtController.text = profile.district ?? '';
            _cropController.text = profile.crop ?? '';
            _farmSizeController.text =
                profile.farmSizeAcres?.toString() ?? '';
            _irrigationController.text = profile.irrigationType ?? '';
            _language = profile.language.isNotEmpty ? profile.language : ref.read(settingsProvider).language;
            _initialized = true;
          }

          return Padding(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    TextFormField(
                      controller: _nameController,
                      decoration: InputDecoration(labelText: isUrdu ? 'نام' : 'Name'),
                      validator: Validators.name,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _emailController,
                      decoration: InputDecoration(labelText: isUrdu ? 'ای میل (اختیاری)' : 'Email (optional)'),
                      keyboardType: TextInputType.emailAddress,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _districtController,
                      decoration: InputDecoration(labelText: isUrdu ? 'ضلع (مثلاً ملتان، لاہور)' : 'District'),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _cropController,
                      decoration: InputDecoration(labelText: isUrdu ? 'اہم فصل (مثلاً گندم، کپاس)' : 'Primary Crop'),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _farmSizeController,
                      decoration: InputDecoration(labelText: isUrdu ? 'رقبہ (ایکڑ)' : 'Farm Size (Acres)'),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      validator: Validators.farmSize,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _irrigationController,
                      decoration: InputDecoration(labelText: isUrdu ? 'آبپاشی کا ذریعہ' : 'Irrigation Type'),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      isUrdu ? 'زبان منتخب کریں' : 'Language',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                    const SizedBox(height: 8),
                    LanguageToggle(
                      language: _language,
                      onChanged: (lang) {
                        setState(() => _language = lang);
                        ref.read(settingsProvider.notifier).setLanguage(lang);
                      },
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _save,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00E676),
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: Text(
                        isUrdu ? 'محفوظ کریں' : 'Save Profile',
                        style: const TextStyle(fontWeight: FontWeight.bold),
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
