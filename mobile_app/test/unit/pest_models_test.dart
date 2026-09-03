import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/advisory.dart';
import 'package:kisaan_dost/models/api_data_status.dart';
import 'package:kisaan_dost/models/pest_alert.dart';
import 'package:kisaan_dost/models/pest_citation.dart';
import 'package:kisaan_dost/models/pest_source.dart';

void main() {
  group('PestAlert.fromJson', () {
    test('parses new backend shape', () {
      final alert = PestAlert.fromJson(const <String, dynamic>{
        'fact_id': 'fact_001',
        'crop': 'wheat',
        'pest_or_disease': 'aphid',
        'source_status': 'live',
        'category': 'advisory',
        'district': 'Lahore',
        'severity': 'medium',
        'reason': 'ingested',
        'advisory_text': 'Spray early in the morning.',
        'pesticide_name': 'Confidor',
        'active_ingredient': 'imidacloprid',
        'formulation': '200 SL',
        'explicit_dose_text': '125 ml per acre',
        'safety_text': 'Wear gloves.',
        'quality_control_status': 'passed',
        'source_page': 42,
        'source_section': 'Wheat Pests',
        'source_excerpt': 'Aphid control on wheat',
        'confidence': 0.95,
        'reviewed': true,
        'recommendations': <String>['Monitor regularly'],
        'updated_at': '2026-08-31T00:00:00Z',
      });

      expect(alert.id, 'fact_001');
      expect(alert.crop, 'wheat');
      expect(alert.pest, 'aphid');
      expect(alert.status, ApiDataStatus.live);
      expect(alert.category, 'advisory');
      expect(alert.district, 'Lahore');
      expect(alert.severity, 'medium');
      expect(alert.reason, 'ingested');
      expect(alert.advisoryText, 'Spray early in the morning.');
      expect(alert.pesticideName, 'Confidor');
      expect(alert.activeIngredient, 'imidacloprid');
      expect(alert.formulation, '200 SL');
      expect(alert.explicitDoseText, '125 ml per acre');
      expect(alert.safetyText, 'Wear gloves.');
      expect(alert.qualityControlStatus, 'passed');
      expect(alert.sourcePage, 42);
      expect(alert.sourceSection, 'Wheat Pests');
      expect(alert.sourceExcerpt, 'Aphid control on wheat');
      expect(alert.confidence, 0.95);
      expect(alert.reviewed, isTrue);
      expect(alert.recommendations, const <String>['Monitor regularly']);
      expect(alert.updatedAt, '2026-08-31T00:00:00Z');
    });

    test('falls back to legacy field names', () {
      final alert = PestAlert.fromJson(const <String, dynamic>{
        'id': 'legacy_001',
        'crop': 'rice',
        'pest': 'stem borer',
        'status': 'mock',
        'recommendations': <String>['Consult extension'],
      });

      expect(alert.id, 'legacy_001');
      expect(alert.pest, 'stem borer');
      expect(alert.status, ApiDataStatus.mock);
      expect(alert.recommendations, const <String>['Consult extension']);
    });

    test('uses defaults for missing fields', () {
      final alert = PestAlert.fromJson(const <String, dynamic>{
        'fact_id': 'minimal',
      });

      expect(alert.id, 'minimal');
      expect(alert.crop, 'general');
      expect(alert.pest, 'general');
      expect(alert.status, ApiDataStatus.unavailable);
      expect(alert.sourcePage, 0);
      expect(alert.confidence, 0.0);
      expect(alert.reviewed, isFalse);
      expect(alert.recommendations, isEmpty);
    });
  });

  group('Advisory.fromJson', () {
    test('parses full advisory response', () {
      final advisory = Advisory.fromJson(const <String, dynamic>{
        'crop': 'wheat',
        'pest': 'aphid',
        'district': 'Lahore',
        'status': 'live',
        'source_status': 'historical',
        'matched': true,
        'reason': 'found_match',
        'recommendations': <String>['Spray now'],
        'dose_guidance': '125 ml/acre',
        'safety_notice': 'Use PPE.',
        'citations': <Map<String, dynamic>>[
          <String, dynamic>{
            'fact_id': 'c1',
            'category': 'advisory',
            'source_page': 10,
            'source_section': 'Wheat',
            'source_excerpt': 'excerpt',
          },
        ],
        'updated_at': '2026-08-31T00:00:00Z',
      });

      expect(advisory.crop, 'wheat');
      expect(advisory.pest, 'aphid');
      expect(advisory.district, 'Lahore');
      expect(advisory.status, ApiDataStatus.live);
      expect(advisory.sourceStatus, ApiDataStatus.historical);
      expect(advisory.matched, isTrue);
      expect(advisory.reason, 'found_match');
      expect(advisory.doseGuidance, '125 ml/acre');
      expect(advisory.safetyNotice, 'Use PPE.');
      expect(advisory.citations, hasLength(1));
      expect(advisory.topic, 'aphid');
    });

    test('topic falls back through crop and district', () {
      final advisory = Advisory.fromJson(const <String, dynamic>{
        'district': 'Faisalabad',
        'status': 'mock',
        'source_status': 'mock',
      });

      expect(advisory.topic, 'Faisalabad');
    });
  });

  group('PestCitation.fromJson', () {
    test('parses citation with defaults', () {
      final citation = PestCitation.fromJson(const <String, dynamic>{
        'fact_id': 'c1',
        'category': 'advisory',
        'source_page': 5,
        'source_section': 'Rice',
        'source_excerpt': 'Use resistant varieties.',
      });

      expect(citation.factId, 'c1');
      expect(citation.category, 'advisory');
      expect(citation.sourcePage, 5);
      expect(citation.sourceSection, 'Rice');
      expect(citation.sourceExcerpt, 'Use resistant varieties.');
    });
  });

  group('PestSource.fromJson', () {
    test('parses source metadata', () {
      final source = PestSource.fromJson(const <String, dynamic>{
        'title': 'Annual Report',
        'year': '2024-25',
        'filename': 'report.pdf',
        'ingestion_timestamp': '2026-08-31T00:00:00Z',
        'page_count': 120,
        'num_facts': 45,
        'num_review_queue': 3,
        'num_chunks': 200,
        'status': 'live',
      });

      expect(source.title, 'Annual Report');
      expect(source.year, '2024-25');
      expect(source.filename, 'report.pdf');
      expect(source.ingestionTimestamp, '2026-08-31T00:00:00Z');
      expect(source.pageCount, 120);
      expect(source.numFacts, 45);
      expect(source.numReviewQueue, 3);
      expect(source.numChunks, 200);
      expect(source.status, 'live');
    });
  });
}
