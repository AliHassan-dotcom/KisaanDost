import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/notification_item.dart';
import 'package:kisaan_dost/models/notification_preferences.dart';
import 'package:kisaan_dost/repositories/mock/mock_notification_repository.dart';

void main() {
  group('NotificationItem', () {
    test('parses NotificationItem JSON correctly', () {
      final json = <String, dynamic>{
        'id': 'test_notif_1',
        'user_id': 'farmer_123',
        'type': 'weather_alert',
        'title': 'Heatwave Alert',
        'title_ur': 'گرمی کی وارننگ',
        'message': 'High temperature expected.',
        'message_ur': 'شدید گرمی کا امکان ہے۔',
        'severity': 'warning',
        'created_at_utc': '2026-09-01T12:00:00Z',
        'is_read': false,
        'source_attribution': 'Weather data by Open-Meteo.com under CC BY 4.0',
        'metadata': <String, dynamic>{'temp': 42.0},
      };

      final item = NotificationItem.fromJson(json);
      expect(item.id, 'test_notif_1');
      expect(item.userId, 'farmer_123');
      expect(item.type, 'weather_alert');
      expect(item.title, 'Heatwave Alert');
      expect(item.severity, 'warning');
      expect(item.isRead, false);
      expect(item.sourceAttribution, 'Weather data by Open-Meteo.com under CC BY 4.0');
    });
  });

  group('NotificationPreferences', () {
    test('parses and serializes NotificationPreferences JSON correctly', () {
      final json = <String, dynamic>{
        'user_id': 'farmer_123',
        'selected_district': 'Lahore District',
        'selected_market': 'Lahore',
        'selected_crops': <String>['Wheat', 'Cotton'],
        'alert_types': <String>['weather', 'market'],
        'channels': <String>['in_app', 'local'],
        'enable_weather_alerts': true,
        'enable_market_alerts': true,
        'enable_advisory_reminders': false,
        'heatwave_temp_threshold': 42.0,
        'rainfall_threshold_mm': 30.0,
        'frost_temp_threshold': 2.0,
        'market_mover_threshold_pct': 15.0,
        'fcm_token': 'test_fcm_token',
        'fcm_status': 'not_configured',
        'updated_at_utc': '2026-09-01T12:00:00Z',
      };

      final prefs = NotificationPreferences.fromJson(json);
      expect(prefs.userId, 'farmer_123');
      expect(prefs.selectedDistrict, 'Lahore District');
      expect(prefs.selectedCrops, <String>['Wheat', 'Cotton']);
      expect(prefs.channels, <String>['in_app', 'local']);
      expect(prefs.enableAdvisoryReminders, false);
      expect(prefs.heatwaveTempThreshold, 42.0);

      final outJson = prefs.toJson();
      expect(outJson['user_id'], 'farmer_123');
      expect(outJson['heatwave_temp_threshold'], 42.0);
    });
  });

  group('MockNotificationRepository', () {
    test('returns mock preferences, unread count, and history', () async {
      final repo = MockNotificationRepository(delay: Duration.zero);
      final prefs = await repo.getPreferences();
      expect(prefs.userId, 'default_farmer');
      expect(prefs.selectedDistrict, 'Lahore District');

      final unreadCount = await repo.getUnreadCount();
      expect(unreadCount, greaterThanOrEqualTo(1));

      final history = await repo.getHistory();
      expect(history.length, greaterThanOrEqualTo(2));
      expect(history.first.type, 'weather_alert');

      final markOk = await repo.markAsRead('mock_notif_1');
      expect(markOk, true);

      final unreadOnly = await repo.getHistory(unreadOnly: true);
      expect(unreadOnly.any((n) => n.id == 'mock_notif_1'), false);

      final markedCount = await repo.markMultipleRead(markAll: true);
      expect(markedCount, greaterThanOrEqualTo(1));
    });
  });
}
