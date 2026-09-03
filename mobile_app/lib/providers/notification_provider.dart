import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/notification_item.dart';
import '../models/notification_preferences.dart';
import '../repositories/notification_repository.dart';
import 'dependency_providers.dart';

class NotificationState {
  const NotificationState({
    this.notifications = const <NotificationItem>[],
    this.preferences,
    this.activeFilter = 'all',
    this.unreadOnly = false,
  });

  final List<NotificationItem> notifications;
  final NotificationPreferences? preferences;
  final String activeFilter;
  final bool unreadOnly;

  int get unreadCount => notifications.where((n) => !n.isRead).length;

  List<NotificationItem> get filteredNotifications {
    var list = notifications;
    if (activeFilter != 'all') {
      list = list.where((n) => n.type == activeFilter).toList();
    }
    if (unreadOnly) {
      list = list.where((n) => !n.isRead).toList();
    }
    return list;
  }

  NotificationState copyWith({
    List<NotificationItem>? notifications,
    NotificationPreferences? preferences,
    String? activeFilter,
    bool? unreadOnly,
  }) {
    return NotificationState(
      notifications: notifications ?? this.notifications,
      preferences: preferences ?? this.preferences,
      activeFilter: activeFilter ?? this.activeFilter,
      unreadOnly: unreadOnly ?? this.unreadOnly,
    );
  }
}

class NotificationNotifier extends AsyncNotifier<NotificationState> {
  NotificationRepository get _repository => ref.read(notificationRepositoryProvider);

  @override
  Future<NotificationState> build() async {
    final prefs = await _repository.getPreferences();
    final items = await _repository.getHistory();
    return NotificationState(
      notifications: items,
      preferences: prefs,
    );
  }

  void setFilter(String filter) {
    final current = state.value;
    if (current == null) return;
    state = AsyncData(current.copyWith(activeFilter: filter));
  }

  void toggleUnreadOnly() {
    final current = state.value;
    if (current == null) return;
    state = AsyncData(current.copyWith(unreadOnly: !current.unreadOnly));
  }

  Future<void> markAsRead(String notificationId) async {
    final current = state.value;
    if (current == null) return;

    await _repository.markAsRead(notificationId);
    final updatedList = current.notifications.map((n) {
      if (n.id == notificationId) {
        return n.copyWith(isRead: true);
      }
      return n;
    }).toList();

    state = AsyncData(current.copyWith(notifications: updatedList));
  }

  Future<void> evaluateAlerts() async {
    final current = state.value;
    if (current == null) return;

    await _repository.evaluateNotifications();
    final freshHistory = await _repository.getHistory();
    state = AsyncData(current.copyWith(notifications: freshHistory));
  }

  Future<void> updatePreferences(NotificationPreferences newPrefs) async {
    final current = state.value;
    if (current == null) return;

    final savedPrefs = await _repository.updatePreferences(newPrefs);
    state = AsyncData(current.copyWith(preferences: savedPrefs));
  }

  Future<void> refresh() async {
    state = const AsyncLoading<NotificationState>();
    state = await AsyncValue.guard<NotificationState>(() => build());
  }
}

final notificationProvider = AsyncNotifierProvider<NotificationNotifier, NotificationState>(
  NotificationNotifier.new,
);
