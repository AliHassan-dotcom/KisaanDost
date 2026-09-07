import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/services/location_service.dart';

void main() {
  group('LocationData Model', () {
    test('serializes and deserializes to JSON correctly', () {
      const loc = LocationData(
        latitude: 31.5497,
        longitude: 74.3436,
        district: 'Lahore',
        tehsil: 'Model Town',
        village: 'Canal Bank Road',
        locality: 'Model Town',
        formattedAddress: 'Model Town, Lahore, Punjab',
        isGps: true,
      );

      final json = loc.toJson();
      expect(json['latitude'], 31.5497);
      expect(json['longitude'], 74.3436);
      expect(json['district'], 'Lahore');
      expect(json['tehsil'], 'Model Town');
      expect(json['isGps'], isTrue);

      final reconstructed = LocationData.fromJson(json);
      expect(reconstructed.latitude, 31.5497);
      expect(reconstructed.longitude, 74.3436);
      expect(reconstructed.district, 'Lahore');
      expect(reconstructed.tehsil, 'Model Town');
      expect(reconstructed.isGps, isTrue);
      expect(reconstructed.displayTitle, 'Model Town, Lahore');
    });

    test('displayTitle shows district when locality matches or is empty', () {
      const loc1 = LocationData(
        latitude: 30.1575,
        longitude: 71.5249,
        district: 'Multan',
        locality: 'Multan',
      );
      expect(loc1.displayTitle, 'Multan');

      const loc2 = LocationData(
        latitude: 31.4504,
        longitude: 73.1350,
        district: 'Faisalabad',
        tehsil: 'Jaranwala',
      );
      expect(loc2.displayTitle, 'Jaranwala, Faisalabad');
    });
  });

  group('LocationService Proximity & District Matching', () {
    final service = LocationService();

    test('correctly maps Lahore coordinates (31.5497, 74.3436) to Lahore district', () {
      final district = service.findClosestPunjabDistrict(31.5497, 74.3436);
      expect(district, 'Lahore');
    });

    test('correctly maps Multan coordinates (30.1575, 71.5249) to Multan district', () {
      final district = service.findClosestPunjabDistrict(30.1575, 71.5249);
      expect(district, 'Multan');
    });

    test('correctly maps Rawalpindi coordinates (33.5651, 73.0169) to Rawalpindi district', () {
      final district = service.findClosestPunjabDistrict(33.5651, 73.0169);
      expect(district, 'Rawalpindi');
    });

    test('correctly calculates Haversine distance in km', () {
      // Distance between Lahore (31.5497, 74.3436) and Gujranwala (32.1877, 74.1945) is ~72km
      final dist = service.calculateDistanceKm(31.5497, 74.3436, 32.1877, 74.1945);
      expect(dist, greaterThan(65));
      expect(dist, lessThan(80));
    });

    test('contains all 36 Punjab agricultural districts in master list', () {
      expect(LocationService.punjabDistricts.length, 36);
      expect(LocationService.punjabDistricts.containsKey('Lahore'), isTrue);
      expect(LocationService.punjabDistricts.containsKey('Faisalabad'), isTrue);
      expect(LocationService.punjabDistricts.containsKey('Rahim Yar Khan'), isTrue);
      expect(LocationService.punjabDistricts.containsKey('Nankana Sahib'), isTrue);
    });
  });
}
