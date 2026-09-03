import 'package:flutter/material.dart';

import '../models/market_price.dart';
import 'status_badge.dart';

class MarketCard extends StatelessWidget {
  const MarketCard({super.key, required this.price, this.onTap});

  final MarketPrice price;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final effectivePrice = price.currentPrice ?? price.fqpPrice ?? price.maxPrice ?? price.minPrice;
    final priceStr = effectivePrice != null
        ? 'PKR ${effectivePrice.toStringAsFixed(0)} ${price.unit}'
        : '-- (${price.unit})';

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Text(
                    'Market Rates',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  StatusBadge(status: price.status),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '${price.crop} · ${price.market ?? price.district}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(
                priceStr,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.bold, color: Colors.green.shade800),
              ),
              if (price.sourceDisplayedDate != null)
                Text(
                  'Dated: ${price.sourceDisplayedDate}',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
