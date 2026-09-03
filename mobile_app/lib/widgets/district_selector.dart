import 'package:flutter/material.dart';

import '../models/district.dart';

class DistrictSelector extends StatelessWidget {
  const DistrictSelector({
    super.key,
    required this.districts,
    this.selected,
    required this.onSelected,
  });

  final List<District> districts;
  final District? selected;
  final ValueChanged<District> onSelected;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<District>(
      initialValue: selected,
      decoration: const InputDecoration(
        labelText: 'District',
        border: OutlineInputBorder(),
      ),
      items: districts.map((district) {
        return DropdownMenuItem<District>(
          value: district,
          child: Text(district.name),
        );
      }).toList(),
      onChanged: (value) {
        if (value != null) onSelected(value);
      },
    );
  }
}
