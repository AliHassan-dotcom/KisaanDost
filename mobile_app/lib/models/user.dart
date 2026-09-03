import 'user_role.dart';

class User {
  const User({
    required this.id,
    required this.phone,
    required this.role,
    this.accessToken,
  });

  final String id;
  final String phone;
  final UserRole role;
  final String? accessToken;

  factory User.fromJson(Map<String, dynamic> json, {String fallbackPhone = ''}) {
    return User(
      id: json['user_id'] as String? ?? json['id'] as String? ?? '',
      phone: json['phone'] as String? ?? fallbackPhone,
      role: json['role'] != null ? UserRole.fromJson(json['role'] as String) : UserRole.farmer,
      accessToken: json['access_token'] as String?,
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'phone': phone,
        'role': role.toJson(),
        if (accessToken != null) 'access_token': accessToken,
      };

  User copyWith({
    String? id,
    String? phone,
    UserRole? role,
    String? accessToken,
  }) =>
      User(
        id: id ?? this.id,
        phone: phone ?? this.phone,
        role: role ?? this.role,
        accessToken: accessToken ?? this.accessToken,
      );
}
