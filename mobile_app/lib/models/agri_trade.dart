class AgriTradeItem {
  const AgriTradeItem({
    required this.commodityGroup,
    required this.commodityName,
    required this.fiscalYear,
    required this.valueMillionUsd,
    required this.quantityThousandMt,
    required this.shareOfTradePct,
    required this.partnerCountries,
    required this.tradeType,
    required this.dataSource,
  });

  final String commodityGroup;
  final String commodityName;
  final String fiscalYear;
  final double valueMillionUsd;
  final double quantityThousandMt;
  final double shareOfTradePct;
  final String partnerCountries;
  final String tradeType;
  final String dataSource;

  factory AgriTradeItem.fromJson(Map<String, dynamic> json) {
    return AgriTradeItem(
      commodityGroup: (json['commodity_group'] as String?) ?? '',
      commodityName: (json['commodity_name'] as String?) ?? '',
      fiscalYear: (json['fiscal_year'] as String?) ?? '',
      valueMillionUsd: (json['value_million_usd'] as num?)?.toDouble() ?? 0.0,
      quantityThousandMt: (json['quantity_thousand_mt'] as num?)?.toDouble() ?? 0.0,
      shareOfTradePct: (json['share_of_trade_pct'] as num?)?.toDouble() ?? 0.0,
      partnerCountries: (json['partner_countries'] as String?) ?? '',
      tradeType: (json['trade_type'] as String?) ?? 'export',
      dataSource: (json['data_source'] as String?) ?? 'PBS / Economic Survey',
    );
  }
}

class AgriTradeSummary {
  const AgriTradeSummary({
    required this.fiscalYear,
    required this.totalAgriExportsMillionUsd,
    required this.totalAgriImportsMillionUsd,
    required this.agriTradeBalanceMillionUsd,
    required this.agriShareOfTotalNationalExportsPct,
    required this.agriShareOfTotalNationalImportsPct,
    required this.topExportCommodity,
    required this.topImportCommodity,
    required this.dataSource,
  });

  final String fiscalYear;
  final double totalAgriExportsMillionUsd;
  final double totalAgriImportsMillionUsd;
  final double agriTradeBalanceMillionUsd;
  final double agriShareOfTotalNationalExportsPct;
  final double agriShareOfTotalNationalImportsPct;
  final String topExportCommodity;
  final String topImportCommodity;
  final String dataSource;

  factory AgriTradeSummary.fromJson(Map<String, dynamic> json) {
    return AgriTradeSummary(
      fiscalYear: (json['fiscal_year'] as String?) ?? '',
      totalAgriExportsMillionUsd: (json['total_agri_exports_million_usd'] as num?)?.toDouble() ?? 0.0,
      totalAgriImportsMillionUsd: (json['total_agri_imports_million_usd'] as num?)?.toDouble() ?? 0.0,
      agriTradeBalanceMillionUsd: (json['agri_trade_balance_million_usd'] as num?)?.toDouble() ?? 0.0,
      agriShareOfTotalNationalExportsPct: (json['agri_share_of_total_national_exports_pct'] as num?)?.toDouble() ?? 0.0,
      agriShareOfTotalNationalImportsPct: (json['agri_share_of_total_national_imports_pct'] as num?)?.toDouble() ?? 0.0,
      topExportCommodity: (json['top_export_commodity'] as String?) ?? '',
      topImportCommodity: (json['top_import_commodity'] as String?) ?? '',
      dataSource: (json['data_source'] as String?) ?? 'Pakistan Economic Survey',
    );
  }
}
