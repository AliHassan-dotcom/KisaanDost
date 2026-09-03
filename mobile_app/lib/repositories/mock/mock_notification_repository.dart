import '../../models/notification_item.dart';
import '../../models/notification_preferences.dart';
import '../notification_repository.dart';

class MockNotificationRepository implements NotificationRepository {
  MockNotificationRepository({this.delay = const Duration(milliseconds: 100)});

  final Duration delay;

  NotificationPreferences _prefs = const NotificationPreferences(
    userId: 'default_farmer',
    selectedDistrict: 'Lahore District',
    selectedMarket: 'Lahore',
    selectedCrops: <String>['Wheat', 'Rice Basmati Super (New)', 'Cotton', 'Potato Fresh'],
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
    updatedAtUtc: '2026-09-01T20:00:00Z',
  );

  final List<NotificationItem> _history = <NotificationItem>[
    const NotificationItem(
      id: 'mock_notif_1',
      userId: 'default_farmer',
      type: 'weather_alert',
      title: 'Heatwave Alert: 41.5°C in Lahore District',
      titleUr: 'شدید گرمی کی وارننگ: لاہور میں درجہ حرارت 41.5°C',
      message: 'Extreme temperature recorded (41.5°C). Protect sensitive crops and schedule evening irrigation.',
      messageUr: 'شدید گرمی (41.5°C) ریکارڈ۔ فصلوں کو دھوپ کے دباؤ سے بچائیں اور شام کو پانی دیں۔',
      severity: 'warning',
      createdAtUtc: '2026-09-01T14:30:00Z',
      isRead: false,
      sourceAttribution: 'Weather data by Open-Meteo.com under CC BY 4.0',
    ),
    const NotificationItem(
      id: 'mock_notif_2',
      userId: 'default_farmer',
      type: 'market_mover',
      title: 'Market Update: Potato Fresh in Lahore',
      titleUr: 'مارکیٹ ریٹ: آلو تازہ (لاہور منڈی)',
      message: 'Potato Fresh rate increased to Rs. 4,200/100 Kg (01-Sep-2026).',
      messageUr: 'آلو تازہ کی قیمت 4,200 روپے فی 100 کلوگرام ریکارڈ (اضافہ)۔',
      severity: 'info',
      createdAtUtc: '2026-09-01T10:15:00Z',
      isRead: true,
      sourceAttribution: 'Market data by AMIS Punjab',
    ),
    const NotificationItem(
      id: 'mock_notif_3',
      userId: 'default_farmer',
      type: 'advisory_reminder',
      title: 'Optimal Spray Window: Lahore District',
      titleUr: 'سپرے کیلئے سازگار موسم: لاہور ضلع',
      message: 'Favorable calm weather (Wind: 8.5 km/h, Rain: 0.0mm). Ideal conditions for crop protection sprays.',
      messageUr: 'ہوا کی رفتار 8.5 کلومیٹر فی گھنٹہ اور بارش کا امکان نہیں۔ حفاظتی سپرے کیلئے موزوں وقت۔',
      severity: 'info',
      createdAtUtc: '2026-09-01T08:00:00Z',
      isRead: false,
      sourceAttribution: 'Advisory based on official reports',
    ),
  ];

  @override
  Future<NotificationPreferences> getPreferences() async {
    await Future<void>.delayed(delay);
    return _prefs;
  }

  @override
  Future<NotificationPreferences> updatePreferences(NotificationPreferences preferences) async {
    await Future<void>.delayed(delay);
    _prefs = preferences;
    return _prefs;
  }

  @override
  Future<List<NotificationItem>> getHistory({bool unreadOnly = false}) async {
    await Future<void>.delayed(delay);
    if (unreadOnly) {
      return _history.where((n) => !n.isRead).toList();
    }
    return List<NotificationItem>.from(_history);
  }

  @override
  Future<int> getUnreadCount() async {
    await Future<void>.delayed(delay);
    return _history.where((n) => !n.isRead).length;
  }

  @override
  Future<bool> markAsRead(String notificationId) async {
    await Future<void>.delayed(delay);
    final idx = _history.indexWhere((n) => n.id == notificationId);
    if (idx != -1) {
      _history[idx] = _history[idx].copyWith(isRead: true);
      return true;
    }
    return false;
  }

  @override
  Future<int> markMultipleRead({List<String>? notificationIds, bool markAll = false}) async {
    await Future<void>.delayed(delay);
    int count = 0;
    final idSet = Set<String>.from(notificationIds ?? <String>[]);
    for (int i = 0; i < _history.length; i++) {
      if (!_history[i].isRead && (markAll || idSet.contains(_history[i].id))) {
        _history[i] = _history[i].copyWith(isRead: true);
        count++;
      }
    }
    return count;
  }

  @override
  Future<List<NotificationItem>> evaluateNotifications() async {
    await Future<void>.delayed(delay);
    return _history.where((n) => !n.isRead).toList();
  }
}
