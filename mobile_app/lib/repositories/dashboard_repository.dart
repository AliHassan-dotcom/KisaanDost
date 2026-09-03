import '../models/farm_health_summary.dart';
import '../models/market_price.dart';
import '../models/risk_assessment.dart';
import '../models/satellite_summary.dart';
import '../models/weather_summary.dart';

class DashboardData {
  const DashboardData({
    required this.user,
    required this.weather,
    required this.farmHealth,
    required this.market,
    required this.satellite,
    required this.quickActions,
    this.riskAssessment,
  });

  final Map<String, dynamic> user;
  final WeatherSummary weather;
  final FarmHealthSummary farmHealth;
  final MarketPrice market;
  final SatelliteSummary satellite;
  final List<Map<String, String>> quickActions;
  final RiskAssessment? riskAssessment;
}

abstract interface class DashboardRepository {
  Future<DashboardData> getDashboard();
}
