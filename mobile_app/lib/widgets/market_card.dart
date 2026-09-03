import 'package:flutter/material.dart';

import '../models/market_price.dart';
import 'status_badge.dart';

class MarketCard extends StatelessWidget {
  const MarketCard({
    super.key,
    required this.price,
    this.onTap,
    this.isUrdu = false,
  });

  final MarketPrice price;
  final VoidCallback? onTap;
  final bool isUrdu;

  @override
  Widget build(BuildContext context) {
    final effectivePrice = price.currentPrice ?? price.fqpPrice ?? price.maxPrice ?? price.minPrice;
    final priceStr = effectivePrice != null
        ? 'PKR ${effectivePrice.toStringAsFixed(0)} ${price.unit}'
        : '-- (${price.unit})';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.amber.shade200),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.storefront, size: 20, color: Colors.orange.shade900),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Market Rates',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  StatusBadge(status: price.status),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                '${price.crop} · ${price.market ?? price.district}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 4),
              Text(
                priceStr,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.green.shade900,
                ),
              ),
              if (price.sourceDisplayedDate != null) ...[
                const SizedBox(height: 4),
                Text(
                  'Dated: ${price.sourceDisplayedDate}',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
