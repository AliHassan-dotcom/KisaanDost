import '../models/advisory.dart';
import '../models/pest_alert.dart';
import '../models/pest_source.dart';

abstract interface class PestRepository {
  Future<List<PestAlert>> getRecentAlerts({
    String? district,
    String? crop,
    String? category,
    int limit = 50,
  });

  Future<Advisory> getAdvisory({
    String? crop,
    String? pest,
    String? district,
  });

  Future<List<PestSource>> getSources();
}
