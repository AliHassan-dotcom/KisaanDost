import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';
import '../models/notification_item.dart';
import '../models/notification_preferences.dart';
import '../services/http_client.dart';
import '../utils/error_mapper.dart';
import 'notification_repository.dart';

class NotificationRepositoryImpl implements NotificationRepository {
  const NotificationRepositoryImpl({required this._client});

  final HttpClient _client;

  @override
  Future<NotificationPreferences> getPreferences() async {
    final uri = AppConfig.apiUri('/notifications/preferences');
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final prefJson = (data['preferences'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    return NotificationPreferences.fromJson(prefJson);
  }

  @override
  Future<NotificationPreferences> updatePreferences(NotificationPreferences preferences) async {
    final uri = AppConfig.apiUri('/notifications/preferences');
    final response = await _client.put(
      uri,
      body: preferences.toJson(),
    );
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final prefJson = (data['preferences'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    return NotificationPreferences.fromJson(prefJson);
  }

  @override
  Future<List<NotificationItem>> getHistory({bool unreadOnly = false}) async {
    final uri = AppConfig.apiUri('/notifications/history').replace(
      queryParameters: unreadOnly ? <String, String>{'unread_only': 'true'} : null,
    );
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['notifications'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(NotificationItem.fromJson).toList(growable: false);
  }

  @override
  Future<int> getUnreadCount() async {
    final uri = AppConfig.apiUri('/notifications/unread-count');
    final response = await _client.get(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    return (data['unread_count'] as num?)?.toInt() ?? 0;
  }

  @override
  Future<bool> markAsRead(String notificationId) async {
    final uri = AppConfig.apiUri('/notifications/$notificationId/read');
    final response = await _client.post(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return (body['success'] as bool?) ?? false;
  }

  @override
  Future<int> markMultipleRead({List<String>? notificationIds, bool markAll = false}) async {
    final uri = AppConfig.apiUri('/notifications/mark-read');
    final response = await _client.put(
      uri,
      body: <String, dynamic>{
        'notification_ids': notificationIds,
        'mark_all': markAll,
      },
    );
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    return (data['marked_count'] as num?)?.toInt() ?? 0;
  }

  @override
  Future<List<NotificationItem>> evaluateNotifications() async {
    final uri = AppConfig.apiUri('/notifications/evaluate');
    final response = await _client.post(uri);
    if (response.statusCode != HttpStatus.ok) {
      throw ApiException.fromResponse(response);
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final data = (body['data'] as Map<String, dynamic>?) ?? const <String, dynamic>{};
    final list = (data['new_alerts'] as List<dynamic>?) ?? <dynamic>[];
    return list.whereType<Map<String, dynamic>>().map(NotificationItem.fromJson).toList(growable: false);
  }
}
