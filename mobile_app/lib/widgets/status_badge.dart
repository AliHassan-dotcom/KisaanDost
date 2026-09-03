import 'package:flutter/material.dart';

import '../models/api_data_status.dart';

class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.status});

  final ApiDataStatus status;

  Color _color(BuildContext context) {
    switch (status) {
      case ApiDataStatus.live:
        return Colors.green;
      case ApiDataStatus.historical:
        return Colors.blue;
      case ApiDataStatus.mock:
        return Colors.orange;
      case ApiDataStatus.unavailable:
        return Colors.grey;
      case ApiDataStatus.error:
        return Colors.red;
    }
  }

  String get _label {
    switch (status) {
      case ApiDataStatus.live:
        return 'LIVE';
      case ApiDataStatus.historical:
        return 'HISTORICAL';
      case ApiDataStatus.mock:
        return 'MOCK';
      case ApiDataStatus.unavailable:
        return 'UNAVAILABLE';
      case ApiDataStatus.error:
        return 'ERROR';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(
        _label,
        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
      ),
      backgroundColor: _color(context).withAlpha(38),
      side: BorderSide(color: _color(context)),
      padding: EdgeInsets.zero,
      labelPadding: const EdgeInsets.symmetric(horizontal: 6),
    );
  }
}
