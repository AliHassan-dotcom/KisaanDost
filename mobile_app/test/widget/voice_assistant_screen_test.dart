import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/screens/voice_assistant_screen.dart';

void main() {
  group('VoiceAssistantScreen Widget Tests', () {
    testWidgets('VoiceAssistantScreen renders status header, suggestions and input box',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: VoiceAssistantScreen(userLocation: 'Lahore'),
        ),
      );
      await tester.pump();

      expect(find.text('KisaanDost Voice AI (Real Data)'), findsOneWidget);
      expect(find.text('Real Datasets Online • Location: Lahore'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('🌾 Aaj ka mausam kya hai?'), findsOneWidget);
      expect(find.text('📈 Wheat ka rate kya hai Lahore mandi mein?'), findsOneWidget);
    });
  });
}
