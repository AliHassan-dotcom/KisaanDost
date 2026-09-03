class MarketMover {
  const MarketMover({
    required this.commodityId,
    required this.commodityName,
    required this.marketName,
    required this.currentPricePkr,
    this.previousPricePkr,
    this.priceChangePkr,
    this.priceChangePct,
    this.unit = 'Rs/100Kg',
    required this.priceDate,
    this.direction = 'stable',
  });

  final int commodityId;
  final String commodityName;
  final String marketName;
  final double currentPricePkr;
  final double? previousPricePkr;
  final double? priceChangePkr;
  final double? priceChangePct;
  final String unit;
  final String priceDate;
  final String direction;

  factory MarketMover.fromJson(Map<String, dynamic> json) {
    return MarketMover(
      commodityId: (json['commodity_id'] as num?)?.toInt() ?? 0,
      commodityName: (json['commodity_name'] as String?) ?? '',
      marketName: (json['market_name'] as String?) ?? '',
      currentPricePkr: (json['current_price_pkr'] as num?)?.toDouble() ?? 0.0,
      previousPricePkr: (json['previous_price_pkr'] as num?)?.toDouble(),
      priceChangePkr: (json['price_change_pkr'] as num?)?.toDouble(),
      priceChangePct: (json['price_change_pct'] as num?)?.toDouble(),
      unit: (json['unit'] as String?) ?? 'Rs/100Kg',
      priceDate: (json['price_date'] as String?) ?? '',
      direction: (json['direction'] as String?) ?? 'stable',
    );
  }
}
