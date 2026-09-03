import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

ProviderContainer createContainer({
  List<Override> overrides = const <Override>[],
  List<ProviderObserver>? observers,
}) {
  final container = ProviderContainer(
    overrides: overrides,
    observers: observers,
  );
  addTearDown(container.dispose);
  return container;
}
