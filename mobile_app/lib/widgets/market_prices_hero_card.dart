import 'package:flutter/material.dart';

import '../models/market_price.dart';

/// Market Prices Card matching Screenshot 3:
/// - Best Market: Lahore Mandi (green badge)
/// - Rs. 3,850 / 40kg
/// - Other Markets: Faisalabad Rs. 3,720 | Multan Rs. 3,680
/// - View Full Prices ↗ button
class MarketPricesHeroCard extends StatelessWidget {
  const MarketPricesHeroCard({
    super.key,
    required this.market,
    required this.isUrdu,
    required this.onTap,
  });

  final MarketPrice market;
  final bool isUrdu;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final price = market.currentPrice ?? 3850;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F2E1E),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.green.withAlpha(50), width: 1),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Colors.black26,
            blurRadius: 8,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            isUrdu ? 'منڈی ریٹس (گندم)' : 'Market Prices (Wheat)',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 14),

          // Best Market Header Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Text(
                isUrdu ? 'بہترین منڈی' : 'Best Market',
                style: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
              Row(
                children: <Widget>[
                  const Icon(Icons.location_on, size: 14, color: Color(0xFF00E676)),
                  const SizedBox(width: 4),
                  Text(
                    isUrdu ? 'لاہور منڈی' : 'Lahore Mandi',
                    style: const TextStyle(
                      color: Color(0xFF00E676),
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 4),

          // Price Display
          RichText(
            text: TextSpan(
              text: 'Rs. $price ',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 26,
                fontWeight: FontWeight.bold,
              ),
              children: const <TextSpan>[
                TextSpan(
                  text: '/ 40kg',
                  style: TextStyle(
                    color: Colors.white60,
                    fontSize: 14,
                    fontWeight: FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Other Markets Header
          Text(
            isUrdu ? 'دیگر قریبی منڈیاں' : 'Other Markets',
            style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 6),

          // Faisalabad Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              const Text('• Faisalabad', style: TextStyle(color: Colors.white60, fontSize: 12)),
              const Text('Rs. 3,720', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 4),

          // Multan Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              const Text('• Multan', style: TextStyle(color: Colors.white60, fontSize: 12)),
              const Text('Rs. 3,680', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 14),

          // View Full Prices Button
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: onTap,
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.white.withAlpha(40)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
                padding: const EdgeInsets.symmetric(vertical: 12),
                backgroundColor: Colors.white.withAlpha(15),
              ),
              child: Text(
                isUrdu ? 'تمام منڈیوں کے ریٹس دیکھیں ↗' : 'View Full Prices ↗',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
