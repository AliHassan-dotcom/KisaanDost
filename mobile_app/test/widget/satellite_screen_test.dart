import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/satellite_coverage.dart';
import 'package:kisaan_dost/models/satellite_record.dart';
import 'package:kisaan_dost/models/satellite_summary.dart';
import 'package:kisaan_dost/providers/satellite_provider.dart';
import 'package:kisaan_dost/repositories/satellite_repository.dart';
import 'package:kisaan_dost/screens/satellite_screen.dart';
import 'package:kisaan_dost/widgets/satellite_card.dart';

class _StaticSatelliteNotifier extends SatelliteNotifier {
  _StaticSatelliteNotifier(SatelliteState initialState)
      : super(_EmptyMockRepo()) {
    state = initialState;
  }

  @override
  Future<void> loadInitial() async {}

  @override
  Future<void> selectDistrict(String district) async {}

  @override
  Future<void> refresh() async {}
}

class _EmptyMockRepo extends Fake implements SatelliteRepository {}

void main() {
  final sampleSummary = SatelliteSummary(
    district: 'Lahore',
    normalizedDistrict: 'Lahore District',
    crop: 'wheat',
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
    healthTrend: 'normal_observation',
    attentionEvidence: 'Monthly canopy greenness (NDVI=0.49) and moisture (NDWI=-0.42) remain within baseline.',
    updatedAt: '2026-09-01T20:45:00Z',
  );

  final sampleHistory = <SatelliteRecord>[
    SatelliteRecord(
      year: 2025,
      month: 12,
      district: 'Lahore',
      normalizedDistrict: 'Lahore District',
      ndviMean: 0.4852,
      ndviMedian: 0.4813,
      ndwiMean: -0.4215,
      ndwiMedian: -0.4248,
      validPixelCount: 15420,
      observationCount: 4,
      cloudOrQualityFraction: 0.08,
      satelliteSource: 'Sentinel-2 MSI / MODIS Terra Baseline',
      productId: 'COPERNICUS/S2_SR_HARMONIZED',
      spatialScaleM: 100,
      periodStart: '2025-12-01',
      periodEnd: '2025-12-31',
      dataStatus: 'historical_satellite_baseline',
      noCoverageFlag: false,
      qualityFlag: 'clean_zonal_aggregate',
      sourceProcessingTimestamp: '2026-09-01T20:45:00Z',
      attentionStatus: 'normal_observation',
      attentionEvidence: 'Monthly baseline observation.',
    ),
  ];

  final sampleCoverage = const SatelliteCoverage(
    district: 'Lahore',
    normalizedDistrict: 'Lahore District',
    hasAuthoritativePolygon: true,
    totalExpectedMonths: 48,
    monthsWithSatelliteData: 48,
    coveragePercentage: '100.0%',
    dataStatus: 'historical_satellite_baseline',
    polygonSource: 'ArcGIS Punjab_District_Boundaries (WGS84)',
    notes: 'Full 48-month cloud-masked monthly baseline',
  );

  testWidgets('SatelliteScreen renders district selector and metrics', (WidgetTester tester) async {
    final state = SatelliteState(
      selectedDistrict: 'Lahore',
      selectedCrop: 'wheat',
      districts: const ['Lahore', 'Faisalabad', 'Multan'],
      summary: sampleSummary,
      history: sampleHistory,
      coverage: sampleCoverage,
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          satelliteNotifierProvider.overrideWith((ref) => _StaticSatelliteNotifier(state)),
        ],
        child: const MaterialApp(
          home: SatelliteScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Satellite Monitoring'), findsOneWidget);
    expect(find.text('District:'), findsOneWidget);
    expect(find.text('Lahore'), findsWidgets);
    expect(find.text('Normal Satellite Observation'), findsOneWidget);
    expect(find.text('0.49'), findsOneWidget);
    expect(find.text('-0.42'), findsOneWidget);
  });

  testWidgets('SatelliteScreen renders boundary unavailable warning for Bhakkar', (WidgetTester tester) async {
    final bhakkarSummary = SatelliteSummary(
      district: 'Bhakkar',
      normalizedDistrict: 'Bhakkar District',
      crop: 'wheat',
      status: ApiDataStatus.unavailable,
      reason: 'missing_authoritative_arcgis_polygon',
      healthTrend: 'boundary_unavailable',
      attentionEvidence: 'Authoritative district boundary polygon is unavailable in provincial GIS records.',
      noCoverageFlag: true,
      qualityFlag: 'missing_authoritative_arcgis_polygon',
    );

    final state = SatelliteState(
      selectedDistrict: 'Bhakkar',
      selectedCrop: 'wheat',
      districts: const ['Lahore', 'Bhakkar'],
      summary: bhakkarSummary,
      history: const [],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          satelliteNotifierProvider.overrideWith((ref) => _StaticSatelliteNotifier(state)),
        ],
        child: const MaterialApp(
          home: SatelliteScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Boundary Unavailable'), findsOneWidget);
    expect(find.text('Missing Authoritative Boundary Polygon'), findsOneWidget);
  });

  testWidgets('SatelliteCard renders in dashboard format', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SatelliteCard(summary: sampleSummary),
        ),
      ),
    );

    expect(find.textContaining('Satellite Monitoring'), findsOneWidget);
    expect(find.text('wheat · Lahore'), findsOneWidget);
    expect(find.textContaining('NDVI (Greenness): 0.49'), findsOneWidget);
    expect(find.textContaining('Observation: Normal Observation'), findsOneWidget);
  });
}
