import 'package:flutter/material.dart';

class QuickActionTile extends StatelessWidget {
  const QuickActionTile({
    super.key,
    required this.label,
    required this.icon,
    this.onTap,
  });

  final String label;
  final String icon;
  final VoidCallback? onTap;

  IconData get _iconData {
    switch (icon) {
      case 'camera':
        return Icons.camera_alt;
      case 'cloud':
        return Icons.cloud;
      case 'alert':
        return Icons.notification_important;
      case 'trend':
        return Icons.trending_up;
      default:
        return Icons.touch_app;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(_iconData, size: 32),
              const SizedBox(height: 8),
              Text(
                label,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
