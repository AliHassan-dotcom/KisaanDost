import '../../models/advisory.dart';
import '../../models/api_data_status.dart';
import '../../models/pest_alert.dart';
import '../../models/pest_citation.dart';
import '../../models/pest_source.dart';
import '../../repositories/pest_repository.dart';

class MockPestRepository implements PestRepository {
  MockPestRepository({this.delay = const Duration(milliseconds: 300)});

  final Duration delay;

  @override
  Future<List<PestAlert>> getRecentAlerts({
    String? district,
    String? crop,
    String? category,
    int limit = 50,
  }) async {
    await Future<void>.delayed(delay);
    return <PestAlert>[
      PestAlert(
        id: 'pest_001',
        crop: 'wheat',
        pest: 'aphid',
        status: ApiDataStatus.mock,
        category: 'advisory',
        district: district ?? 'Lahore',
        severity: 'medium',
        reason: 'pesticide_report_not_ingested',
        recommendations: const <String>[
          'Consult the latest Pest Warning report.',
          'Contact a local extension worker before applying pesticide.',
        ],
      ),
    ];
  }

  @override
  Future<Advisory> getAdvisory({
    String? crop,
    String? pest,
    String? district,
  }) async {
    await Future<void>.delayed(delay);
    return Advisory(
      crop: crop,
      pest: pest,
      district: district,
      status: ApiDataStatus.mock,
      sourceStatus: ApiDataStatus.mock,
      matched: false,
      reason: 'pesticide_report_not_ingested',
      recommendations: const <String>[
        'Consult the latest Pest Warning and Quality Control of Pesticides Annual Report.',
        'Contact a local extension worker before applying any pesticide.',
      ],
      safetyNotice:
          'Always follow label instructions and consult a local extension worker before applying any pesticide.',
      citations: const <PestCitation>[
        PestCitation(
          factId: 'mock_001',
          category: 'advisory',
          sourcePage: 0,
          sourceSection: 'Mock',
          sourceExcerpt: 'Mock citation for development.',
        ),
      ],
    );
  }

  @override
  Future<List<PestSource>> getSources() async {
    await Future<void>.delayed(delay);
    return <PestSource>[
      PestSource(
        title: 'Pest Warning and Quality Control of Pesticides Annual Report',
        year: '2024-25',
        filename: 'Annual Report 2024-25_copy.pdf',
        pageCount: 0,
        numFacts: 0,
        numReviewQueue: 0,
        numChunks: 0,
        status: 'mock',
      ),
    ];
  }
}
