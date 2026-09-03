import '../../models/api_data_status.dart';
import '../../models/disease_prediction.dart';
import '../../repositories/scan_repository.dart';

class MockScanRepository implements ScanRepository {
  MockScanRepository({this.delay = const Duration(milliseconds: 800)});

  final Duration delay;
  final List<DiseasePrediction> _history = <DiseasePrediction>[];

  @override
  Future<DiseasePrediction> scan(String filePath) async {
    await Future<void>.delayed(delay);
    final prediction = const DiseasePrediction(
      scanId: 'scan_mock_001',
      predictedClass: 'healthy',
      confidence: 0.92,
      modelVersion: 'v2_mock',
      uncertain: false,
      status: ApiDataStatus.mock,
    );
    _history.insert(0, prediction);
    return prediction;
  }

  @override
  Future<List<DiseasePrediction>> getHistory() async {
    await Future<void>.delayed(delay);
    return List<DiseasePrediction>.unmodifiable(_history);
  }
}
