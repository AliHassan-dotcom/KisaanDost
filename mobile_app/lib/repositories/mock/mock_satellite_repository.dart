import '../../models/api_data_status.dart';
import '../../models/satellite_coverage.dart';
import '../../models/satellite_record.dart';
import '../../models/satellite_summary.dart';
import '../satellite_repository.dart';

class MockSatelliteRepository implements SatelliteRepository {
  MockSatelliteRepository({this.delay = const Duration(milliseconds: 100)});

  final Duration delay;

  static const List<String> _districts = <String>[
    'Attock', 'Bahawalnagar', 'Bahawalpur', 'Bhakkar',
    'Chakwal', 'Dera Ghazi Khan', 'Faisalabad', 'Gujranwala',
    'Gujrat', 'Hafizabad', 'Jhang', 'Jhelum',
    'Kasur', 'Khanewal', 'Khushab', 'Lahore',
    'Layyah', 'Lodhran', 'Mandi Bahauddin', 'Mianwali',
    'Multan', 'Muzaffargarh', 'Narowal', 'Okara',
    'Pakpattan', 'Rahim Yar Khan', 'Rajanpur', 'Rawalpindi',
    'Sahiwal', 'Sargodha', 'Sheikhupura', 'Sialkot',
    'Toba Tek Singh', 'Vehari',
  ];

  static const Set<String> _missingBoundaries = <String>{
    'Bhakkar', 'Jhang', 'Layyah', 'Muzaffargarh', 'Okara',
    'Bhakkar District', 'Jhang District', 'Layyah District', 'Muzaffargarh District', 'Okara District',
  };

  @override
  Future<SatelliteSummary> getSummary({
    required String district,
    required String crop,
  }) async {
    return getLatest(district: district, crop: crop);
  }

  @override
  Future<SatelliteSummary> getLatest({
    required String district,
    required String crop,
  }) async {
    await Future<void>.delayed(delay);
    final isMissing = _missingBoundaries.contains(district);

    if (isMissing) {
      return SatelliteSummary(
        district: district,
        normalizedDistrict: '$district District',
        crop: crop,
        status: ApiDataStatus.unavailable,
        reason: 'missing_authoritative_arcgis_polygon',
        healthTrend: 'boundary_unavailable',
        attentionEvidence:
            'Authoritative district boundary polygon is unavailable in provincial GIS records. Satellite zonal statistics are not estimated.',
        noCoverageFlag: true,
        qualityFlag: 'missing_authoritative_arcgis_polygon',
        satelliteSource: 'Sentinel-2 MSI / MODIS Terra Baseline',
        productId: 'COPERNICUS/S2_SR_HARMONIZED',
        periodStart: '2025-12-01',
        periodEnd: '2025-12-31',
        updatedAt: '2026-09-01T20:45:00Z',
      );
    }

    return SatelliteSummary(
      district: district,
      normalizedDistrict: '$district District',
      crop: crop,
      status: ApiDataStatus.historical,
      reason: 'clean_zonal_aggregate',
      ndvi: 0.4852,
      ndwi: -0.4215,
      ndviMedian: 0.4813,
      ndwiMedian: -0.4248,
      cloudCoverPercent: 8.0,
      validPixelCount: 15420,
      observationCount: 4,
      satelliteSource: 'Sentinel-2 MSI / MODIS Terra Baseline',
      productId: 'COPERNICUS/S2_SR_HARMONIZED',
      spatialScaleM: 100,
      periodStart: '2025-12-01',
      periodEnd: '2025-12-31',
      lastClearScene: '2025-12-31',
      healthTrend: 'normal_observation',
      attentionEvidence:
          'Monthly canopy greenness (NDVI=0.49) and moisture (NDWI=-0.42) remain within expected seasonal baseline parameters.',
      updatedAt: '2026-09-01T20:45:00Z',
    );
  }

  @override
  Future<List<SatelliteRecord>> getHistory({
    required String district,
    String? start,
    String? end,
  }) async {
    await Future<void>.delayed(delay);
    final isMissing = _missingBoundaries.contains(district);
    final records = <SatelliteRecord>[];

    for (int y = 2022; y <= 2025; y++) {
      for (int m = 1; m <= 12; m++) {
        final periodStart = '$y-${m.toString().padLeft(2, '0')}-01';
        final periodEnd = '$y-${m.toString().padLeft(2, '0')}-28';

        if (isMissing) {
          records.add(SatelliteRecord(
            year: y,
            month: m,
            district: district,
            normalizedDistrict: '$district District',
            satelliteSource: 'Sentinel-2 MSI / MODIS Terra Baseline',
            productId: 'COPERNICUS/S2_SR_HARMONIZED',
            spatialScaleM: 100,
            periodStart: periodStart,
            periodEnd: periodEnd,
            dataStatus: 'boundary_unavailable',
            noCoverageFlag: true,
            qualityFlag: 'missing_authoritative_arcgis_polygon',
            sourceProcessingTimestamp: '2026-09-01T20:45:00Z',
            attentionStatus: 'boundary_unavailable',
            attentionEvidence:
                'Authoritative district boundary polygon is unavailable in provincial GIS records.',
          ));
        } else {
          // Normal seasonal curve
          final baseNdvi = 0.35 + 0.20 * (m <= 3 ? 0.8 : (m <= 6 ? 0.2 : (m <= 9 ? 0.5 : 0.7)));
          final baseNdwi = -0.30 - 0.15 * (m >= 6 && m <= 9 ? 0.3 : 0.8);
          records.add(SatelliteRecord(
            year: y,
            month: m,
            district: district,
            normalizedDistrict: '$district District',
            ndviMean: baseNdvi,
            ndviMedian: baseNdvi * 0.99,
            ndwiMean: baseNdwi,
            ndwiMedian: baseNdwi * 1.01,
            validPixelCount: 15420,
            observationCount: 4,
            cloudOrQualityFraction: 0.08,
            satelliteSource: 'Sentinel-2 MSI / MODIS Terra Baseline',
            productId: 'COPERNICUS/S2_SR_HARMONIZED',
            spatialScaleM: 100,
            periodStart: periodStart,
            periodEnd: periodEnd,
            dataStatus: 'historical_satellite_baseline',
            noCoverageFlag: false,
            qualityFlag: 'clean_zonal_aggregate',
            sourceProcessingTimestamp: '2026-09-01T20:45:00Z',
            attentionStatus: 'normal_observation',
            attentionEvidence:
                'Monthly canopy greenness and moisture remain within expected seasonal baseline parameters.',
          ));
        }
      }
    }

    return records;
  }

  @override
  Future<SatelliteCoverage> getCoverage({required String district}) async {
    await Future<void>.delayed(delay);
    final isMissing = _missingBoundaries.contains(district);

    return SatelliteCoverage(
      district: district,
      normalizedDistrict: '$district District',
      hasAuthoritativePolygon: !isMissing,
      totalExpectedMonths: 48,
      monthsWithSatelliteData: isMissing ? 0 : 48,
      coveragePercentage: isMissing ? '0.0%' : '100.0%',
      dataStatus: isMissing ? 'boundary_unavailable' : 'historical_satellite_baseline',
      polygonSource: isMissing ? 'None' : 'ArcGIS Punjab_District_Boundaries (WGS84)',
      notes: isMissing
          ? 'Omitted from ArcGIS source GeoJSON; null metrics emitted.'
          : 'Full 48-month cloud-masked monthly baseline',
    );
  }

  @override
  Future<List<String>> getDistricts() async {
    await Future<void>.delayed(delay);
    return _districts;
  }
}
