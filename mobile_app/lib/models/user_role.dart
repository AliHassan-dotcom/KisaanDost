enum UserRole {
  farmer,
  extensionWorker,
  admin;

  static UserRole fromJson(String value) {
    switch (value) {
      case 'farmer':
        return UserRole.farmer;
      case 'extension_worker':
        return UserRole.extensionWorker;
      case 'admin':
        return UserRole.admin;
      default:
        throw FormatException('Unknown role: $value');
    }
  }

  String toJson() {
    switch (this) {
      case UserRole.farmer:
        return 'farmer';
      case UserRole.extensionWorker:
        return 'extension_worker';
      case UserRole.admin:
        return 'admin';
    }
  }

  bool get isAdmin => this == UserRole.admin;
}
