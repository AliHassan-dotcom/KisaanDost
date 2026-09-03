import '../models/satellite_coverage.dart';
import '../models/satellite_record.dart';
import '../models/satellite_summary.dart';

abstract interface class SatelliteRepository {
  Future<SatelliteSummary> getSummary({required String district, required String crop});
  Future<SatelliteSummary> getLatest({required String district, required String crop});
  Future<List<SatelliteRecord>> getHistory({required String district, String? start, String? end});
  Future<SatelliteCoverage> getCoverage({required String district});
  Future<List<String>> getDistricts();
}
