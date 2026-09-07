import 'dart:convert';
import 'dart:math' as math;
import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';

import '../utils/logger.dart';
import 'secure_storage_service.dart';

class LocationData {
  const LocationData({
    required this.latitude,
    required this.longitude,
    required this.district,
    this.tehsil,
    this.village,
    this.locality,
    this.formattedAddress = '',
    this.isGps = false,
  });

  final double latitude;
  final double longitude;
  final String district;
  final String? tehsil;
  final String? village;
  final String? locality;
  final String formattedAddress;
  final bool isGps;

  String get displayTitle {
    if (locality != null && locality!.isNotEmpty && locality != district) {
      return '$locality, $district';
    }
    if (tehsil != null && tehsil!.isNotEmpty && tehsil != district) {
      return '$tehsil, $district';
    }
    return district;
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'latitude': latitude,
        'longitude': longitude,
        'district': district,
        'tehsil': tehsil,
        'village': village,
        'locality': locality,
        'formattedAddress': formattedAddress,
        'isGps': isGps,
      };

  factory LocationData.fromJson(Map<String, dynamic> json) => LocationData(
        latitude: (json['latitude'] as num?)?.toDouble() ?? 31.5497,
        longitude: (json['longitude'] as num?)?.toDouble() ?? 74.3436,
        district: json['district'] as String? ?? 'Lahore',
        tehsil: json['tehsil'] as String?,
        village: json['village'] as String?,
        locality: json['locality'] as String?,
        formattedAddress: (json['formattedAddress'] as String?) ?? (json['formatted_address'] as String?) ?? 'Lahore, Punjab',
        isGps: (json['isGps'] as bool?) ?? (json['is_gps'] as bool?) ?? false,
      );

  static const LocationData defaultLocation = LocationData(
    latitude: 31.5497,
    longitude: 74.3436,
    district: 'Lahore',
    locality: 'Model Town',
    formattedAddress: 'Model Town, Lahore, Punjab',
    isGps: false,
  );
}

class LocationService {
  LocationService({SecureStorageService? storage})
      : _storage = storage ?? const FlutterSecureStorageService();

  final SecureStorageService _storage;

  static const String _cachedLocationKey = 'cached_farm_location';

  // Master Punjab district coordinate centers (36 districts)
  static const Map<String, ({double lat, double lng})> punjabDistricts = {
    'Lahore': (lat: 31.5497, lng: 74.3436),
    'Faisalabad': (lat: 31.4504, lng: 73.1350),
    'Rawalpindi': (lat: 33.5651, lng: 73.0169),
    'Multan': (lat: 30.1575, lng: 71.5249),
    'Gujranwala': (lat: 32.1877, lng: 74.1945),
    'Sialkot': (lat: 32.4945, lng: 74.5229),
    'Bahawalpur': (lat: 29.3544, lng: 71.6911),
    'Sargodha': (lat: 32.0836, lng: 72.6711),
    'Sheikhupura': (lat: 31.7131, lng: 73.9783),
    'Rahim Yar Khan': (lat: 28.4212, lng: 70.2989),
    'Jhang': (lat: 31.2781, lng: 72.3317),
    'Dera Ghazi Khan': (lat: 30.0489, lng: 70.6455),
    'Gujrat': (lat: 32.5742, lng: 74.0754),
    'Sahiwal': (lat: 30.6682, lng: 73.1114),
    'Kasur': (lat: 31.1179, lng: 74.4460),
    'Okara': (lat: 30.8081, lng: 73.4458),
    'Muzaffargarh': (lat: 30.0754, lng: 71.1921),
    'Bahawalnagar': (lat: 29.9986, lng: 73.2536),
    'Khanewal': (lat: 30.3017, lng: 71.9321),
    'Hafizabad': (lat: 32.0679, lng: 73.6880),
    'Mandi Bahauddin': (lat: 32.5870, lng: 73.4912),
    'Toba Tek Singh': (lat: 30.9743, lng: 72.4827),
    'Vehari': (lat: 30.0419, lng: 72.3528),
    'Pakpattan': (lat: 30.3410, lng: 73.3866),
    'Layyah': (lat: 30.9613, lng: 70.9390),
    'Chakwal': (lat: 32.9328, lng: 72.8630),
    'Mianwali': (lat: 32.5853, lng: 71.5436),
    'Attock': (lat: 33.7660, lng: 72.3609),
    'Rajanpur': (lat: 29.1035, lng: 70.3250),
    'Bhakkar': (lat: 31.6253, lng: 71.0657),
    'Jhelum': (lat: 32.9405, lng: 73.7276),
    'Lodhran': (lat: 29.5405, lng: 71.6336),
    'Khushab': (lat: 32.2955, lng: 72.3528),
    'Narowal': (lat: 32.1000, lng: 74.8760),
    'Chiniot': (lat: 31.7200, lng: 72.9789),
    'Nankana Sahib': (lat: 31.4492, lng: 73.7124),
  };

