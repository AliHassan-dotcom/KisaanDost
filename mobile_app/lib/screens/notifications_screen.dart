import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/notification_item.dart';
import '../models/notification_preferences.dart';
import '../providers/notification_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifAsync = ref.watch(notificationProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'اطلاعات اور انتباہات' : 'Notifications & Alerts',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: isUrdu ? 'ترتیبات' : 'Preferences',
            onPressed: () => _openPreferencesSheet(context, ref, isUrdu),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: isUrdu ? 'تازہ کریں' : 'Refresh',
            onPressed: () => ref.read(notificationProvider.notifier).refresh(),
          ),
        ],
      ),
      body: notifAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Icon(Icons.notifications_off_outlined, size: 48, color: Colors.grey),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'اطلاعات لوڈ نہیں ہو سکیں' : 'Failed to load notifications',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text('$err', textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(notificationProvider.notifier).refresh(),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) => RefreshIndicator(
          onRefresh: () => ref.read(notificationProvider.notifier).refresh(),
          child: Column(
            children: <Widget>[
              // Top Filter Chips Bar
              _buildFilterBar(context, ref, state, isUrdu),
              const Divider(height: 1),

              // Notifications List
              Expanded(
                child: state.filteredNotifications.isEmpty
                    ? _buildEmptyState(context, isUrdu)
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: state.filteredNotifications.length,
                        itemBuilder: (ctx, idx) {
                          final item = state.filteredNotifications[idx];
                          return _buildNotificationCard(context, ref, item, isUrdu);
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await ref.read(notificationProvider.notifier).evaluateAlerts();
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(isUrdu ? 'انتباہات چیک کر لیے گئے ہیں' : 'Alert triggers evaluated successfully'),
                duration: const Duration(seconds: 2),
              ),
            );
          }
        },
        icon: const Icon(Icons.sync),
        label: Text(isUrdu ? 'چیک کریں' : 'Check Alerts'),
      ),
    );
  }

  Widget _buildFilterBar(BuildContext context, WidgetRef ref, NotificationState state, bool isUrdu) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: Colors.grey.shade50,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: <Widget>[
            FilterChip(
              label: Text(isUrdu ? 'سب (${state.notifications.length})' : 'All (${state.notifications.length})'),
              selected: state.activeFilter == 'all',
              onSelected: (_) => ref.read(notificationProvider.notifier).setFilter('all'),
            ),
            const SizedBox(width: 8),
            FilterChip(
              avatar: const Icon(Icons.cloud_outlined, size: 16),
              label: Text(isUrdu ? 'موسمی انتباہات' : 'Weather Alerts'),
              selected: state.activeFilter == 'weather_alert',
              onSelected: (_) => ref.read(notificationProvider.notifier).setFilter('weather_alert'),
            ),
            const SizedBox(width: 8),
            FilterChip(
              avatar: const Icon(Icons.trending_up, size: 16),
              label: Text(isUrdu ? 'مارکیٹ ریٹس' : 'Market Movers'),
              selected: state.activeFilter == 'market_mover',
              onSelected: (_) => ref.read(notificationProvider.notifier).setFilter('market_mover'),
            ),
            const SizedBox(width: 8),
            FilterChip(
              avatar: const Icon(Icons.assignment_outlined, size: 16),
              label: Text(isUrdu ? 'زرعی مشورے' : 'Advisories'),
              selected: state.activeFilter == 'advisory_reminder',
              onSelected: (_) => ref.read(notificationProvider.notifier).setFilter('advisory_reminder'),
            ),
            const SizedBox(width: 12),
            ChoiceChip(
              label: Text(isUrdu ? 'صرف غیر خواندہ' : 'Unread (${state.unreadCount})'),
              selected: state.unreadOnly,
              onSelected: (_) => ref.read(notificationProvider.notifier).toggleUnreadOnly(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotificationCard(BuildContext context, WidgetRef ref, NotificationItem item, bool isUrdu) {
    final title = isUrdu && item.titleUr.isNotEmpty ? item.titleUr : item.title;
    final message = isUrdu && item.messageUr.isNotEmpty ? item.messageUr : item.message;

    Color badgeColor;
    IconData typeIcon;
    switch (item.type) {
      case 'weather_alert':
        typeIcon = Icons.cloud;
        badgeColor = item.severity == 'critical' ? Colors.red : Colors.amber.shade800;
        break;
      case 'market_mover':
        typeIcon = Icons.trending_up;
        badgeColor = Colors.teal.shade700;
        break;
      default:
        typeIcon = Icons.eco;
        badgeColor = Colors.green.shade800;
        break;
    }

    return Card(
      elevation: item.isRead ? 1 : 3,
      margin: const EdgeInsets.only(bottom: 10),
      color: item.isRead ? Colors.white : Colors.green.shade50.withValues(alpha: 0.3),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: item.isRead ? Colors.grey.shade200 : badgeColor.withValues(alpha: 0.5),
          width: item.isRead ? 1 : 1.5,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: item.isRead ? null : () => ref.read(notificationProvider.notifier).markAsRead(item.id),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              // Header Row: Type Badge + Read Dot
              Row(
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: badgeColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Icon(typeIcon, size: 14, color: badgeColor),
                        const SizedBox(width: 4),
                        Text(
                          item.type.replaceAll('_', ' ').toUpperCase(),
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: badgeColor),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  if (!item.isRead) ...<Widget>[
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: Colors.green,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      isUrdu ? 'نیا' : 'NEW',
                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.green),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 8),

              // Title
              Text(
                title,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: item.isRead ? FontWeight.w600 : FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 4),

              // Message
              Text(
                message,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade800,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 10),

              // Footer: Provenance Attribution + Time
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Expanded(
                    child: Text(
                      item.sourceAttribution,
                      style: TextStyle(fontSize: 10, color: Colors.grey.shade600, fontStyle: FontStyle.italic),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Text(
                    item.createdAtUtc.isNotEmpty ? item.createdAtUtc.substring(0, 10) : '',
                    style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context, bool isUrdu) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          Icon(Icons.notifications_none, size: 64, color: Colors.grey.shade400),
          const SizedBox(height: 16),
          Text(
            isUrdu ? 'کوئی اطلاع نہیں ہے' : 'No notifications found',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Colors.grey.shade700),
          ),
          const SizedBox(height: 8),
          Text(
            isUrdu ? 'نئے انتباہات کیلئے "چیک کریں" دبائیں' : 'Tap "Check Alerts" to evaluate active triggers',
            style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
          ),
        ],
      ),
    );
  }

  void _openPreferencesSheet(BuildContext context, WidgetRef ref, bool isUrdu) {
    final state = ref.read(notificationProvider).value;
    final prefs = state?.preferences;
    if (prefs == null) return;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => _PreferencesModal(preferences: prefs, isUrdu: isUrdu),
    );
  }
}

