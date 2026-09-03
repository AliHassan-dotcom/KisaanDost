import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/dashboard_provider.dart';
import '../providers/settings_provider.dart';
import '../routing/app_router.dart';
import '../widgets/crop_diagnosis_hero_card.dart';
import '../widgets/disease_hotspot_hero_card.dart';
import '../widgets/farm_insights_hero_card.dart';
import '../widgets/hero_greeting_header.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/market_prices_hero_card.dart';
import '../widgets/ndvi_vegetation_hero_card.dart';
import '../widgets/quick_actions_hub.dart';
import '../widgets/summary_metric_grid.dart';
import '../widgets/weather_forecast_hero_card.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      backgroundColor: const Color(0xFF071D12),
      appBar: KdAppBar(
        title: isUrdu ? 'کسان دوست' : 'Kisaan Dost',
        showBack: false,
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.mic, color: Color(0xFF00E676)),
            tooltip: isUrdu ? 'وائس اسسٹنٹ' : 'Voice AI',
            onPressed: () => context.push(AppRoutes.voice),
          ),
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () => context.push(AppRoutes.profile),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => context.push(AppRoutes.settings),
          ),
        ],
      ),
      floatingActionButton: _buildFloatingVoiceButton(context),
      body: Stack(
        children: <Widget>[
          // Background Sunset Wheat Field Agricultural Gradient
          Positioned.fill(
            child: Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    Color(0xFFE65100), // Sunset Amber Sky
                    Color(0xFF4E342E), // Horizon Earth
                    Color(0xFF1B5E20), // Lush Field
                    Color(0xFF071D12), // Dark Canopy Floor
                  ],
                  stops: <double>[0.0, 0.15, 0.45, 1.0],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
            ),
          ),

          // Frosted Dark Ambient Tint
          Positioned.fill(
            child: Container(
              color: const Color(0xFF04140C).withAlpha(190),
            ),
          ),

          // Main Scrollable Dashboard Content
          SafeArea(
            child: dashboardAsync.when(
              loading: () => const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00E676)),
                    ),
                    SizedBox(height: 16),
                    Text(
                      'Loading agricultural intelligence...',
                      style: TextStyle(color: Colors.white70, fontSize: 13),
                    ),
                  ],
                ),
              ),
              error: (error, stack) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: <Widget>[
                      const Icon(Icons.spa, size: 56, color: Color(0xFF00E676)),
                      const SizedBox(height: 16),
                      Text(
                        isUrdu ? 'ڈیٹا لوڈ نہیں ہو سکا' : 'Could not load dashboard',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '$error',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: Colors.white60, fontSize: 12),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: () => ref.read(dashboardProvider.notifier).refresh(),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF00E676),
                          foregroundColor: Colors.black,
                        ),
                        icon: const Icon(Icons.refresh),
                        label: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry Connection'),
                      ),
                    ],
                  ),
                ),
              ),
              data: (data) => RefreshIndicator(
                onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
                color: const Color(0xFF00E676),
                backgroundColor: const Color(0xFF0F2E1E),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 90),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      // 1. Top Header Card (Good Morning, Farm Hero 👋, Urdu Toggle, Date, Bell)
                      HeroGreetingHeader(
                        name: data.user['name'] as String?,
                        isUrdu: isUrdu,
                        onLanguageToggle: () {
                          final newLang = isUrdu ? 'en' : 'ur';
                          ref.read(settingsProvider.notifier).setLanguage(newLang);
                        },
                        onNotificationTap: () => context.push(AppRoutes.pest),
                      ),
                      const SizedBox(height: 14),

                      // 2. 2x2 Metric Summary Grid (Farm Health 92%, Weather 32.5°C, Market Rs. 3,850, Satellite 0.685)
                      SummaryMetricGrid(
                        farmHealth: data.farmHealth,
                        weather: data.weather,
                        market: data.market,
                        satellite: data.satellite,
                        isUrdu: isUrdu,
                        onFarmHealthTap: () => context.push(AppRoutes.scan),
                        onWeatherTap: () => context.push(AppRoutes.weather),
                        onMarketTap: () => context.push(AppRoutes.market),
                        onSatelliteTap: () => context.push(AppRoutes.satellite),
                      ),
                      const SizedBox(height: 14),

                      // 3. Quick Actions Hub (Urdu Voice, Scan Crop, Satellite View, Market Prices, Weather, Irrigation, Alerts)
                      QuickActionsHub(
                        isUrdu: isUrdu,
                        onVoiceTap: () => context.push(AppRoutes.voice),
                        onScanTap: () => context.push(AppRoutes.scan),
                        onSatelliteTap: () => context.push(AppRoutes.satellite),
                        onMarketTap: () => context.push(AppRoutes.market),
                        onWeatherTap: () => context.push(AppRoutes.weather),
                        onIrrigationTap: () => context.push(AppRoutes.irrigation),
                        onAlertsTap: () => context.push(AppRoutes.pest),
                      ),
                      const SizedBox(height: 14),

                      // 4. Crop Diagnosis Card (Wheat Leaf Rust Detected, Severity 65%, Confidence 92%)
                      CropDiagnosisHeroCard(
                        summary: data.farmHealth,
                        isUrdu: isUrdu,
                        onViewDetails: () => context.push(AppRoutes.scan),
                      ),
                      const SizedBox(height: 14),

                      // 5. Weather Forecast Card (5-Day Forecast, Rain 70%, Wind 18km/h, Humidity 65%, AI Advice)
                      WeatherForecastHeroCard(
                        weather: data.weather,
                        isUrdu: isUrdu,
                        onTap: () => context.push(AppRoutes.weather),
                      ),
                      const SizedBox(height: 14),

                      // 6. Market Prices (Wheat) Card (Best Market Lahore Mandi Rs. 3,850/40kg, Faisalabad, Multan)
                      MarketPricesHeroCard(
                        market: data.market,
                        isUrdu: isUrdu,
                        onTap: () => context.push(AppRoutes.market),
                      ),
                      const SizedBox(height: 14),

                      // 7. NDVI (Vegetation Health) Card (3D Field Canopy Perspective & High/Med/Low Legend)
                      NdviVegetationHeroCard(
                        satellite: data.satellite,
                        isUrdu: isUrdu,
                        onTap: () => context.push(AppRoutes.satellite),
                      ),
                      const SizedBox(height: 14),

                      // 8. Disease Hotspot (Pakistan) & Risk Model Card (Punjab Radar Nodes + 78% High Risk Gauge)
                      DiseaseHotspotHeroCard(
                        riskAssessment: data.riskAssessment,
                        isUrdu: isUrdu,
                        onTap: () => context.push(AppRoutes.pest),
                      ),
                      const SizedBox(height: 14),

                      // 9. Farm Insights Card (Live Agronomic & Irrigation Insights)
                      FarmInsightsHeroCard(
                        isUrdu: isUrdu,
                        riskAssessment: data.riskAssessment,
                        weather: data.weather,
                        farmHealth: data.farmHealth,
                        onIrrigationTap: () => context.push(AppRoutes.irrigation),
                      ),
                      const SizedBox(height: 14),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFloatingVoiceButton(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: const Color(0xFF00E676).withAlpha(120),
            blurRadius: 18,
            spreadRadius: 3,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: FloatingActionButton(
        backgroundColor: const Color(0xFF00E676),
        foregroundColor: Colors.black87,
        elevation: 6,
        onPressed: () => context.push(AppRoutes.voice),
        child: const Icon(Icons.mic, size: 28, color: Colors.black),
      ),
    );
  }
}
