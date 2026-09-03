import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/district.dart';
import '../models/weather_forecast.dart';
import '../models/weather_summary.dart';
import '../repositories/weather_repository.dart';
import 'dependency_providers.dart';

class WeatherState {
  const WeatherState({
    required this.districts,
    this.selectedDistrict,
    this.current,
    this.forecast,
    this.historical = const <WeatherSummary>[],
  });

  final List<District> districts;
  final District? selectedDistrict;
  final WeatherSummary? current;
  final WeatherForecast? forecast;
  final List<WeatherSummary> historical;
}

class WeatherNotifier extends AsyncNotifier<WeatherState> {
  WeatherRepository get _repository => ref.read(weatherRepositoryProvider);

  @override
  Future<WeatherState> build() async {
    final districts = await _repository.getDistricts();
    final selected = districts.isNotEmpty ? districts.first : null;
    if (selected == null) {
      return const WeatherState(districts: <District>[]);
    }

    final current = await _repository.getCurrent(selected.name);
    final forecast = await _repository.getForecast(selected.name);
    final historical = await _repository.getHistorical(selected.name);

    return WeatherState(
      districts: districts,
      selectedDistrict: selected,
      current: current,
      forecast: forecast,
      historical: historical,
    );
  }

  Future<void> selectDistrict(District district) async {
    state = const AsyncLoading<WeatherState>();
    state = await AsyncValue.guard<WeatherState>(() async {
      final current = await _repository.getCurrent(district.name);
      final forecast = await _repository.getForecast(district.name);
      final historical = await _repository.getHistorical(district.name);
      return WeatherState(
        districts: state.value?.districts ?? <District>[],
        selectedDistrict: district,
        current: current,
        forecast: forecast,
        historical: historical,
      );
    });
  }

  Future<void> refresh() async {
    state = const AsyncLoading<WeatherState>();
    state = await AsyncValue.guard<WeatherState>(() async {
      final districts = await _repository.getDistricts();
      final selected = state.value?.selectedDistrict ??
          (districts.isNotEmpty ? districts.first : null);
      if (selected == null) {
        return const WeatherState(districts: <District>[]);
      }
      final current = await _repository.getCurrent(selected.name);
      final forecast = await _repository.getForecast(selected.name);
      final historical = await _repository.getHistorical(selected.name);
      return WeatherState(
        districts: districts,
        selectedDistrict: selected,
        current: current,
        forecast: forecast,
        historical: historical,
      );
    });
  }
}

final weatherProvider = AsyncNotifierProvider<WeatherNotifier, WeatherState>(
  WeatherNotifier.new,
);
