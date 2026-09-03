import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/market_mover.dart';
import '../models/market_price.dart';
import '../providers/market_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/status_badge.dart';

class MarketScreen extends ConsumerWidget {
  const MarketScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final marketAsync = ref.watch(marketProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'منڈی کے ریٹس' : 'Market Rates (AMIS Punjab)',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(marketProvider.notifier).refresh(),
          ),
        ],
      ),
      body: marketAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                const Icon(Icons.storefront_outlined, size: 48, color: Colors.grey),
                const SizedBox(height: 16),
                Text(
                  isUrdu ? 'منڈی کا ڈیٹا لوڈ نہیں ہو سکا' : 'Failed to load market data',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  '$error',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(marketProvider.notifier).refresh(),
                  child: Text(isUrdu ? 'دوبارہ کوشش کریں' : 'Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (state) => RefreshIndicator(
          onRefresh: () => ref.read(marketProvider.notifier).refresh(),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                // Top Movers Section
                if (state.movers.isNotEmpty) ...<Widget>[
                  Text(
                    isUrdu ? 'منڈی کے اہم ریٹس:' : 'Observed Market Rates (Lahore Mandi):',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 100,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: state.movers.length,
                      separatorBuilder: (context, index) => const SizedBox(width: 8),
                      itemBuilder: (context, idx) {
                        final mover = state.movers[idx];
                        return _buildMoverCard(context, mover, isUrdu);
                      },
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Commodity Selector Chips
                Text(
                  isUrdu ? 'اجناس منتخب کریں:' : 'Select Commodity:',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: state.commodities.map((cropName) {
                    final isSelected = cropName.toLowerCase() == state.crop.toLowerCase();
                    return ChoiceChip(
                      label: Text(cropName),
                      selected: isSelected,
                      onSelected: (selected) {
                        if (selected) {
                          ref.read(marketProvider.notifier).selectCommodity(cropName, district: state.district);
                        }
                      },
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),

                if (state.price != null) ...<Widget>[
                  _buildMarketPriceCard(context, state.price!, isUrdu),
                  const SizedBox(height: 16),

                  if (state.price!.isStale || state.price!.warning != null)
                    _buildWarningBanner(context, state.price!.warning ?? 'Showing retained historical AMIS observation.'),

                  _buildSourceProvenanceCard(context, state.price!, isUrdu),
                ] else
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Center(
                        child: Text(
                          isUrdu ? 'کوئی ڈیٹا دستیاب نہیں ہے' : 'No official market data available for this commodity.',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMoverCard(BuildContext context, MarketMover mover, bool isUrdu) {
    return Card(
      color: Colors.green.shade50,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: Colors.green.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text(
              mover.commodityName,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            const SizedBox(height: 4),
            Text(
              'PKR ${mover.currentPricePkr.toStringAsFixed(0)}',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Colors.green.shade900,
              ),
            ),
            Text(
              mover.unit,
              style: TextStyle(fontSize: 10, color: Colors.grey.shade700),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMarketPriceCard(BuildContext context, MarketPrice price, bool isUrdu) {
    final fqpStr = price.fqpPrice != null ? 'PKR ${price.fqpPrice!.toStringAsFixed(0)}' : '--';
    final minStr = price.minPrice != null ? 'PKR ${price.minPrice!.toStringAsFixed(0)}' : '--';
    final maxStr = price.maxPrice != null ? 'PKR ${price.maxPrice!.toStringAsFixed(0)}' : '--';
    final qtyStr = price.quantity != null ? price.quantity!.toStringAsFixed(0) : '--';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      '${price.crop} (${price.market ?? price.district})',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    if (price.sourceDisplayedDate != null)
                      Text(
                        isUrdu ? 'تاریخ: ${price.sourceDisplayedDate}' : 'Dated: ${price.sourceDisplayedDate}',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                  ],
                ),
                StatusBadge(status: price.status),
              ],
            ),
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: <Widget>[
                _buildPriceMetric(context, isUrdu ? 'کم سے کم' : 'Min Price', minStr),
                _buildPriceMetric(context, isUrdu ? 'اکثر ریٹ (FQP)' : 'FQP (Common)', fqpStr, isBold: true),
                _buildPriceMetric(context, isUrdu ? 'زیادہ سے زیادہ' : 'Max Price', maxStr),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(
                  isUrdu ? 'یونٹ: ${price.unit}' : 'Unit: ${price.unit}',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                ),
                Text(
                  isUrdu ? 'آمد مقدار: $qtyStr' : 'Arrival Qty: $qtyStr',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPriceMetric(BuildContext context, String label, String value, {bool isBold = false}) {
    return Column(
      children: <Widget>[
        Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: isBold ? 15 : 13,
            fontWeight: isBold ? FontWeight.bold : FontWeight.w500,
            color: isBold ? Colors.green.shade800 : Colors.black87,
          ),
        ),
      ],
    );
  }

  Widget _buildWarningBanner(BuildContext context, String warning) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.amber.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.amber.shade300),
      ),
      child: Row(
        children: <Widget>[
          Icon(Icons.info_outline, size: 20, color: Colors.amber.shade900),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              warning,
              style: TextStyle(fontSize: 12, color: Colors.amber.shade900),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSourceProvenanceCard(BuildContext context, MarketPrice price, bool isUrdu) {
    return Card(
      elevation: 0,
      color: Colors.grey.shade50,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              isUrdu ? 'ماخذ اور تصدیق:' : 'Source & Verification:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
            ),
            const SizedBox(height: 4),
            Text(
              '${price.sourceName ?? 'Official AMIS Punjab'} · ${price.sourceUrl ?? 'http://www.amis.pk/'}',
              style: TextStyle(fontSize: 11, color: Colors.grey.shade700),
            ),
            if (price.retrievedAt != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                isUrdu ? 'حاصل کرنے کا وقت: ${price.retrievedAt}' : 'Retrieved At: ${price.retrievedAt}',
                style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
