import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/satellite_coverage.dart';
import '../models/satellite_record.dart';
import '../models/satellite_summary.dart';
import '../repositories/satellite_repository.dart';
import 'dependency_providers.dart';

class SatelliteState {
  const SatelliteState({
    required this.selectedDistrict,
    required this.selectedCrop,
    this.summary,
    this.history = const <SatelliteRecord>[],
    this.coverage,
    this.districts = const <String>[],
    this.isLoading = false,
    this.errorMessage,
  });

  final String selectedDistrict;
  final String selectedCrop;
  final SatelliteSummary? summary;
  final List<SatelliteRecord> history;
  final SatelliteCoverage? coverage;
  final List<String> districts;
  final bool isLoading;
  final String? errorMessage;

  SatelliteState copyWith({
    String? selectedDistrict,
    String? selectedCrop,
    SatelliteSummary? summary,
    List<SatelliteRecord>? history,
    SatelliteCoverage? coverage,
    List<String>? districts,
    bool? isLoading,
    String? errorMessage,
  }) {
    return SatelliteState(
      selectedDistrict: selectedDistrict ?? this.selectedDistrict,
      selectedCrop: selectedCrop ?? this.selectedCrop,
      summary: summary ?? this.summary,
      history: history ?? this.history,
      coverage: coverage ?? this.coverage,
      districts: districts ?? this.districts,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
    );
  }
}

class SatelliteNotifier extends StateNotifier<SatelliteState> {
  SatelliteNotifier(this._repository)
      : super(const SatelliteState(selectedDistrict: 'Lahore', selectedCrop: 'wheat')) {
    loadInitial();
  }

  final SatelliteRepository _repository;

  Future<void> loadInitial() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final districts = await _repository.getDistricts();
      final currentDistrict = districts.contains(state.selectedDistrict)
          ? state.selectedDistrict
          : (districts.isNotEmpty ? districts.first : 'Lahore');

      final summary = await _repository.getLatest(
        district: currentDistrict,
        crop: state.selectedCrop,
      );
      final history = await _repository.getHistory(district: currentDistrict);
      final coverage = await _repository.getCoverage(district: currentDistrict);

      state = state.copyWith(
        selectedDistrict: currentDistrict,
        districts: districts,
        summary: summary,
        history: history,
        coverage: coverage,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> selectDistrict(String district) async {
    if (district == state.selectedDistrict && state.summary != null) return;
    state = state.copyWith(selectedDistrict: district, isLoading: true, errorMessage: null);
    try {
      final summary = await _repository.getLatest(
        district: district,
        crop: state.selectedCrop,
      );
      final history = await _repository.getHistory(district: district);
      final coverage = await _repository.getCoverage(district: district);

      state = state.copyWith(
        selectedDistrict: district,
        summary: summary,
        history: history,
        coverage: coverage,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> refresh() async {
    await selectDistrict(state.selectedDistrict);
  }
}

final satelliteNotifierProvider =
    StateNotifierProvider<SatelliteNotifier, SatelliteState>((ref) {
  final repository = ref.watch(satelliteRepositoryProvider);
  return SatelliteNotifier(repository);
});

// Legacy backward-compatible provider for screens watching AsyncValue<SatelliteSummary>
final satelliteProvider = FutureProvider<SatelliteSummary>((ref) async {
  final state = ref.watch(satelliteNotifierProvider);
  if (state.summary != null) {
    return state.summary!;
  }
  final repo = ref.watch(satelliteRepositoryProvider);
  return repo.getSummary(district: state.selectedDistrict, crop: state.selectedCrop);
});
