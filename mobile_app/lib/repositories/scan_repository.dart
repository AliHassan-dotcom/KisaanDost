import '../models/disease_prediction.dart';

abstract interface class ScanRepository {
  Future<DiseasePrediction> scan(String filePath);
  Future<List<DiseasePrediction>> getHistory();
}
