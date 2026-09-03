/// Model representing the Punjab-wide and district-level crop-stress risk assessment and disease hotspot telemetry.
class RiskHotspot {
  const RiskHotspot({
    required this.district,
    required this.severity,
    required this.disease,
    required this.riskPercent,
    required this.lat,
    required this.lon,
  });

  final String district;
  final String severity; // High, Medium, Low
  final String disease;
  final int riskPercent;
  final double lat;
  final double lon;

  factory RiskHotspot.fromJson(Map<String, dynamic> json) {
    return RiskHotspot(
      district: json['district'] as String? ?? 'Multan',
      severity: json['severity'] as String? ?? 'High',
      disease: json['disease'] as String? ?? 'Leaf Rust',
      riskPercent: (json['risk_percent'] as num?)?.toInt() ?? 78,
      lat: (json['lat'] as num?)?.toDouble() ?? 30.1575,
      lon: (json['lon'] as num?)?.toDouble() ?? 71.5249,
    );
  }
}

class RiskAssessment {
  const RiskAssessment({
    required this.riskScore,
    required this.riskPercent,
    required this.riskLevel,
    required this.province,
    required this.district,
    required this.crop,
    required this.mainReason,
    required this.recommendedAction,
    required this.hotspots,
    this.components = const <String, dynamic>{},
  });

  final double riskScore;
  final int riskPercent;
  final String riskLevel; // High, Medium, Low
  final String province;
  final String district;
  final String crop;
  final String mainReason;
  final String recommendedAction;
  final List<RiskHotspot> hotspots;
  final Map<String, dynamic> components;

  factory RiskAssessment.fromJson(Map<String, dynamic> json) {
    final hotspotsList = (json['hotspots'] as List<dynamic>?)
            ?.map((e) => RiskHotspot.fromJson(e as Map<String, dynamic>))
            .toList() ??
        <RiskHotspot>[
          const RiskHotspot(
            district: 'Multan',
            severity: 'High',
            disease: 'Leaf Rust / Teli',
            riskPercent: 82,
            lat: 30.1575,
            lon: 71.5249,
          ),
          const RiskHotspot(
            district: 'Faisalabad',
            severity: 'Medium',
            disease: 'Yellow Rust',
            riskPercent: 68,
            lat: 31.4504,
            lon: 73.1350,
          ),
          const RiskHotspot(
            district: 'Bahawalpur',
            severity: 'High',
            disease: 'Bacterial Blight',
            riskPercent: 79,
            lat: 29.3544,
            lon: 71.6911,
          ),
        ];

    return RiskAssessment(
      riskScore: (json['risk_score'] as num?)?.toDouble() ?? 0.78,
      riskPercent: (json['risk_percent'] as num?)?.toInt() ?? 78,
      riskLevel: json['risk_level'] as String? ?? 'High',
      province: json['province'] as String? ?? 'Punjab',
      district: json['district'] as String? ?? 'Multan',
      crop: json['crop'] as String? ?? 'wheat',
      mainReason: json['main_reason'] as String? ?? 'NDWI below baseline & temperature anomaly',
      recommendedAction: json['recommended_action'] as String? ??
          'Apply prophylactic fungicide spray before rain and maintain irrigation schedule.',
      hotspots: hotspotsList,
      components: (json['components'] as Map<String, dynamic>?) ?? <String, dynamic>{},
    );
  }

  factory RiskAssessment.mockDefault() {
    return const RiskAssessment(
      riskScore: 0.78,
      riskPercent: 78,
      riskLevel: 'High',
      province: 'Punjab',
      district: 'Multan',
      crop: 'wheat',
      mainReason: 'NDWI below baseline & temperature anomaly',
      recommendedAction: 'Apply prophylactic fungicide spray before rain and maintain irrigation schedule.',
      hotspots: <RiskHotspot>[
        RiskHotspot(
          district: 'Multan',
          severity: 'High',
          disease: 'Leaf Rust / Teli',
          riskPercent: 82,
          lat: 30.1575,
          lon: 71.5249,
        ),
        RiskHotspot(
          district: 'Faisalabad',
          severity: 'Medium',
          disease: 'Yellow Rust',
          riskPercent: 68,
          lat: 31.4504,
          lon: 73.1350,
        ),
        RiskHotspot(
          district: 'Bahawalpur',
          severity: 'High',
          disease: 'Bacterial Blight',
          riskPercent: 79,
          lat: 29.3544,
          lon: 71.6911,
        ),
      ],
    );
  }
}
