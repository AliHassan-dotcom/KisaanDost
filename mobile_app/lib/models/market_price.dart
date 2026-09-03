import 'api_data_status.dart';

class MarketPrice {
  const MarketPrice({
    required this.crop,
    required this.district,
    required this.status,
    this.commodityId,
    this.market,
    this.validationStatus = 'validated',
    this.unit = 'per 40kg',
    this.currentPrice,
    this.minPrice,
    this.maxPrice,
    this.fqpPrice,
    this.quantity,
    this.priceDate,
    this.sourceDisplayedDate,
    this.sourceName = 'Official AMIS Punjab',
    this.sourceUrl,
    this.retrievedAt,
    this.warning,
    this.reason,
    this.trend = 'stable',
    this.isMock = false,
    this.sources = const <String>[],
  });

  final String crop;
  final int? commodityId;
  final String district;
  final String? market;
  final ApiDataStatus status;
  final String validationStatus;
  final String unit;
  final double? currentPrice;
  final double? minPrice;
  final double? maxPrice;
  final double? fqpPrice;
  final double? quantity;
  final String? priceDate;
  final String? sourceDisplayedDate;
  final String? sourceName;
  final String? sourceUrl;
  final String? retrievedAt;
  final String? warning;
  final String? reason;
  final String trend;
  final bool isMock;
  final List<String> sources;

  bool get isStale => status == ApiDataStatus.historical || (warning != null && warning!.contains('days ago'));

  factory MarketPrice.fromJson(Map<String, dynamic> json) {
    // Handle both /market/summary and /market/latest response shapes
    final cropName = (json['crop'] as String?) ?? (json['commodity_name'] as String?) ?? 'Wheat';
    final districtName = (json['district'] as String?) ?? 'Lahore';
    final marketName = (json['market'] as String?) ?? (json['market_name'] as String?);
    final statusVal = (json['status'] as String?) ?? (json['data_status'] as String?);

    final minVal = (json['min_price'] as num?)?.toDouble() ?? (json['min_price_pkr'] as num?)?.toDouble();
    final maxVal = (json['max_price'] as num?)?.toDouble() ?? (json['max_price_pkr'] as num?)?.toDouble();
    final fqpVal = (json['fqp_price'] as num?)?.toDouble() ?? (json['fqp_price_pkr'] as num?)?.toDouble();
    final currentVal = (json['current_price'] as num?)?.toDouble() ?? fqpVal ?? maxVal ?? minVal;

    return MarketPrice(
      crop: cropName,
      commodityId: (json['commodity_id'] as num?)?.toInt(),
      district: districtName,
      market: marketName,
      status: ApiDataStatus.fromJson(statusVal),
      validationStatus: (json['validation_status'] as String?) ?? 'validated',
      unit: (json['unit'] as String?) ?? 'Rs/100Kg',
      currentPrice: currentVal,
      minPrice: minVal,
      maxPrice: maxVal,
      fqpPrice: fqpVal,
      quantity: (json['quantity'] as num?)?.toDouble(),
      priceDate: json['price_date'] as String?,
      sourceDisplayedDate: json['source_displayed_date'] as String?,
      sourceName: (json['source_name'] as String?) ?? 'Official AMIS Punjab',
      sourceUrl: json['source_url'] as String?,
      retrievedAt: json['retrieved_at'] as String?,
      warning: json['warning'] as String?,
      reason: json['reason'] as String?,
      trend: (json['trend'] as String?) ?? 'stable',
      isMock: statusVal == 'mock',
      sources: (json['sources'] as List<dynamic>?)?.cast<String>() ?? const <String>[],
    );
  }
}
