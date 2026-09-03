import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../providers/dashboard_provider.dart';
import '../providers/settings_provider.dart';
import '../routing/app_router.dart';
import '../widgets/farm_health_card.dart';
import '../widgets/greeting_header.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/language_toggle.dart';
import '../widgets/market_card.dart';
import '../widgets/satellite_card.dart';
import '../widgets/weather_card.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardProvider);
    final auth = ref.watch(authProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'کسان دوست' : 'Kisaan Dost',
        showBack: false,
        actions: <Widget>[
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
      body: dashboardAsync.when(
        loading: () => const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Loading agricultural intelligence...'),
            ],
          ),
        ),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                Icon(Icons.spa, size: 56, color: Colors.green.shade700),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'ڈیٹا لوڈ نہیں ہو سکا' : 'Could not load dashboard',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  '$error',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () => ref.read(dashboardProvider.notifier).refresh(),
                  icon: const Icon(Icons.refresh),
                  label: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry Connection'),
                ),
              ],
            ),
          ),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                // Farmer Greeting & Language Selector Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: <Color>[
                        Colors.green.shade50,
                        Colors.white,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: <Widget>[
                      Expanded(
                        child: GreetingHeader(
                          name: data.user['name'] as String?,
                          district: data.user['district'] as String?,
                          crop: data.user['crop'] as String?,
                          isUrdu: isUrdu,
                        ),
                      ),
                      LanguageToggle(
                        language: settings.language,
                        onChanged: (lang) =>
                            ref.read(settingsProvider.notifier).setLanguage(lang),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Live Weather Card
                WeatherCard(
                  summary: data.weather,
                  isUrdu: isUrdu,
                  onTap: () => context.push(AppRoutes.weather),
                ),
                const SizedBox(height: 12),

                // Crop Disease AI Diagnostic Card
                FarmHealthCard(
                  summary: data.farmHealth,
                  isUrdu: isUrdu,
                  onTap: () => context.push(AppRoutes.scan),
                ),
                const SizedBox(height: 12),

                // Mandi Market Rates Card
                MarketCard(
                  price: data.market,
                  isUrdu: isUrdu,
                  onTap: () => context.push(AppRoutes.market),
                ),
                const SizedBox(height: 12),

                // Satellite Vegetation NDVI/NDWI Card
                SatelliteCard(
                  summary: data.satellite,
                  isUrdu: isUrdu,
                  onTap: () => context.push(AppRoutes.satellite),
                ),
                const SizedBox(height: 20),

                // Quick Action Hub Header
                Row(
                  children: <Widget>[
                    Icon(Icons.dashboard_customize, size: 20, color: Colors.green.shade800),
                    const SizedBox(width: 8),
                    Text(
                      isUrdu ? 'فوری زرعی سہولیات' : 'Quick Actions',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.green.shade900,
                          ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // 6 Core Agricultural Action Tiles
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 3,
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 0.95,
                  children: <Widget>[
                    _buildServiceTile(
                      context,
                      icon: Icons.camera_alt,
                      color: Colors.green,
                      label: isUrdu ? 'فصل اسکین' : 'Crop Scan',
                      sublabel: isUrdu ? 'AI تشخیص' : 'AI Disease',
                      onTap: () => context.push(AppRoutes.scan),
                    ),
                    _buildServiceTile(
                      context,
                      icon: Icons.wb_sunny,
                      color: Colors.orange,
                      label: isUrdu ? 'موسم' : 'Weather',
                      sublabel: isUrdu ? 'پیشگوئی' : 'Forecast',
                      onTap: () => context.push(AppRoutes.weather),
                    ),
                    _buildServiceTile(
                      context,
                      icon: Icons.trending_up,
                      color: Colors.green,
                      label: isUrdu ? 'منڈی ریٹس' : 'Mandi Rates',
                      sublabel: isUrdu ? 'روزانہ قیمت' : 'Daily Prices',
                      onTap: () => context.push(AppRoutes.market),
                    ),
                    _buildServiceTile(
                      context,
                      icon: Icons.satellite_alt,
                      color: Colors.teal,
                      label: isUrdu ? 'سیٹلائٹ' : 'Satellite',
                      sublabel: isUrdu ? 'NDVI ہریالی' : 'Canopy Health',
                      onTap: () => context.push(AppRoutes.satellite),
                    ),
                    _buildServiceTile(
                      context,
                      icon: Icons.pest_control,
                      color: Colors.deepOrange,
                      label: isUrdu ? 'کیڑے مار ادویات' : 'Pest Advisory',
                      sublabel: isUrdu ? 'ماہرانہ مشورہ' : 'Punjab RAG',
                      onTap: () => context.push(AppRoutes.pest),
                    ),
                    _buildServiceTile(
                      context,
                      icon: Icons.water_drop,
                      color: Colors.blue,
                      label: isUrdu ? 'آبپاشی شیڈول' : 'Irrigation',
                      sublabel: isUrdu ? 'نمی کنٹرول' : 'Soil Water',
                      onTap: () => context.push(AppRoutes.irrigation),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                if (auth.user?.role.isAdmin ?? false)
                  ElevatedButton.icon(
                    onPressed: () => context.push(AppRoutes.admin),
                    icon: const Icon(Icons.admin_panel_settings),
                    label: const Text('Admin Panel'),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildServiceTile(
    BuildContext context, {
    required IconData icon,
    required MaterialColor color,
    required String label,
    required String sublabel,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: color.shade100, width: 1),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: color.shade50,
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: color.shade800, size: 22),
              ),
              const SizedBox(height: 6),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              Text(
                sublabel,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
