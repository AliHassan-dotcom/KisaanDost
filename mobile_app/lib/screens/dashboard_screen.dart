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
import '../widgets/quick_action_tile.dart';
import '../widgets/satellite_card.dart';
import '../widgets/weather_card.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardProvider);
    final auth = ref.watch(authProvider);
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      appBar: KdAppBar(
        title: 'Kisaan Dost',
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
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Could not load dashboard', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () => ref.read(dashboardProvider.notifier).refresh(),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: <Widget>[
                      Expanded(
                        child: GreetingHeader(
                          name: data.user['name'] as String?,
                          district: data.user['district'] as String?,
                          crop: data.user['crop'] as String?,
                        ),
                      ),
                      LanguageToggle(
                        language: settings.language,
                        onChanged: (lang) =>
                            ref.read(settingsProvider.notifier).setLanguage(lang),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  WeatherCard(
                    summary: data.weather,
                    onTap: () => context.push(AppRoutes.weather),
                  ),
                  const SizedBox(height: 12),
                  FarmHealthCard(
                    summary: data.farmHealth,
                    onTap: () => context.push(AppRoutes.scan),
                  ),
                  const SizedBox(height: 12),
                  MarketCard(
                    price: data.market,
                    onTap: () => context.push(AppRoutes.market),
                  ),
                  const SizedBox(height: 12),
                  SatelliteCard(
                    summary: data.satellite,
                    onTap: () => context.push(AppRoutes.satellite),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Quick Actions',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  GridView.count(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisCount: 4,
                    children: data.quickActions.map((action) {
                      return QuickActionTile(
                        label: action['label'] ?? '',
                        icon: action['icon'] ?? '',
                        onTap: () => _handleQuickAction(context, action['href'] ?? ''),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 24),
                  if (auth.user?.role.isAdmin ?? false)
                    ElevatedButton(
                      onPressed: () => context.push(AppRoutes.admin),
                      child: const Text('Admin Panel'),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _handleQuickAction(BuildContext context, String href) {
    final route = href.replaceAll('.html', '');
    context.push(route);
  }
}
