import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/dashboard_provider.dart';
import '../providers/location_provider.dart';
import '../providers/profile_provider.dart';
import '../providers/settings_provider.dart';
import '../routing/app_router.dart';
import '../services/location_service.dart';
import '../widgets/kd_app_bar.dart';

class LocationPickerScreen extends ConsumerStatefulWidget {
  const LocationPickerScreen({super.key, this.isFirstTime = false});

  final bool isFirstTime;

  @override
  ConsumerState<LocationPickerScreen> createState() => _LocationPickerScreenState();
}

class _LocationPickerScreenState extends ConsumerState<LocationPickerScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  String? _selectedDistrict;

  @override
  void initState() {
    super.initState();
    _selectedDistrict = ref.read(locationProvider).location.district;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _handleAutoDetect() async {
    final messenger = ScaffoldMessenger.of(context);
    await ref.read(locationProvider.notifier).detectGpsLocation();
    final state = ref.read(locationProvider);
    if (state.errorMessage != null) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(state.errorMessage!),
          backgroundColor: Colors.orange.shade800,
        ),
      );
    } else {
      setState(() {
        _selectedDistrict = state.location.district;
      });
      messenger.showSnackBar(
        SnackBar(
          content: Text('GPS Location detected: ${state.location.formattedAddress}'),
          backgroundColor: const Color(0xFF00E676),
        ),
      );
    }
  }

  Future<void> _saveLocation() async {
    final selected = _selectedDistrict ?? 'Lahore';
    await ref.read(locationProvider.notifier).selectDistrict(selected);

    // Sync with profile provider if available
    try {
      await ref.read(profileProvider.notifier).updateProfile({
        'district': selected,
      });
    } catch (_) {}

    // Refresh dashboard for new location
    ref.read(dashboardProvider.notifier).refresh();

    if (mounted) {
      if (widget.isFirstTime) {
        context.go(AppRoutes.dashboard);
      } else {
        context.pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider);
    final isUrdu = ref.watch(settingsProvider).language == 'ur';
    final districts = LocationService.punjabDistrictCoordinates.keys.toList()
      ..sort((a, b) => a.compareTo(b));

    final filteredDistricts = _searchQuery.isEmpty
        ? districts
        : districts
            .where((d) => d.toLowerCase().contains(_searchQuery.toLowerCase()))
            .toList();

    return Scaffold(
      backgroundColor: const Color(0xFF071D12),
      appBar: KdAppBar(
        title: isUrdu ? 'کھیت کی لوکیشن (GPS)' : 'Farm Location & GPS',
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              // Header Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF1B5E20), Color(0xFF0F2E1E)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF00E676).withAlpha(60)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00E676).withAlpha(40),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.my_location, color: Color(0xFF00E676), size: 24),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                isUrdu ? 'موجودہ فارم لوکیشن' : 'Current Farm Location',
                                style: const TextStyle(color: Colors.white70, fontSize: 13),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                locationState.location.formattedAddress,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: <Widget>[
                        _buildCoordinateChip(
                          'Lat: ${locationState.location.latitude.toStringAsFixed(4)}',
                          Icons.explore,
                        ),
                        const SizedBox(width: 8),
                        _buildCoordinateChip(
                          'Lng: ${locationState.location.longitude.toStringAsFixed(4)}',
                          Icons.navigation,
                        ),
                        const SizedBox(width: 8),
                        _buildCoordinateChip(
                          locationState.isAutoDetected ? 'GPS Active' : 'Manual',
                          locationState.isAutoDetected ? Icons.gps_fixed : Icons.edit_location_alt,
                          color: locationState.isAutoDetected ? const Color(0xFF00E676) : Colors.orangeAccent,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // Auto Detect GPS Button
              ElevatedButton.icon(
                onPressed: locationState.isLoading ? null : _handleAutoDetect,
                icon: locationState.isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
                        ),
                      )
                    : const Icon(Icons.gps_fixed, color: Colors.black),
                label: Text(
                  locationState.isLoading
                      ? (isUrdu ? 'لوکیشن تلاش کی جا رہی ہے...' : 'Acquiring GPS Signal...')
                      : (isUrdu ? 'موجودہ GPS لوکیشن حاصل کریں' : 'Use Current GPS Location'),
                  style: const TextStyle(
                    color: Colors.black,
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00E676),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 20),

              // Divider with OR
              Row(
                children: <Widget>[
                  const Expanded(child: Divider(color: Colors.white24)),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      isUrdu ? 'یا ضلع منتخب کریں' : 'OR SELECT DISTRICT',
                      style: const TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const Expanded(child: Divider(color: Colors.white24)),
                ],
              ),
              const SizedBox(height: 16),

              // Search Bar
              TextField(
                controller: _searchController,
                onChanged: (value) => setState(() => _searchQuery = value),
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: isUrdu ? 'ضلع یا تحصیل تلاش کریں...' : 'Search Punjab district or tehsil...',
                  hintStyle: const TextStyle(color: Colors.white38),
                  prefixIcon: const Icon(Icons.search, color: Color(0xFF00E676)),
                  filled: true,
                  fillColor: const Color(0xFF0F2E1E),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: Colors.green.withAlpha(50)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: Colors.green.withAlpha(50)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Color(0xFF00E676)),
                  ),
                ),
              ),
              const SizedBox(height: 14),

              // Districts Grid / List
              Container(
                constraints: const BoxConstraints(maxHeight: 280),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F2E1E),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.green.withAlpha(50)),
                ),
                child: ListView.separated(
                  shrinkWrap: true,
                  padding: const EdgeInsets.all(8),
                  itemCount: filteredDistricts.length,
                  separatorBuilder: (context, index) => const Divider(color: Colors.white10, height: 1),
                  itemBuilder: (context, index) {
                    final district = filteredDistricts[index];
                    final isSelected = _selectedDistrict == district;
                    final coords = LocationService.punjabDistrictCoordinates[district];

                    return ListTile(
                      dense: true,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      tileColor: isSelected ? const Color(0xFF00E676).withAlpha(40) : Colors.transparent,
                      leading: Icon(
                        isSelected ? Icons.check_circle : Icons.location_city,
                        color: isSelected ? const Color(0xFF00E676) : Colors.white60,
                        size: 20,
                      ),
                      title: Text(
                        district,
                        style: TextStyle(
                          color: isSelected ? const Color(0xFF00E676) : Colors.white,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          fontSize: 14,
                        ),
                      ),
                      subtitle: coords != null
                          ? Text(
                              '${coords.lat.toStringAsFixed(2)}°N, ${coords.lng.toStringAsFixed(2)}°E',
                              style: const TextStyle(color: Colors.white38, fontSize: 11),
                            )
                          : null,
                      trailing: isSelected
                          ? const Icon(Icons.radio_button_checked, color: Color(0xFF00E676), size: 18)
                          : const Icon(Icons.radio_button_unchecked, color: Colors.white38, size: 18),
                      onTap: () {
                        setState(() {
                          _selectedDistrict = district;
                        });
                      },
                    );
                  },
                ),
              ),
              const SizedBox(height: 20),

              // Confirm / Save Button
              ElevatedButton(
                onPressed: _saveLocation,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1B5E20),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: const BorderSide(color: Color(0xFF00E676)),
                  ),
                ),
                child: Text(
                  isUrdu ? 'لوکیشن محفوظ کریں اور ڈیش بورڈ دیکھیں' : 'Confirm & Save Farm Location',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCoordinateChip(String label, IconData icon, {Color color = Colors.white70}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, color: color, size: 12),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
