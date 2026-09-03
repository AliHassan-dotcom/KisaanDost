import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/notification_item.dart';
import 'package:kisaan_dost/models/notification_preferences.dart';
import 'package:kisaan_dost/providers/notification_provider.dart';
import 'package:kisaan_dost/screens/notifications_screen.dart';

class _StaticNotificationNotifier extends NotificationNotifier {
  _StaticNotificationNotifier(this._state);

  final NotificationState _state;

  @override
  Future<NotificationState> build() async {
    return _state;
  }

  @override
  void setFilter(String filter) {
    state = AsyncData(_state.copyWith(activeFilter: filter));
  }

  @override
  void toggleUnreadOnly() {
    state = AsyncData(_state.copyWith(unreadOnly: !_state.unreadOnly));
  }

  @override
  Future<void> markAsRead(String notificationId) async {
    final updated = _state.notifications.map((n) {
      if (n.id == notificationId) {
        return n.copyWith(isRead: true);
      }
      return n;
    }).toList();
    state = AsyncData(_state.copyWith(notifications: updated));
  }

  @override
  Future<void> refresh() async {}

  @override
  Future<void> evaluateAlerts() async {}
}

void main() {
  final sampleNotifications = <NotificationItem>[
    const NotificationItem(
      id: 'test_notif_1',
      userId: 'default_farmer',
      type: 'weather_alert',
      title: 'Heatwave Alert: 41.5°C in Lahore District',
      titleUr: 'شدید گرمی کی وارننگ',
      message: 'Extreme temperature recorded. Schedule evening irrigation.',
      messageUr: 'شدید گرمی ریکارڈ۔',
      severity: 'warning',
      createdAtUtc: '2026-09-01T14:30:00Z',
      isRead: false,
      sourceAttribution: 'Weather data by Open-Meteo.com under CC BY 4.0',
    ),
    const NotificationItem(
      id: 'test_notif_2',
      userId: 'default_farmer',
      type: 'market_mover',
      title: 'Market Update: Potato Fresh in Lahore',
      titleUr: 'مارکیٹ ریٹ: آلو تازہ',
      message: 'Potato Fresh rate increased to Rs. 4,200/100 Kg.',
      messageUr: 'قیمت میں اضافہ۔',
      severity: 'info',
      createdAtUtc: '2026-09-01T10:15:00Z',
      isRead: true,
      sourceAttribution: 'Market data by AMIS Punjab',
    ),
  ];

  final samplePrefs = const NotificationPreferences(
    userId: 'default_farmer',
    selectedDistrict: 'Lahore District',
    selectedMarket: 'Lahore',
    selectedCrops: <String>['Wheat', 'Cotton'],
    alertTypes: <String>['weather', 'market', 'advisory'],
    channels: <String>['in_app', 'local'],
    enableWeatherAlerts: true,
    enableMarketAlerts: true,
    enableAdvisoryReminders: true,
    heatwaveTempThreshold: 40.0,
    rainfallThresholdMm: 25.0,
    frostTempThreshold: 3.0,
    marketMoverThresholdPct: 10.0,
    fcmStatus: 'not_configured',
    updatedAtUtc: '2026-09-01T12:00:00Z',
  );

  testWidgets('NotificationsScreen renders filter chips, notification cards, and attribution', (WidgetTester tester) async {
    final state = NotificationState(
      notifications: sampleNotifications,
      preferences: samplePrefs,
      activeFilter: 'all',
      unreadOnly: false,
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          notificationProvider.overrideWith(() => _StaticNotificationNotifier(state)),
        ],
        child: const MaterialApp(
          home: NotificationsScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Notifications & Alerts'), findsOneWidget);
    expect(find.text('All (2)'), findsOneWidget);
    expect(find.text('Weather Alerts'), findsOneWidget);
    expect(find.text('Market Movers'), findsOneWidget);
    expect(find.text('Advisories'), findsOneWidget);
    expect(find.text('Unread (1)'), findsOneWidget);

    // Notification card checks
    expect(find.text('Heatwave Alert: 41.5°C in Lahore District'), findsOneWidget);
    expect(find.text('Market Update: Potato Fresh in Lahore'), findsOneWidget);
    expect(find.text('NEW'), findsOneWidget);
    expect(find.text('Weather data by Open-Meteo.com under CC BY 4.0'), findsOneWidget);
    expect(find.text('Market data by AMIS Punjab'), findsOneWidget);
    expect(find.text('Check Alerts'), findsOneWidget);
  });
}
