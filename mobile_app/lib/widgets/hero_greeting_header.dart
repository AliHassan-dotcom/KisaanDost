import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Top header card matching Screenshot 1:
/// "Good Morning, Farm Hero 👋"
/// "Live Gemini 2.5 Voice & Grounded AI Agronomist Online 🌿 🇵🇰"
/// With Urdu/English toggle pill, current date pill, and notification bell with red badge.
class HeroGreetingHeader extends StatelessWidget {
  const HeroGreetingHeader({
    super.key,
    required this.name,
    required this.isUrdu,
    required this.onLanguageToggle,
    required this.onNotificationTap,
    this.unreadCount = 2,
    this.location,
    this.onLocationTap,
  });

  final String? name;
  final bool isUrdu;
  final VoidCallback onLanguageToggle;
  final VoidCallback onNotificationTap;
  final int unreadCount;
  final String? location;
  final VoidCallback? onLocationTap;

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final hour = now.hour;
    String greeting;
    if (hour < 12) {
      greeting = isUrdu ? 'صبح بخیر، کسان ہیرو' : 'Good Morning, Farm Hero';
    } else if (hour < 17) {
      greeting = isUrdu ? 'سہ پہر بخیر، کسان ہیرو' : 'Good Afternoon, Farm Hero';
    } else {
      greeting = isUrdu ? 'شام بخیر، کسان ہیرو' : 'Good Evening, Farm Hero';
    }

    final formattedDate = DateFormat('EEEE,\nMMMM d, yyyy').format(now);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F2E1E), // Dark forest green
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.green.withAlpha(50), width: 1),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Colors.black26,
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          // Heading
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Expanded(
                child: Text(
                  '$greeting 👋',
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
              const Text('🇵🇰', style: TextStyle(fontSize: 20)),
            ],
          ),
          const SizedBox(height: 4),

          // Subtitle & Farm Location
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Expanded(
                child: Text(
                  isUrdu
                      ? 'لائیو جیمنائی وائس اور گرائونڈڈ زرعی AI آن لائن 🌿'
                      : 'Live Gemini 2.5 Voice & Grounded AI Agronomist Online 🌿',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.green.shade200,
                    height: 1.3,
                  ),
                ),
              ),
              if (onLocationTap != null)
                InkWell(
                  onTap: onLocationTap,
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00E676).withAlpha(30),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF00E676).withAlpha(90)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        const Icon(Icons.location_on, size: 13, color: Color(0xFF00E676)),
                        const SizedBox(width: 4),
                        Text(
                          location ?? (isUrdu ? 'لاہور' : 'Lahore'),
                          style: const TextStyle(
                            color: Color(0xFF00E676),
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 2),
                        const Icon(Icons.arrow_drop_down, size: 14, color: Color(0xFF00E676)),
                      ],
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),

          // 3 Inline Pills: Language Toggle | Date | Notification Bell
          Row(
            children: <Widget>[
              // Language Switcher Pill
              InkWell(
                onTap: onLanguageToggle,
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.white.withAlpha(25),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white.withAlpha(30)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      const Icon(Icons.language, size: 14, color: Colors.white70),
                      const SizedBox(width: 6),
                      Text(
                        isUrdu ? 'English (EN)' : 'اردو\n(UR)',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),

              // Date Pill
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.white.withAlpha(25),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white.withAlpha(30)),
                  ),
                  child: Row(
                    children: <Widget>[
                      const Icon(Icons.calendar_today, size: 13, color: Colors.white70),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          formattedDate,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            height: 1.2,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),

              // Notification Bell Button with Red Alert Badge
              InkWell(
                onTap: onNotificationTap,
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white.withAlpha(25),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white.withAlpha(30)),
                  ),
                  child: Stack(
                    clipBehavior: Clip.none,
                    children: <Widget>[
                      const Icon(Icons.notifications_none, size: 18, color: Colors.white),
                      if (unreadCount > 0)
                        Positioned(
                          top: -2,
                          right: -2,
                          child: Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: Color(0xFFFF5252), // Glowing red alert dot
                              shape: BoxShape.circle,
                            ),
                          ),
                        ),
                    ],
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
