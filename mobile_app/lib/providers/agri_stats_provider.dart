import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/agri_gdp.dart';
import '../models/agri_trade.dart';
import '../models/land_utilization.dart';
import '../models/water_availability.dart';
import '../repositories/agri_stats_repository.dart';
import 'dependency_providers.dart';

class AgriStatsState {
  const AgriStatsState({
    required this.selectedDistrict,
    this.landUtilization,
    this.waterAvailability,
    this.gdpSeries = const <AgriGdp>[],
    this.exportsList = const <AgriTradeItem>[],
    this.importsList = const <AgriTradeItem>[],
    this.tradeSummary,
    this.selectedTab = 0,
    this.allDistricts = const <String>[
      'Lahore District',
      'Faisalabad District',
      'Multan District',
      'Rawalpindi District',
      'Gujranwala District',
      'Sargodha District',
      'Bahawalpur District',
      'Sahiwal District',
      'Rahim Yar Khan District',
      'Dera Ghazi Khan District',
      'Sialkot District',
      'Kasur District',
      'Sheikhupura District',
      'Jhang District',
      'Okara District',
      'Mianwali District',
      'Attock District',
      'Chakwal District',
      'Jhelum District',
      'Muzaffargarh District',
    ],
  });

  final String selectedDistrict;
  final LandUtilization? landUtilization;
  final WaterAvailability? waterAvailability;
  final List<AgriGdp> gdpSeries;
  final List<AgriTradeItem> exportsList;
  final List<AgriTradeItem> importsList;
  final AgriTradeSummary? tradeSummary;
  final int selectedTab;
  final List<String> allDistricts;

  AgriStatsState copyWith({
    String? selectedDistrict,
    LandUtilization? landUtilization,
    WaterAvailability? waterAvailability,
    List<AgriGdp>? gdpSeries,
    List<AgriTradeItem>? exportsList,
    List<AgriTradeItem>? importsList,
    AgriTradeSummary? tradeSummary,
    int? selectedTab,
    List<String>? allDistricts,
  }) {
    return AgriStatsState(
      selectedDistrict: selectedDistrict ?? this.selectedDistrict,
      landUtilization: landUtilization ?? this.landUtilization,
      waterAvailability: waterAvailability ?? this.waterAvailability,
      gdpSeries: gdpSeries ?? this.gdpSeries,
      exportsList: exportsList ?? this.exportsList,
      importsList: importsList ?? this.importsList,
      tradeSummary: tradeSummary ?? this.tradeSummary,
      selectedTab: selectedTab ?? this.selectedTab,
      allDistricts: allDistricts ?? this.allDistricts,
    );
  }
}

class AgriStatsNotifier extends AsyncNotifier<AgriStatsState> {
  AgriStatsRepository get _repository => ref.read(agriStatsRepositoryProvider);

  @override
  Future<AgriStatsState> build() async {
    const defaultDistrict = 'Lahore District';
    final landList = await _repository.getLandUtilization(district: defaultDistrict);
    final waterList = await _repository.getWaterAvailability(district: defaultDistrict);
    final gdpList = await _repository.getGdp();
    final expList = await _repository.getExports();
    final impList = await _repository.getImports();
    final sumList = await _repository.getTradeSummary();

    return AgriStatsState(
      selectedDistrict: defaultDistrict,
      landUtilization: landList.isNotEmpty ? landList.first : null,
      waterAvailability: waterList.isNotEmpty ? waterList.first : null,
      gdpSeries: gdpList,
      exportsList: expList,
      importsList: impList,
      tradeSummary: sumList.isNotEmpty ? sumList.first : null,
      selectedTab: 0,
    );
  }

  Future<void> selectDistrict(String district) async {
    final current = state.value;
    state = const AsyncLoading<AgriStatsState>();
    state = await AsyncValue.guard<AgriStatsState>(() async {
      final landList = await _repository.getLandUtilization(district: district);
      final waterList = await _repository.getWaterAvailability(district: district);

      return (current ?? const AgriStatsState(selectedDistrict: 'Lahore District')).copyWith(
        selectedDistrict: district,
        landUtilization: landList.isNotEmpty ? landList.first : null,
        waterAvailability: waterList.isNotEmpty ? waterList.first : null,
      );
    });
  }

  void setTab(int tabIndex) {
    final current = state.value;
    if (current == null) return;
    state = AsyncData(current.copyWith(selectedTab: tabIndex));
  }

  Future<void> refresh() async {
    final current = state.value;
    if (current == null) return;
    state = const AsyncLoading<AgriStatsState>();
    state = await AsyncValue.guard<AgriStatsState>(() => build());
  }
}

final agriStatsProvider = AsyncNotifierProvider<AgriStatsNotifier, AgriStatsState>(
  AgriStatsNotifier.new,
);