class _PreferencesModal extends ConsumerStatefulWidget {
  const _PreferencesModal({required this.preferences, required this.isUrdu});

  final NotificationPreferences preferences;
  final bool isUrdu;

  @override
  ConsumerState<_PreferencesModal> createState() => _PreferencesModalState();
}

class _PreferencesModalState extends ConsumerState<_PreferencesModal> {
  late bool _weather;
  late bool _market;
  late bool _advisory;
  late bool _inAppChannel;
  late bool _localChannel;
  late bool _fcmChannel;
  late double _heatwave;
  late double _rain;
  late double _frost;

  @override
  void initState() {
    super.initState();
    _weather = widget.preferences.enableWeatherAlerts;
    _market = widget.preferences.enableMarketAlerts;
    _advisory = widget.preferences.enableAdvisoryReminders;
    _inAppChannel = widget.preferences.channels.contains('in_app');
    _localChannel = widget.preferences.channels.contains('local');
    _fcmChannel = widget.preferences.channels.contains('fcm');
    _heatwave = widget.preferences.heatwaveTempThreshold;
    _rain = widget.preferences.rainfallThresholdMm;
    _frost = widget.preferences.frostTempThreshold;
  }

  @override
  Widget build(BuildContext context) {
    final isUrdu = widget.isUrdu;
    return Padding(
      padding: EdgeInsets.only(
        top: 16,
        left: 16,
        right: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'انتباہات اور اطلاعات کی ترتیبات' : 'Alert Preferences & Channels',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
              ],
            ),
            const Divider(),

            // Section 1: Notification Delivery Channels
            Text(
              isUrdu ? 'اطلاع کے ذرائع (Delivery Channels):' : 'Delivery Channels:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            SwitchListTile(
              title: Text(isUrdu ? 'ان ایپ ان باکس (In-App Inbox)' : 'In-App Notification Inbox'),
              subtitle: Text(isUrdu ? 'ایپ کے اندر الرٹس دکھائیں' : 'Show alerts in app notification center'),
              value: _inAppChannel,
              onChanged: (val) => setState(() => _inAppChannel = val),
            ),
            SwitchListTile(
              title: Text(isUrdu ? 'مقامی اطلاعات (Local Device Notifications)' : 'Local Device Notifications'),
              subtitle: Text(isUrdu ? 'ڈیوائس پر بینر الرٹ بھیجیں' : 'Show local notification banner on trigger'),
              value: _localChannel,
              onChanged: (val) => setState(() => _localChannel = val),
            ),
            ListTile(
              title: Row(
                children: <Widget>[
                  Text(isUrdu ? 'پش اطلاعات (FCM Push)' : 'FCM Cloud Messaging'),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      widget.preferences.fcmStatus == 'configured' ? 'CONFIGURED' : 'OPTIONAL (NOT CONFIGURED)',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.grey.shade700),
                    ),
                  ),
                ],
              ),
              subtitle: Text(isUrdu ? 'کلاؤڈ پش فی الحال غیر فعال ہے' : 'Remote push skipped (local fallback active)'),
              trailing: Switch(
                value: _fcmChannel && widget.preferences.fcmStatus == 'configured',
                onChanged: widget.preferences.fcmStatus == 'configured'
                    ? (val) => setState(() => _fcmChannel = val)
                    : null,
              ),
            ),

            const Divider(),
            // Section 2: Alert Types
            Text(
              isUrdu ? 'انتباہ کی اقسام (Alert Types):' : 'Alert Trigger Categories:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            SwitchListTile(
              title: Text(isUrdu ? 'موسمی انتباہات (Weather Alerts)' : 'Weather Alerts (Open-Meteo)'),
              subtitle: Text(isUrdu ? 'شدید گرمی، بارش، اور کورا' : 'Heatwave, heavy rain, frost risk'),
              value: _weather,
              onChanged: (val) => setState(() => _weather = val),
            ),
            SwitchListTile(
              title: Text(isUrdu ? 'مارکیٹ ریٹ انتباہات (Market Movers)' : 'Market Movers (AMIS Punjab)'),
              subtitle: Text(isUrdu ? 'منڈی ریٹس میں 10%+ اتار چڑھاؤ' : 'Wholesale commodity price shifts >= 10%'),
              value: _market,
              onChanged: (val) => setState(() => _market = val),
            ),
            SwitchListTile(
              title: Text(isUrdu ? 'زرعی مشاورتی یاد دہانیاں (Advisory)' : 'Advisory Reminders (Agri Dept)'),
              subtitle: Text(isUrdu ? 'سپرے اور آبپاشی کیلئے سازگار اوقات' : 'Spray windows and irrigation timing'),
              value: _advisory,
              onChanged: (val) => setState(() => _advisory = val),
            ),

            const Divider(),
            Text(
              isUrdu ? 'انتباہ کی حدیں (Thresholds):' : 'Threshold Settings:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            const SizedBox(height: 8),

            Text('${isUrdu ? "شدید گرمی کی حد" : "Heatwave Threshold"}: ${_heatwave.toStringAsFixed(0)}°C'),
            Slider(
              value: _heatwave,
              min: 35.0,
              max: 48.0,
              divisions: 13,
              label: '${_heatwave.toStringAsFixed(0)}°C',
              onChanged: (v) => setState(() => _heatwave = v),
            ),

            Text('${isUrdu ? "بارش کی حد" : "Rainfall Threshold"}: ${_rain.toStringAsFixed(0)} mm'),
            Slider(
              value: _rain,
              min: 10.0,
              max: 60.0,
              divisions: 10,
              label: '${_rain.toStringAsFixed(0)} mm',
              onChanged: (v) => setState(() => _rain = v),
            ),

            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                final channelsList = <String>[
                  if (_inAppChannel) 'in_app',
                  if (_localChannel) 'local',
                  if (_fcmChannel && widget.preferences.fcmStatus == 'configured') 'fcm',
                ];
                final alertTypesList = <String>[
                  if (_weather) 'weather',
                  if (_market) 'market',
                  if (_advisory) 'advisory',
                ];

                final updated = widget.preferences.copyWith(
                  channels: channelsList,
                  alertTypes: alertTypesList,
                  enableWeatherAlerts: _weather,
                  enableMarketAlerts: _market,
                  enableAdvisoryReminders: _advisory,
                  heatwaveTempThreshold: _heatwave,
                  rainfallThresholdMm: _rain,
                  frostTempThreshold: _frost,
                );
                ref.read(notificationProvider.notifier).updatePreferences(updated);
                Navigator.pop(context);
              },
              child: Text(isUrdu ? 'محفوظ کریں' : 'Save Preferences'),
            ),
          ],
        ),
      ),
    );
  }
}
