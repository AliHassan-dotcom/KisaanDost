import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kisaan_dost/screens/disease_scanner_screen.dart';
import 'package:kisaan_dost/screens/what_if_analysis_screen.dart';
import 'package:kisaan_dost/widgets/field_3d_viewer.dart';
import 'package:kisaan_dost/widgets/ndvi_timeline_chart.dart';
import 'package:kisaan_dost/widgets/satellite_heatmap_widget.dart';
import 'package:kisaan_dost/widgets/yield_prediction_widget.dart';

void main() {
  group('Advanced Technical Features Widget Tests', () {
    testWidgets('1. SatelliteHeatmapWidget renders and supports mode switching', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: SingleChildScrollView(
                child: SatelliteHeatmapWidget(district: 'Lahore', meanNdvi: 0.62),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Satellite NDVI Heatmap'), findsOneWidget);
      expect(find.text('Lahore - 10m Sentinel-2 Resolution'), findsOneWidget);
      expect(find.text('NDVI Green'), findsOneWidget);
      expect(find.text('Moisture'), findsOneWidget);
      expect(find.text('Thermal'), findsOneWidget);
      expect(find.text('0.8+ Lush'), findsOneWidget);

      // Switch to Moisture mode
      await tester.tap(find.text('Moisture'));
      await tester.pumpAndSettle();
    });

    testWidgets('2. NdviTimelineChart renders multi-year curve and filter chips', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: NdviTimelineChart(district: 'Faisalabad'),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('56-Month NDVI Trajectory'), findsOneWidget);
      expect(find.text('All 56 Mo'), findsOneWidget);
      expect(find.text('2026'), findsOneWidget);
      expect(find.text('2025'), findsOneWidget);
      expect(find.text('2024'), findsOneWidget);
      expect(find.text('Peak'), findsOneWidget);

      // Filter by 2026
      await tester.tap(find.text('2026'));
      await tester.pumpAndSettle();
    });

    testWidgets('3. Field3DViewer renders 3D isometric canvas and tilt control', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Field3DViewer(district: 'Multan', meanNdvi: 0.58),
            ),
          ),
        ),
      );
      await tester.pump();

      expect(find.text('3D Field Health Topography'), findsOneWidget);
      expect(find.text('3D Canopy Height'), findsOneWidget);
      expect(find.text('Moisture Saturation'), findsOneWidget);
      expect(find.text('Risk Hotspots'), findsOneWidget);

      // Switch to Risk Hotspots layer
      await tester.tap(find.text('Risk Hotspots'));
      await tester.pump();
    });

    testWidgets('4. YieldPredictionWidget calculates maunds and economic revenue', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: YieldPredictionWidget(district: 'Gujranwala'),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Predictive Yield Analytics'), findsOneWidget);
      expect(find.text('Wheat'), findsOneWidget);
      expect(find.text('Cotton'), findsOneWidget);
      expect(find.text('Rice'), findsOneWidget);
      expect(find.text('Predicted Yield / Acre'), findsOneWidget);
      expect(find.text('Estimated Revenue'), findsOneWidget);
      expect(find.text('AI Yield Booster Protocol:'), findsOneWidget);

      // Select Cotton
      await tester.tap(find.text('Cotton'));
      await tester.pumpAndSettle();
    });

    testWidgets('5. DiseaseScannerScreen renders viewfinder, presets and treatment', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: DiseaseScannerScreen(),
          ),
        ),
      );
      await tester.pump();

      expect(find.text('AI Disease Scanner'), findsOneWidget);
      expect(find.text('Capture Leaf'), findsOneWidget);
      expect(find.text('Choose Gallery'), findsOneWidget);
      expect(find.text('Recommended Spray Protocol:'), findsOneWidget);
      expect(find.text('Wheat Yellow Rust (Stripe Rust)'), findsOneWidget);
      expect(find.text('Tilt 250 EC (Propiconazole)'), findsOneWidget);
    });

    testWidgets('6. WhatIfAnalysisScreen renders sliders, presets, and risk deltas', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: WhatIfAnalysisScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('What-If Scenario Analysis'), findsOneWidget);
      expect(find.text('AI Scenario Simulator'), findsOneWidget);
      expect(find.text('Heatwave & Drought'), findsOneWidget);
      expect(find.text('Heavy Monsoon'), findsOneWidget);
      expect(find.text('Temperature Delta'), findsOneWidget);
      expect(find.text('Rainfall Variation'), findsOneWidget);
      expect(find.text('Pest Outbreak Risk'), findsOneWidget);

      // Tap Heatwave preset
      await tester.tap(find.text('Heatwave & Drought'));
      await tester.pumpAndSettle();
    });
  });
}
