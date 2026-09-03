import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/market_mover.dart';
import '../models/market_price.dart';
import '../repositories/market_repository.dart';
import 'dependency_providers.dart';

class MarketState {
  const MarketState({
    required this.crop,
    required this.district,
    this.commodities = const <String>[
      'Wheat',
      'Rice Basmati Super (New)',
      'Rice (IRRI)',
      'Maize',
      'Potato Fresh',
      'Potato Store',
      'Onion',
      'Tomato',
      'Seed Cotton(Phutti)',
      'Sugarcane',
      'Gram Black Bareek',
      'Moong',
    ],
    this.price,
    this.movers = const <MarketMover>[],
    this.history = const <Map<String, dynamic>>[],
  });

  final String crop;
  final String district;
  final List<String> commodities;
  final MarketPrice? price;
  final List<MarketMover> movers;
  final List<Map<String, dynamic>> history;
}

class MarketNotifier extends AsyncNotifier<MarketState> {
  MarketRepository get _repository => ref.read(marketRepositoryProvider);

  @override
  Future<MarketState> build() async {
    final commodities = await _repository.getCommodities();
    final selectedCrop = commodities.isNotEmpty ? commodities.first : 'Wheat';
    final price = await _repository.getSummary(crop: selectedCrop, district: 'Lahore');
    final movers = await _repository.getMovers();
    final history = await _repository.getHistory(crop: selectedCrop, district: 'Lahore');

    return MarketState(
      crop: selectedCrop,
      district: 'Lahore',
      commodities: commodities.isNotEmpty ? commodities : const <String>[
        'Wheat',
        'Rice Basmati Super (New)',
        'Rice (IRRI)',
        'Maize',
        'Potato Fresh',
        'Potato Store',
        'Onion',
        'Tomato',
        'Seed Cotton(Phutti)',
        'Sugarcane',
        'Gram Black Bareek',
        'Moong',
      ],
      price: price,
      movers: movers,
      history: history,
    );
  }

  Future<void> selectCommodity(String crop, {String district = 'Lahore'}) async {
    state = const AsyncLoading<MarketState>();
    state = await AsyncValue.guard<MarketState>(() async {
      final commodities = state.value?.commodities ?? await _repository.getCommodities();
      final price = await _repository.getLatest(commodity: crop, market: district);
      final movers = state.value?.movers ?? await _repository.getMovers();
      final history = await _repository.getHistory(crop: crop, district: district);
      return MarketState(
        crop: crop,
        district: district,
        commodities: commodities,
        price: price,
        movers: movers,
        history: history,
      );
    });
  }

  Future<void> load({required String crop, required String district}) async {
    state = const AsyncLoading<MarketState>();
    state = await AsyncValue.guard<MarketState>(() async {
      final commodities = state.value?.commodities ?? await _repository.getCommodities();
      final price = await _repository.getSummary(crop: crop, district: district);
      final movers = await _repository.getMovers();
      final history = await _repository.getHistory(crop: crop, district: district);
      return MarketState(
        crop: crop,
        district: district,
        commodities: commodities,
        price: price,
        movers: movers,
        history: history,
      );
    });
  }

  Future<void> refresh() async {
    final current = state.value;
    if (current == null) return;
    await selectCommodity(current.crop, district: current.district);
  }
}

final marketProvider = AsyncNotifierProvider<MarketNotifier, MarketState>(
  MarketNotifier.new,
);
