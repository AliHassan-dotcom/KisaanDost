import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/location_service.dart';

final locationServiceProvider = Provider<LocationService>((ref) {
  return LocationService();
});

class LocationState {
  const LocationState({
    required this.location,
    this.isLoading = false,
    this.errorMessage,
    this.isAutoDetected = false,
  });

  final LocationData location;
  final bool isLoading;
  final String? errorMessage;
  final bool isAutoDetected;

  LocationState copyWith({
    LocationData? location,
    bool? isLoading,
    String? errorMessage,
    bool? isAutoDetected,
  }) {
    return LocationState(
      location: location ?? this.location,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      isAutoDetected: isAutoDetected ?? this.isAutoDetected,
    );
  }
}

class LocationNotifier extends StateNotifier<LocationState> {
  LocationNotifier(this._locationService)
      : super(const LocationState(location: LocationData.defaultLocation)) {
    loadCachedLocation();
  }

  final LocationService _locationService;

  Future<void> loadCachedLocation() async {
    state = state.copyWith(isLoading: true);
    final cached = await _locationService.getLastKnownLocation();
    state = state.copyWith(
      location: cached,
      isLoading: false,
      isAutoDetected: cached.isGps,
    );
  }

  Future<void> detectGpsLocation() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final loc = await _locationService.getCurrentLocation();
      if (loc != null) {
        state = state.copyWith(
          location: loc,
          isLoading: false,
          isAutoDetected: true,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          errorMessage: 'Could not acquire GPS signal. Using cached location.',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> selectDistrict(String district, {String? tehsil}) async {
    state = state.copyWith(isLoading: true);
    final coords = LocationService.punjabDistrictCoordinates[district] ?? (lat: 31.5497, lng: 74.3436);
    final loc = LocationData(
      latitude: coords.lat,
      longitude: coords.lng,
      district: district,
      tehsil: tehsil,
      locality: tehsil ?? district,
      formattedAddress: tehsil != null ? '$tehsil, $district, Punjab' : '$district, Punjab',
      isGps: false,
    );
    await _locationService.saveLocation(loc);
    state = state.copyWith(
      location: loc,
      isLoading: false,
      isAutoDetected: false,
    );
  }
}

final locationProvider = StateNotifierProvider<LocationNotifier, LocationState>((ref) {
  final service = ref.watch(locationServiceProvider);
  return LocationNotifier(service);
});
