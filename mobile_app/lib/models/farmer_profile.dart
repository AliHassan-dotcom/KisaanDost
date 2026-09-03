class FarmerProfile {
  const FarmerProfile({
    required this.userId,
    required this.name,
    required this.phone,
    this.email,
    this.district,
    this.crop,
    this.farmSizeAcres,
    this.irrigationType,
    this.language = 'en',
  });

  final String userId;
  final String name;
  final String phone;
  final String? email;
  final String? district;
  final String? crop;
  final double? farmSizeAcres;
  final String? irrigationType;
  final String language;

  factory FarmerProfile.fromJson(Map<String, dynamic> json) {
    return FarmerProfile(
      userId: json['user_id'] as String,
      name: json['name'] as String,
      phone: json['phone'] as String,
      email: json['email'] as String?,
      district: json['district'] as String?,
      crop: json['crop'] as String?,
      farmSizeAcres: (json['farm_size_acres'] as num?)?.toDouble(),
      irrigationType: json['irrigation_type'] as String?,
      language: json['language'] as String? ?? 'en',
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'user_id': userId,
        'name': name,
        'phone': phone,
        if (email != null) 'email': email,
        if (district != null) 'district': district,
        if (crop != null) 'crop': crop,
        if (farmSizeAcres != null) 'farm_size_acres': farmSizeAcres,
        if (irrigationType != null) 'irrigation_type': irrigationType,
        'language': language,
      };

  FarmerProfile copyWith({
    String? name,
    String? email,
    String? district,
    String? crop,
    double? farmSizeAcres,
    String? irrigationType,
    String? language,
  }) =>
      FarmerProfile(
        userId: userId,
        name: name ?? this.name,
        phone: phone,
        email: email ?? this.email,
        district: district ?? this.district,
        crop: crop ?? this.crop,
        farmSizeAcres: farmSizeAcres ?? this.farmSizeAcres,
        irrigationType: irrigationType ?? this.irrigationType,
        language: language ?? this.language,
      );
}
