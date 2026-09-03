import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

void main() => runApp(const KisaanDostApp());

/// Urdu-first (PRD.md §6): default locale `ur`, English toggle in settings.
/// Every screen must be reviewed in BOTH locales before merge (RULES.md §4.4).
class KisaanDostApp extends StatelessWidget {
  const KisaanDostApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kisaan Dost',
      debugShowCheckedModeBanner: false,
      locale: const Locale('ur'),
      supportedLocales: const [Locale('ur'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: ThemeData(useMaterial3: true),
      home: const Scaffold(
        body: Center(child: Text('Kisaan Dost — skeleton')),
      ),
    );
  }
}
