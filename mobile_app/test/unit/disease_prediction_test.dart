import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/disease_prediction.dart';

void main() {
  group('DiseasePrediction.fromJson', () {
    test('parses live backend response envelope and scanned_at timestamp', () {
      final prediction = DiseasePrediction.fromJson(const <String, dynamic>{
        'success': true,
        'data': <String, dynamic>{
          'scan_id': 'scan_000001',
          'user_id': 'user_000001',
          'image_path': 'app_data/uploads/test.jpg',
          'predicted_class': 'Tomato_Septoria_leaf_spot',
          'confidence': 0.6249,
          'model_version': 'plantvillage_v2',
          'uncertain': true,
          'warning':
              'Low confidence prediction. Please consult an extension worker for confirmation.',
          'scanned_at': '2026-09-01T20:10:00.000000+00:00',
        },
      });

      expect(prediction.scanId, 'scan_000001');
      expect(prediction.predictedClass, 'Tomato_Septoria_leaf_spot');
      expect(prediction.confidence, 0.6249);
      expect(prediction.modelVersion, 'plantvillage_v2');
      expect(prediction.uncertain, isTrue);
      expect(
        prediction.warning,
        'Low confidence prediction. Please consult an extension worker for confirmation.',
      );
      expect(prediction.status, ApiDataStatus.live);
      expect(prediction.createdAt, '2026-09-01T20:10:00.000000+00:00');
    });

    test('parses direct map with created_at fallback', () {
      final prediction = DiseasePrediction.fromJson(const <String, dynamic>{
        'scan_id': 'scan_000002',
        'predicted_class': 'Pepper__bell___healthy',
        'confidence': 0.9850,
        'model_version': 'plantvillage_v2',
        'uncertain': false,
        'status': 'live',
        'created_at': '2026-09-01T12:00:00Z',
      });

      expect(prediction.scanId, 'scan_000002');
      expect(prediction.predictedClass, 'Pepper__bell___healthy');
      expect(prediction.confidence, 0.9850);
      expect(prediction.modelVersion, 'plantvillage_v2');
      expect(prediction.uncertain, isFalse);
      expect(prediction.warning, isNull);
      expect(prediction.status, ApiDataStatus.live);
      expect(prediction.createdAt, '2026-09-01T12:00:00Z');
    });

    test('uses safe defaults for missing fields', () {
      final prediction = DiseasePrediction.fromJson(const <String, dynamic>{});

      expect(prediction.scanId, '');
      expect(prediction.predictedClass, 'unknown');
      expect(prediction.confidence, 0.0);
      expect(prediction.modelVersion, 'unknown');
      expect(prediction.uncertain, isFalse);
      expect(prediction.warning, isNull);
      expect(prediction.status, ApiDataStatus.unavailable);
      expect(prediction.createdAt, isNull);
    });
  });
}