  static Map<String, ({double lat, double lng})> get punjabDistrictCoordinates => punjabDistricts;

  /// Checks whether GPS location services are enabled on the device
  Future<bool> isLocationEnabled() async {
    try {
      return await Geolocator.isLocationServiceEnabled();
    } catch (e) {
      Logger.error('Error checking location service status', error: e);
      return false;
    }
  }

  /// Checks and requests location permission
  Future<LocationPermission> handlePermission() async {
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    return permission;
  }

  /// Fetches current GPS coordinates and translates them into Punjab district and locality
  Future<LocationData?> getCurrentLocation() async {
    try {
      final serviceEnabled = await isLocationEnabled();
      if (!serviceEnabled) {
        Logger.startup('Location service disabled on device');
        return await getLastKnownLocation();
      }

      final permission = await handlePermission();
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        Logger.startup('Location permission not granted: $permission');
        return await getLastKnownLocation();
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 7),
      );

      final location = await getAddressFromCoords(position.latitude, position.longitude, isGps: true);
      await saveLocation(location);
      return location;
    } catch (e, st) {
      Logger.error('Failed to get current GPS location', error: e, stackTrace: st);
      return await getLastKnownLocation();
    }
  }

  /// Converts coordinates into human-readable district, tehsil, and village
  Future<LocationData> getAddressFromCoords(
    double latitude,
    double longitude, {
    bool isGps = false,
  }) async {
    String? locality;
    String? subAdmin;
    String? street;
    String district = findClosestPunjabDistrict(latitude, longitude);

    try {
      final placemarks = await placemarkFromCoordinates(latitude, longitude);
      if (placemarks.isNotEmpty) {
        final place = placemarks.first;
        locality = place.locality?.isNotEmpty == true ? place.locality : place.subLocality;
        subAdmin = place.subAdministrativeArea;
        street = place.street;

        // Try mapping subAdministrativeArea or locality to known district
        if (subAdmin != null && subAdmin.isNotEmpty) {
          final matched = _matchDistrictName(subAdmin);
          if (matched != null) district = matched;
        } else if (locality != null && locality.isNotEmpty) {
          final matched = _matchDistrictName(locality);
          if (matched != null) district = matched;
        }
      }
    } catch (e) {
      Logger.startup('Geocoding service unavailable, using mathematical boundary matching: $e');
    }

    final formatted = <String>[
      if (locality != null && locality.isNotEmpty) locality,
      if (district.isNotEmpty && district != locality) district,
      'Punjab',
    ].join(', ');

    return LocationData(
      latitude: latitude,
      longitude: longitude,
      district: district,
      tehsil: subAdmin,
      village: street,
      locality: locality ?? district,
      formattedAddress: formatted.isNotEmpty ? formatted : '$district, Punjab',
      isGps: isGps,
    );
  }

  /// Retrieves cached farm location from secure storage
  Future<LocationData> getLastKnownLocation() async {
    try {
      final raw = await _storage.read(_cachedLocationKey);
      if (raw != null && raw.isNotEmpty) {
        final map = jsonDecode(raw) as Map<String, dynamic>;
        return LocationData.fromJson(map);
      }
    } catch (e) {
      Logger.error('Error reading cached location', error: e);
    }
    return LocationData.defaultLocation;
  }

  /// Persists chosen farm location to storage
  Future<void> saveLocation(LocationData location) async {
    try {
      final jsonStr = jsonEncode(location.toJson());
      await _storage.write(_cachedLocationKey, jsonStr);
      Logger.startup('Saved farm location to storage', location.formattedAddress);
    } catch (e) {
      Logger.error('Failed to save farm location', error: e);
    }
  }

  /// Matches string name against known Punjab districts
  String? _matchDistrictName(String rawName) {
    final clean = rawName.toLowerCase().replaceAll('district', '').trim();
    for (final district in punjabDistrictCoordinates.keys) {
      if (clean.contains(district.toLowerCase())) {
        return district;
      }
    }
    return null;
  }

  /// Mathematical Euclidean/Haversine closest Punjab district lookup
  String findClosestPunjabDistrict(double lat, double lng) {
    String closestDistrict = 'Lahore';
    double minDistance = double.infinity;

    punjabDistrictCoordinates.forEach((district, coords) {
      final d = calculateDistanceKm(lat, lng, coords.lat, coords.lng);
      if (d < minDistance) {
        minDistance = d;
        closestDistrict = district;
      }
    });

    return closestDistrict;
  }

  /// Haversine distance formula in kilometers
  double calculateDistanceKm(double lat1, double lon1, double lat2, double lon2) {
    const double p = 0.017453292519943295; // Math.PI / 180
    final double a = 0.5 -
        math.cos((lat2 - lat1) * p) / 2 +
        math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2;
    return 12742 * math.asin(math.sqrt(a)); // 2 * R; R = 6371 km
  }
}
