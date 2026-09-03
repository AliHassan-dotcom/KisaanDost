import 'package:flutter/material.dart';

class GreetingHeader extends StatelessWidget {
  const GreetingHeader({
    super.key,
    this.name,
    this.district,
    this.crop,
    this.isUrdu = false,
  });

  final String? name;
  final String? district;
  final String? crop;
  final bool isUrdu;

  String get _greeting {
    final hour = DateTime.now().hour;
    if (isUrdu) {
      if (hour < 12) return 'صبح بخیر';
      if (hour < 17) return 'دوپہر بخیر';
      return 'شام بخیر';
    }
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  @override
  Widget build(BuildContext context) {
    final farmerName = name ?? (isUrdu ? 'کسان دوست' : 'Farmer');
    final districtLabel = district ?? (isUrdu ? 'پنجاب' : 'Punjab');
    final cropLabel = crop ?? (isUrdu ? 'گندم' : 'Wheat');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          '$_greeting, $farmerName',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.green.shade900,
              ),
        ),
        const SizedBox(height: 4),
        Row(
          children: <Widget>[
            Icon(Icons.location_on, size: 14, color: Colors.green.shade700),
            const SizedBox(width: 4),
            Text(
              '$districtLabel · $cropLabel',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: Colors.green.shade800,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
