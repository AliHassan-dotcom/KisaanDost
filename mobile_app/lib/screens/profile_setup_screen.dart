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

    return Scaffold(
      appBar: const KdAppBar(title: 'Profile'),
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
          _nameController.text = profile.name;
          _emailController.text = profile.email ?? '';
          _districtController.text = profile.district ?? '';
          _cropController.text = profile.crop ?? '';
          _farmSizeController.text =
              profile.farmSizeAcres?.toString() ?? '';
          _irrigationController.text = profile.irrigationType ?? '';
          _language = profile.language;

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
                      decoration: const InputDecoration(labelText: 'Name'),
                      validator: Validators.name,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(labelText: 'Email (optional)'),
                      keyboardType: TextInputType.emailAddress,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _districtController,
                      decoration: const InputDecoration(labelText: 'District'),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _cropController,
                      decoration: const InputDecoration(labelText: 'Crop'),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _farmSizeController,
                      decoration: const InputDecoration(
                        labelText: 'Farm size (acres)',
                      ),
                      keyboardType: TextInputType.number,
                      validator: Validators.farmSize,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _irrigationController,
                      decoration: const InputDecoration(
                        labelText: 'Irrigation type',
                      ),
                    ),
                    const SizedBox(height: 16),
                    LanguageToggle(
                      language: _language,
                      onChanged: (lang) => setState(() => _language = lang),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _save,
                      child: const Text('Save Profile'),
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
