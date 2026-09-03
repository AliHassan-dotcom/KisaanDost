import '../models/agri_gdp.dart';
import '../models/agri_trade.dart';
import '../models/land_utilization.dart';
import '../models/water_availability.dart';

abstract interface class AgriStatsRepository {
  Future<List<LandUtilization>> getLandUtilization({String? district});
  Future<List<WaterAvailability>> getWaterAvailability({String? district});
  Future<List<AgriGdp>> getGdp({String? province});
  Future<List<AgriTradeItem>> getExports({String? commodity});
  Future<List<AgriTradeItem>> getImports({String? commodity});
  Future<List<AgriTradeSummary>> getTradeSummary();
}

