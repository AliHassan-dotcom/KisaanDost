import 'package:flutter/material.dart';

import '../models/weather_summary.dart';

/// Weather Forecast Card matching Screenshot 2:
/// - 5-Day horizontal forecast strip (Today, Fri, Sat, Sun, Mon)
/// - Rain Chance: 70%, Wind: 18 km/h, Humidity: 65%
/// - AI Advice Banner: "AI Advice: Rain expected tomorrow. Spray before 6 PM today."
class WeatherForecastHeroCard extends StatelessWidget {
  const WeatherForecastHeroCard({
    super.key,
    required this.weather,
    required this.isUrdu,
    required this.onTap,
  });

  final WeatherSummary weather;
  final bool isUrdu;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: Container(
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
              isUrdu ? 'موسم کی پیشگوئی (5 روزہ)' : 'Weather Forecast',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 14),

            // 5-Day Forecast Row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                _buildDayForecast(
                  day: isUrdu ? 'آج' : 'Today',
                  icon: '⛅',
                  high: '32°',
                  low: '26°',
                  isCurrent: true,
                ),
                _buildDayForecast(
                  day: isUrdu ? 'جمعہ' : 'Fri',
                  icon: '🌧️',
                  high: '31°',
                  low: '25°',
                ),
                _buildDayForecast(
                  day: isUrdu ? 'ہفتہ' : 'Sat',
                  icon: '☁️',
                  high: '30°',
                  low: '24°',
                ),
                _buildDayForecast(
                  day: isUrdu ? 'اتوار' : 'Sun',
                  icon: '☀️',
                  high: '33°',
                  low: '26°',
                ),
                _buildDayForecast(
                  day: isUrdu ? 'پیر' : 'Mon',
                  icon: '☀️',
                  high: '34°',
                  low: '27°',
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Detailed telemetry metrics
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    const Text('🌧️', style: TextStyle(fontSize: 14)),
                    const SizedBox(width: 4),
                    Text(
                      isUrdu ? 'بارش: 70%' : 'Rain Chance: 70%',
                      style: const TextStyle(color: Color(0xFF00E5FF), fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
                Row(
                  children: <Widget>[
                    const Text('💨', style: TextStyle(fontSize: 14)),
                    const SizedBox(width: 4),
                    Text(
                      isUrdu ? 'ہوا: 18 km/h' : 'Wind: 18 km/h',
                      style: const TextStyle(color: Color(0xFF00E5FF), fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
                Row(
                  children: <Widget>[
                    const Text('💧', style: TextStyle(fontSize: 14)),
                    const SizedBox(width: 4),
                    Text(
                      isUrdu ? 'نمی: 65%' : 'Humidity: 65%',
                      style: const TextStyle(color: Color(0xFF00E5FF), fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 14),

            // AI Advice Banner
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF072114),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF00E676).withAlpha(80)),
              ),
              child: Row(
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00E676),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text(
                      'AI',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: Colors.black,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      isUrdu
                          ? 'AI مشورہ: کل بارش متوقع ہے۔ آج شام 6 بجے سے پہلے اسپرے مکمل کریں۔'
                          : 'AI Advice: Rain expected tomorrow. Spray before 6 PM today.',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        height: 1.25,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDayForecast({
    required String day,
    required String icon,
    required String high,
    required String low,
    bool isCurrent = false,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      decoration: BoxDecoration(
        color: isCurrent ? Colors.white.withAlpha(25) : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: isCurrent ? Border.all(color: Colors.white.withAlpha(40)) : null,
      ),
      child: Column(
        children: <Widget>[
          Text(
            day,
            style: TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          const SizedBox(height: 4),
          Text(icon, style: const TextStyle(fontSize: 18)),
          const SizedBox(height: 4),
          Text(
            high,
            style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
          ),
          Text(
            low,
            style: const TextStyle(color: Colors.white60, fontSize: 10),
          ),
        ],
      ),
    );
  }
}
