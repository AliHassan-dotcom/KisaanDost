import 'package:flutter/material.dart';

/// Farm Insights Card matching Screenshot 3:
/// - 💧 "Irrigate in 2 days"
/// - 🌱 "Fertilizer application recommended"
class FarmInsightsHeroCard extends StatelessWidget {
  const FarmInsightsHeroCard({
    super.key,
    required this.isUrdu,
    required this.onIrrigationTap,
  });

  final bool isUrdu;
  final VoidCallback onIrrigationTap;

  @override
  Widget build(BuildContext context) {
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
            isUrdu ? 'کھیت کی بصیرت اور تجاویز' : 'Farm Insights',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 14),

          // Insight 1: Irrigation
          InkWell(
            onTap: onIrrigationTap,
            borderRadius: BorderRadius.circular(12),
            child: Row(
              children: <Widget>[
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E5FF).withAlpha(30),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.water_drop, size: 16, color: Color(0xFF00E5FF)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    isUrdu ? '2 دن بعد آبپاشی کریں' : 'Irrigate in 2 days',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Insight 2: Fertilizer
          Row(
            children: <Widget>[
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF00E676).withAlpha(30),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.eco, size: 16, color: Color(0xFF00E676)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  isUrdu ? 'کھاد کا استعمال تجویز کیا گیا ہے' : 'Fertilizer application recommended',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
