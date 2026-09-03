import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class KdAppBar extends StatelessWidget implements PreferredSizeWidget {
  const KdAppBar({
    super.key,
    required this.title,
    this.showBack = true,
    this.actions,
  });

  final String title;
  final bool showBack;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(title),
      automaticallyImplyLeading: showBack,
      leading: showBack && Navigator.canPop(context)
          ? IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () => context.pop(),
            )
          : null,
      actions: actions,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
