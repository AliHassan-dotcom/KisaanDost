import 'package:flutter/material.dart';

import '../widgets/kd_app_bar.dart';

class AdminPlaceholderScreen extends StatelessWidget {
  const AdminPlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      appBar: KdAppBar(title: 'Admin'),
      body: Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Admin dashboard is reserved for future release. '
            'It will include user management, audit logs, and usage statistics.',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}
