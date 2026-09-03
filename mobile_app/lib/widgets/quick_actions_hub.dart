import 'package:flutter/material.dart';

/// Quick Actions Hub matching Screenshot 1 & 2:
/// - Urdu Voice (with glowing mint accent)
/// - Scan Crop
/// - Satellite View
/// - Market Prices
/// - Weather
/// - Irrigation Guide
/// - Alerts
class QuickActionsHub extends StatelessWidget {
  const QuickActionsHub({
    super.key,
    required this.isUrdu,
    required this.onVoiceTap,
    required this.onScanTap,
    required this.onSatelliteTap,
    required this.onMarketTap,
    required this.onWeatherTap,
    required this.onIrrigationTap,
    required this.onAlertsTap,
  });

  final bool isUrdu;
  final VoidCallback onVoiceTap;
  final VoidCallback onScanTap;
  final VoidCallback onSatelliteTap;
  final VoidCallback onMarketTap;
  final VoidCallback onWeatherTap;
  final VoidCallback onIrrigationTap;
  final VoidCallback onAlertsTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F2E1E),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.green.withAlpha(50), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            isUrdu ? 'فوری زرعی سہولیات' : 'Quick Actions',
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 14),

          // Row 1: Urdu Voice | Scan Crop | Satellite View | Market Prices
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              _buildActionTile(
                icon: Icons.mic,
                label: isUrdu ? 'اردو آواز' : 'Urdu\nVoice',
                isHighlighted: true,
                onTap: onVoiceTap,
              ),
              _buildActionTile(
                icon: Icons.camera_alt_outlined,
                label: isUrdu ? 'فصل اسکین' : 'Scan\nCrop',
                onTap: onScanTap,
              ),
              _buildActionTile(
                icon: Icons.satellite_outlined,
                label: isUrdu ? 'سیٹلائٹ' : 'Satellite\nView',
                onTap: onSatelliteTap,
              ),
              _buildActionTile(
                icon: Icons.storefront_outlined,
                label: isUrdu ? 'منڈی ریٹس' : 'Market\nPrices',
                onTap: onMarketTap,
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Row 2: Weather | Irrigation Guide | Alerts
          Row(
            children: <Widget>[
              Expanded(
                child: _buildActionTile(
                  icon: Icons.cloud_outlined,
                  label: isUrdu ? 'موسم' : 'Weather',
                  onTap: onWeatherTap,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildActionTile(
                  icon: Icons.water_drop_outlined,
                  label: isUrdu ? 'آبپاشی' : 'Irrigation\nGuide',
                  onTap: onIrrigationTap,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildActionTile(
                  icon: Icons.notifications_none,
                  label: isUrdu ? 'الرٹس' : 'Alerts',
                  onTap: onAlertsTap,
                ),
              ),
              const SizedBox(width: 8),
              const Expanded(child: SizedBox.shrink()), // Spacer for symmetry
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionTile({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool isHighlighted = false,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: 72,
        height: 78,
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        decoration: BoxDecoration(
          color: isHighlighted ? const Color(0xFF00E676) : Colors.white.withAlpha(20),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isHighlighted ? const Color(0xFF00E676) : Colors.white.withAlpha(25),
          ),
          boxShadow: isHighlighted
              ? const <BoxShadow>[
                  BoxShadow(
                    color: Color(0x6600E676),
                    blurRadius: 10,
                    offset: Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(
              icon,
              size: 24,
              color: isHighlighted ? Colors.black87 : Colors.white,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isHighlighted ? FontWeight.bold : FontWeight.w500,
                color: isHighlighted ? Colors.black87 : Colors.white,
                height: 1.1,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}
