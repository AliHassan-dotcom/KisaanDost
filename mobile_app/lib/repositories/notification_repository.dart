import '../models/notification_item.dart';
import '../models/notification_preferences.dart';

abstract interface class NotificationRepository {
  Future<NotificationPreferences> getPreferences();
  Future<NotificationPreferences> updatePreferences(NotificationPreferences preferences);
  Future<List<NotificationItem>> getHistory({bool unreadOnly = false});
  Future<int> getUnreadCount();
  Future<bool> markAsRead(String notificationId);
  Future<int> markMultipleRead({List<String>? notificationIds, bool markAll = false});
  Future<List<NotificationItem>> evaluateNotifications();
}
