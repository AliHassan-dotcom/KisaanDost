import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/models/voice_chat_message.dart';
import 'package:kisaan_dost/providers/voice_provider.dart';
import 'package:kisaan_dost/screens/voice_screen.dart';
import 'package:kisaan_dost/services/gemini_live_service.dart';
import 'package:kisaan_dost/widgets/voice_visualizer_orb.dart';

void main() {
  group('VoiceScreen Widget Tests', () {
    testWidgets('VoiceScreen renders title, visualizer orb, and action button', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: VoiceScreen(),
          ),
        ),
      );

      await tester.pump();

      expect(find.text('KisaanDost Voice AI'), findsOneWidget);
      expect(find.byType(VoiceVisualizerOrb), findsOneWidget);
      expect(find.byIcon(Icons.mic), findsWidgets);
    });

    testWidgets('VoiceScreen displays suggestion chips', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: VoiceScreen(),
          ),
        ),
      );

      await tester.pump();

      expect(find.textContaining('Wheat Yellow Rust'), findsOneWidget);
      expect(find.textContaining('irrigate my wheat'), findsOneWidget);
    });

    testWidgets('VoiceScreen displays active conversation messages', (tester) async {
      final sampleMessages = <VoiceChatMessage>[
        VoiceChatMessage(
          id: '1',
          sender: 'user',
          text: 'Gandum me peeli kangi ka ilaj bataiye',
          timestamp: DateTime.now(),
        ),
        VoiceChatMessage(
          id: '2',
          sender: 'assistant',
          text: 'Ji Kisaan bhai, gandum me peeli kangi k liye Tebuconazole ka spray karein.',
          timestamp: DateTime.now(),
        ),
      ];

      await tester.pumpWidget(
        ProviderScope(
          overrides: <Override>[
            voiceProvider.overrideWith((ref) {
              final notifier = VoiceNotifier();
              notifier.state = notifier.state.copyWith(
                connectionState: GeminiLiveConnectionState.connected,
                agentState: VoiceAgentState.listening,
                messages: sampleMessages,
              );
              return notifier;
            }),
          ],
          child: const MaterialApp(
            home: VoiceScreen(),
          ),
        ),
      );

      await tester.pump();

      expect(find.text('Gandum me peeli kangi ka ilaj bataiye'), findsOneWidget);
      expect(find.textContaining('Tebuconazole ka spray karein'), findsOneWidget);
    });
  });
}
