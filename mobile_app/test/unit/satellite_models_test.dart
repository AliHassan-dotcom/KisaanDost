import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/satellite_coverage.dart';
import 'package:kisaan_dost/models/satellite_record.dart';
import 'package:kisaan_dost/models/satellite_summary.dart';
import 'package:kisaan_dost/repositories/mock/mock_satellite_repository.dart';

void main() {
  group('SatelliteSummary', () {
    test('parses valid historical JSON response correctly', () {
      final json = <String, dynamic>{
        'district': 'Lahore',
        'normalized_district': 'Lahore District',
        'crop': 'wheat',
        'status': 'historical',
        'reason': 'clean_zonal_aggregate',
        'ndvi': 0.4852,
        'ndwi': -0.4215,
        'ndvi_median': 0.4813,
        'ndwi_median': -0.4248,
        'cloud_cover_percent': 8.0,
        'valid_pixel_count': 15420,
        'observation_count': 4,
        'satellite_source': 'Sentinel-2 MSI / MODIS Terra Baseline',
        'product_id': 'COPERNICUS/S2_SR_HARMONIZED',
        'spatial_scale_m': 100,
        'period_start': '2025-12-01',
        'period_end': '2025-12-31',
        'health_trend': 'normal_observation',
        'attention_evidence': 'Monthly canopy greenness and moisture within expected baseline.',
        'no_coverage_flag': false,
        'quality_flag': 'clean_zonal_aggregate',
        'updated_at': '2026-09-01T20:45:00Z',
      };

      final summary = SatelliteSummary.fromJson(json);
      expect(summary.district, 'Lahore');
      expect(summary.status, ApiDataStatus.historical);
      expect(summary.ndvi, 0.4852);
      expect(summary.ndwi, -0.4215);
      expect(summary.isBoundaryUnavailable, isFalse);
      expect(summary.isCloudMasked, isFalse);
      expect(summary.healthTrend, 'normal_observation');
    });

    test('parses boundary unavailable JSON response', () {
      final json = <String, dynamic>{
        'district': 'Bhakkar',
        'normalized_district': 'Bhakkar District',
        'crop': 'wheat',
        'status': 'unavailable',
        'reason': 'missing_authoritative_arcgis_polygon',
        'health_trend': 'boundary_unavailable',
        'no_coverage_flag': true,
      };

      final summary = SatelliteSummary.fromJson(json);
      expect(summary.district, 'Bhakkar');
      expect(summary.status, ApiDataStatus.unavailable);
      expect(summary.ndvi, isNull);
      expect(summary.isBoundaryUnavailable, isTrue);
    });
  });

  group('SatelliteRecord', () {
    test('parses single monthly observation record', () {
      final json = <String, dynamic>{
        'year': 2024,
        'month': 3,
        'district': 'Multan',
        'normalized_district': 'Multan District',
        'ndvi_mean': 0.5123,
        'ndwi_mean': -0.3891,
        'satellite_source': 'Sentinel-2 MSI / MODIS Terra Baseline',
        'product_id': 'COPERNICUS/S2_SR_HARMONIZED',
        'spatial_scale_m': 100,
        'period_start': '2024-03-01',
        'period_end': '2024-03-31',
        'data_status': 'historical_satellite_baseline',
        'no_coverage_flag': false,
        'quality_flag': 'clean_zonal_aggregate',
        'source_processing_timestamp': '2026-09-01T20:45:00Z',
        'attention_status': 'normal_observation',
        'attention_evidence': 'Baseline observation.',
      };

      final rec = SatelliteRecord.fromJson(json);
      expect(rec.year, 2024);
      expect(rec.month, 3);
      expect(rec.label, '2024-03');
      expect(rec.hasValidMetrics, isTrue);
      expect(rec.ndviMean, 0.5123);
    });
  });

  group('SatelliteCoverage', () {
    test('parses district coverage metadata', () {
      final json = <String, dynamic>{
        'district': 'Faisalabad',
        'normalized_district': 'Faisalabad District',
        'has_authoritative_polygon': true,
        'total_expected_months': 48,
        'months_with_satellite_data': 48,
        'coverage_percentage': '100.0%',
        'data_status': 'historical_satellite_baseline',
        'polygon_source': 'ArcGIS Punjab_District_Boundaries (WGS84)',
        'notes': 'Full 48-month cloud-masked monthly baseline',
      };

      final cov = SatelliteCoverage.fromJson(json);
      expect(cov.district, 'Faisalabad');
      expect(cov.hasAuthoritativePolygon, isTrue);
      expect(cov.totalExpectedMonths, 48);
      expect(cov.coveragePercentage, '100.0%');
    });
  });

  group('MockSatelliteRepository', () {
    test('returns valid historical baseline for mapped district', () async {
      final repo = MockSatelliteRepository(delay: Duration.zero);
      final summary = await repo.getLatest(district: 'Lahore', crop: 'wheat');
      expect(summary.district, 'Lahore');
      expect(summary.status, ApiDataStatus.historical);
      expect(summary.ndvi, isNotNull);

      final history = await repo.getHistory(district: 'Lahore');
      expect(history.length, 48);
    });

    test('returns boundary unavailable for unmapped district', () async {
      final repo = MockSatelliteRepository(delay: Duration.zero);
      final summary = await repo.getLatest(district: 'Bhakkar', crop: 'wheat');
      expect(summary.district, 'Bhakkar');
      expect(summary.status, ApiDataStatus.unavailable);
      expect(summary.isBoundaryUnavailable, isTrue);
      expect(summary.ndvi, isNull);
    });
  });
}
