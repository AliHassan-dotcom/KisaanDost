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

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['user_id'] as String? ?? json['id'] as String,
      phone: json['phone'] as String,
      role: UserRole.fromJson(json['role'] as String),
      accessToken: json['access_token'] as String?,
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'phone': phone,
        'role': role.toJson(),
        if (accessToken != null) 'access_token': accessToken,
      };

  User copyWith({String? accessToken}) => User(
        id: id,
        phone: phone,
        role: role,
        accessToken: accessToken ?? this.accessToken,
      );
}
