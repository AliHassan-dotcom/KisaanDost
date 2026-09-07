import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/disease_prediction.dart';
import '../repositories/scan_repository.dart';
import 'dependency_providers.dart';

class ScanNotifier extends AsyncNotifier<ScanState> {
  ScanRepository get _repository => ref.read(scanRepositoryProvider);

  @override
  Future<ScanState> build() async {
    try {
      final history = await _repository.getHistory();
      return ScanState(history: history);
    } catch (_) {
      return const ScanState();
    }
  }

  Future<void> scan(String filePath) async {
    state = const AsyncLoading<ScanState>();
    state = await AsyncValue.guard<ScanState>(() async {
      final prediction = await _repository.scan(filePath);
      List<DiseasePrediction> history = state.value?.history ?? const <DiseasePrediction>[];
      try {
        history = await _repository.getHistory();
      } catch (_) {
        history = <DiseasePrediction>[prediction, ...history];
      }
      return ScanState(
        lastPrediction: prediction,
        history: history,
      );
    });
  }

  Future<void> refreshHistory() async {
    state = const AsyncLoading<ScanState>();
    state = await AsyncValue.guard<ScanState>(() async {
      final history = await _repository.getHistory();
      return ScanState(
        lastPrediction: state.value?.lastPrediction,
        history: history,
      );
    });
  }
}

class ScanState {
  const ScanState({
    this.lastPrediction,
    this.history = const <DiseasePrediction>[],
  });

  final DiseasePrediction? lastPrediction;
  final List<DiseasePrediction> history;
}

final scanProvider = AsyncNotifierProvider<ScanNotifier, ScanState>(
  ScanNotifier.new,
);
