class NotificationPreferences {
  const NotificationPreferences({
    required this.userId,
    required this.selectedDistrict,
    required this.selectedMarket,
    required this.selectedCrops,
    this.alertTypes = const <String>['weather', 'market', 'advisory'],
    this.channels = const <String>['in_app', 'local'],
    required this.enableWeatherAlerts,
    required this.enableMarketAlerts,
    required this.enableAdvisoryReminders,
    required this.heatwaveTempThreshold,
    required this.rainfallThresholdMm,
    required this.frostTempThreshold,
    required this.marketMoverThresholdPct,
    this.fcmToken,
    this.fcmStatus = 'not_configured',
    required this.updatedAtUtc,
  });

  final String userId;
  final String selectedDistrict;
  final String selectedMarket;
  final List<String> selectedCrops;
  final List<String> alertTypes;
  final List<String> channels;
  final bool enableWeatherAlerts;
  final bool enableMarketAlerts;
  final bool enableAdvisoryReminders;
  final double heatwaveTempThreshold;
  final double rainfallThresholdMm;
  final double frostTempThreshold;
  final double marketMoverThresholdPct;
  final String? fcmToken;
  final String fcmStatus;
  final String updatedAtUtc;

  NotificationPreferences copyWith({
    String? userId,
    String? selectedDistrict,
    String? selectedMarket,
    List<String>? selectedCrops,
    List<String>? alertTypes,
    List<String>? channels,
    bool? enableWeatherAlerts,
    bool? enableMarketAlerts,
    bool? enableAdvisoryReminders,
    double? heatwaveTempThreshold,
    double? rainfallThresholdMm,
    double? frostTempThreshold,
    double? marketMoverThresholdPct,
    String? fcmToken,
    String? fcmStatus,
    String? updatedAtUtc,
  }) {
    return NotificationPreferences(
      userId: userId ?? this.userId,
      selectedDistrict: selectedDistrict ?? this.selectedDistrict,
      selectedMarket: selectedMarket ?? this.selectedMarket,
      selectedCrops: selectedCrops ?? this.selectedCrops,
      alertTypes: alertTypes ?? this.alertTypes,
      channels: channels ?? this.channels,
      enableWeatherAlerts: enableWeatherAlerts ?? this.enableWeatherAlerts,
      enableMarketAlerts: enableMarketAlerts ?? this.enableMarketAlerts,
      enableAdvisoryReminders: enableAdvisoryReminders ?? this.enableAdvisoryReminders,
      heatwaveTempThreshold: heatwaveTempThreshold ?? this.heatwaveTempThreshold,
      rainfallThresholdMm: rainfallThresholdMm ?? this.rainfallThresholdMm,
      frostTempThreshold: frostTempThreshold ?? this.frostTempThreshold,
      marketMoverThresholdPct: marketMoverThresholdPct ?? this.marketMoverThresholdPct,
      fcmToken: fcmToken ?? this.fcmToken,
      fcmStatus: fcmStatus ?? this.fcmStatus,
      updatedAtUtc: updatedAtUtc ?? this.updatedAtUtc,
    );
  }

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      userId: (json['user_id'] as String?) ?? 'default_farmer',
      selectedDistrict: (json['selected_district'] as String?) ?? 'Lahore District',
      selectedMarket: (json['selected_market'] as String?) ?? 'Lahore',
      selectedCrops: (json['selected_crops'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
          <String>['Wheat', 'Rice Basmati Super (New)', 'Cotton', 'Potato Fresh'],
      alertTypes: (json['alert_types'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
          <String>['weather', 'market', 'advisory'],
      channels: (json['channels'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
          <String>['in_app', 'local'],
      enableWeatherAlerts: (json['enable_weather_alerts'] as bool?) ?? true,
      enableMarketAlerts: (json['enable_market_alerts'] as bool?) ?? true,
      enableAdvisoryReminders: (json['enable_advisory_reminders'] as bool?) ?? true,
      heatwaveTempThreshold: (json['heatwave_temp_threshold'] as num?)?.toDouble() ?? 40.0,
      rainfallThresholdMm: (json['rainfall_threshold_mm'] as num?)?.toDouble() ?? 25.0,
      frostTempThreshold: (json['frost_temp_threshold'] as num?)?.toDouble() ?? 3.0,
      marketMoverThresholdPct: (json['market_mover_threshold_pct'] as num?)?.toDouble() ?? 10.0,
      fcmToken: json['fcm_token'] as String?,
      fcmStatus: (json['fcm_status'] as String?) ?? 'not_configured',
      updatedAtUtc: (json['updated_at_utc'] as String?) ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'user_id': userId,
      'selected_district': selectedDistrict,
      'selected_market': selectedMarket,
      'selected_crops': selectedCrops,
      'alert_types': alertTypes,
      'channels': channels,
      'enable_weather_alerts': enableWeatherAlerts,
      'enable_market_alerts': enableMarketAlerts,
      'enable_advisory_reminders': enableAdvisoryReminders,
      'heatwave_temp_threshold': heatwaveTempThreshold,
      'rainfall_threshold_mm': rainfallThresholdMm,
      'frost_temp_threshold': frostTempThreshold,
      'market_mover_threshold_pct': marketMoverThresholdPct,
      'fcm_token': fcmToken,
      'fcm_status': fcmStatus,
      'updated_at_utc': updatedAtUtc,
    };
  }
}
