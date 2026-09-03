import '../models/market_mover.dart';
import '../models/market_price.dart';

abstract interface class MarketRepository {
  Future<List<String>> getCommodities();
  Future<MarketPrice> getSummary({required String crop, required String district});
  Future<MarketPrice> getLatest({required String commodity, String? market});
  Future<List<MarketMover>> getMovers();
  Future<List<Map<String, dynamic>>> getHistory({
    required String crop,
    required String district,
  });
}
