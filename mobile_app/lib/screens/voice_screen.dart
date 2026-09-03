import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/gemini_live_config.dart';
import '../providers/settings_provider.dart';
import '../providers/voice_provider.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/voice_visualizer_orb.dart';

class VoiceScreen extends ConsumerStatefulWidget {
  const VoiceScreen({super.key});

  @override
  ConsumerState<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends ConsumerState<VoiceScreen> {
  final ScrollController _scrollController = ScrollController();

  final List<Map<String, String>> _suggestionChips = const <Map<String, String>>[
    {
      'ur': '🌾 گندم کی پیلی کنگی کا علاج کیا ہے؟',
      'en': 'What is the treatment for Wheat Yellow Rust?',
    },
    {
      'ur': '💧 آج گندم کو پانی لگانا چاہیے یا نہیں؟',
      'en': 'Should I irrigate my wheat crop today?',
    },
    {
      'ur': '📈 آج لاہور منڈی میں کیا ریٹ چل رہے ہیں؟',
      'en': 'What are today\'s market mandi rates in Lahore?',
    },
    {
      'ur': '🐛 کماد میں کیڑے کا کون سا اسپرے کریں؟',
      'en': 'Which pesticide spray for sugarcane borers?',
    },
    {
      'ur': '🌦️ اگلے تین دن میں بارش کا امکان ہے؟',
      'en': 'Is there any rain expected in next 3 days?',
    },
  ];

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showSettingsDialog(BuildContext context, VoiceState voiceState) {
    final keyController = TextEditingController(
      text: voiceState.apiKey.isNotEmpty ? voiceState.apiKey : GeminiLiveConfig.apiKey,
    );
    String selectedVoice = voiceState.selectedVoice;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(
            children: <Widget>[
              Icon(Icons.tune, color: Colors.green),
              SizedBox(width: 8),
              Text('Gemini Live Settings', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                const Text(
                  'Google Gemini Live (BidiGenerateContent) API Key:',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: keyController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    hintText: 'AIzaSy...',
                    labelText: 'Gemini API Key',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.key),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Assistant Voice (لهجہ و آواز):',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: selectedVoice,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  items: const <DropdownMenuItem<String>>[
                    DropdownMenuItem(value: 'Aoede', child: Text('Aoede (Warm & Natural)')),
                    DropdownMenuItem(value: 'Puck', child: Text('Puck (Energetic)')),
                    DropdownMenuItem(value: 'Kore', child: Text('Kore (Calm)')),
                    DropdownMenuItem(value: 'Fenrir', child: Text('Fenrir (Deep)')),
                    DropdownMenuItem(value: 'Charon', child: Text('Charon (Gentle)')),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      setDialogState(() => selectedVoice = val);
                    }
                  },
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: const Text(
                    '⚡ Model: gemini-2.0-flash-exp (16kHz PCM In, 24kHz Out, Realtime Barge-in)',
                    style: TextStyle(fontSize: 11, color: Colors.green),
                  ),
                ),
              ],
            ),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                final newKey = keyController.text.trim();
                ref.read(voiceProvider.notifier).setApiKey(newKey);
                ref.read(voiceProvider.notifier).setVoice(selectedVoice);
                Navigator.pop(ctx);
              },
              child: const Text('Save Settings'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final voiceState = ref.watch(voiceProvider);
    final settings = ref.watch(settingsProvider);
    final isUrdu = settings.language == 'ur';

    // Auto-scroll transcript when new messages arrive
    ref.listen(voiceProvider, (prev, next) {
      if (prev?.messages.length != next.messages.length) {
        _scrollToBottom();
      }
    });

    return Scaffold(
      appBar: KdAppBar(
        title: isUrdu ? 'کسان دوست لائیو وائس' : 'KisaanDost Voice AI',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: 'Settings',
            onPressed: () => _showSettingsDialog(context, voiceState),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: <Widget>[
            // Connection Status Header Bar
            _buildStatusHeader(context, voiceState, isUrdu),

            // Center Visualizer & Interaction Area
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Column(
                  children: <Widget>[
                    const SizedBox(height: 8),

                    // Voice Waveform / Orb
                    VoiceVisualizerOrb(
                      agentState: voiceState.agentState,
                      micLevel: voiceState.micLevel,
                      speakerLevel: voiceState.speakerLevel,
                      size: 190,
                      onTap: () {
                        if (voiceState.isConnected) {
                          ref.read(voiceProvider.notifier).stopSession();
                        } else {
                          ref.read(voiceProvider.notifier).startSession();
                        }
                      },
                    ),

                    const SizedBox(height: 16),

                    // Dynamic State Prompt
                    _buildDynamicStateText(voiceState, isUrdu),

                    const SizedBox(height: 16),

                    // Quick Suggestion Chips
                    _buildSuggestionChips(isUrdu),

                    const SizedBox(height: 16),

                    // Live Conversation Transcript Box
                    _buildTranscriptSection(voiceState, isUrdu),
                  ],
                ),
              ),
            ),

            // Bottom Control Dock
            _buildBottomControls(context, voiceState, isUrdu),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusHeader(BuildContext context, VoiceState voiceState, bool isUrdu) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    if (voiceState.hasError) {
      statusColor = Colors.red;
      statusText = isUrdu ? 'کنکشن میں رکاوٹ' : 'Connection Error';
      statusIcon = Icons.error_outline;
    } else if (voiceState.isConnecting) {
      statusColor = Colors.amber;
      statusText = isUrdu ? 'جڑ رہا ہے...' : 'Connecting to Gemini Live...';
      statusIcon = Icons.sync;
    } else if (voiceState.isConnected) {
      statusColor = Colors.green;
      statusText = isUrdu ? 'جڑا ہوا ہے (Gemini Live آن لائن)' : 'Connected • Gemini Live Ready';
      statusIcon = Icons.wifi;
    } else {
      statusColor = Colors.grey;
      statusText = isUrdu ? 'آف لائن (شروع کرنے کے لیے مائیک دبائیں)' : 'Idle • Tap mic to start';
      statusIcon = Icons.mic_off_outlined;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: statusColor.withAlpha(20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(statusIcon, color: statusColor, size: 16),
              const SizedBox(width: 8),
              Text(
                statusText,
                style: TextStyle(
                  color: statusColor == Colors.grey ? Colors.grey.shade800 : statusColor,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          if (voiceState.isMuted)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.red.shade100,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text(
                'MUTED',
                style: TextStyle(color: Colors.red, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildDynamicStateText(VoiceState voiceState, bool isUrdu) {
    String stateHeading;
    String stateDescription;

    switch (voiceState.agentState) {
      case VoiceAgentState.speaking:
        stateHeading = isUrdu ? 'کسان دوست بول رہا ہے...' : 'KisaanDost is Speaking...';
        stateDescription = isUrdu ? 'بول کر روک سکتے ہیں (Barge-in Active)' : 'You can interrupt anytime by speaking';
        break;
      case VoiceAgentState.listening:
        stateHeading = isUrdu ? 'آپ کی آواز سن رہا ہوں...' : 'Listening to You...';
        stateDescription = isUrdu ? 'اپنی فصل، کھاد یا منڈی کے بارے میں پوچھیں' : 'Ask about crops, pests, water, or mandi rates';
        break;
      case VoiceAgentState.interrupted:
        stateHeading = isUrdu ? 'جی بتائیں، میں سن رہا ہوں...' : 'Listening to Interruption...';
        stateDescription = isUrdu ? 'اپنی بات جاری رکھیں' : 'Go ahead, assistant is listening';
        break;
      case VoiceAgentState.idle:
        stateHeading = isUrdu ? 'بات چیت شروع کریں' : 'Start Voice Conversation';
        stateDescription = isUrdu ? 'نیچے دیے گئے سبز مائیک بٹن کو دبائیں' : 'Tap the green microphone button below';
        break;
    }

    return Column(
      children: <Widget>[
        Text(
          stateHeading,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        const SizedBox(height: 4),
        Text(
          stateDescription,
          style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
        ),
      ],
    );
  }

  Widget _buildSuggestionChips(bool isUrdu) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          isUrdu ? 'عام زرعی سوالات (پوچھنے کے لیے ٹیپ کریں):' : 'Suggested Farmer Questions (Tap to ask):',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        ),
        const SizedBox(height: 8),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: _suggestionChips.map((chip) {
              final text = isUrdu ? chip['ur']! : chip['en']!;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ActionChip(
                  avatar: const Icon(Icons.chat_bubble_outline, size: 14, color: Colors.green),
                  label: Text(text, style: const TextStyle(fontSize: 12)),
                  onPressed: () {
                    final voiceNotifier = ref.read(voiceProvider.notifier);
                    final state = ref.read(voiceProvider);
                    if (!state.isConnected) {
                      voiceNotifier.startSession().then((_) {
                        voiceNotifier.sendTextMessage(text);
                      });
                    } else {
                      voiceNotifier.sendTextMessage(text);
                    }
                  },
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildTranscriptSection(VoiceState voiceState, bool isUrdu) {
    if (voiceState.messages.isEmpty) {
      return Container(
        height: 140,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey.shade50,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(Icons.record_voice_over, color: Colors.grey.shade400, size: 36),
              const SizedBox(height: 8),
              Text(
                isUrdu ? 'آپ کی گفتگو کا متن یہاں ظاہر ہوگا' : 'Live conversation transcript will appear here',
                style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
              ),
            ],
          ),
        ),
      );
    }

    return Container(
      height: 220,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: ListView.builder(
        controller: _scrollController,
        itemCount: voiceState.messages.length,
        itemBuilder: (context, index) {
          final msg = voiceState.messages[index];
          final isUser = msg.isUser;

          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser ? Colors.green.shade800 : Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: isUser ? null : Border.all(color: Colors.grey.shade300),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: Colors.black.withAlpha(10),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    isUser ? (isUrdu ? 'آپ (کسان)' : 'You (Farmer)') : (isUrdu ? 'کسان دوست AI' : 'KisaanDost AI'),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isUser ? Colors.green.shade100 : Colors.green.shade800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    msg.text,
                    style: TextStyle(
                      fontSize: 13,
                      color: isUser ? Colors.white : Colors.black87,
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildBottomControls(BuildContext context, VoiceState voiceState, bool isUrdu) {
    final notifier = ref.read(voiceProvider.notifier);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withAlpha(15),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: <Widget>[
          // Mute Button
          IconButton(
            icon: Icon(
              voiceState.isMuted ? Icons.mic_off : Icons.mic,
              color: voiceState.isMuted ? Colors.red : Colors.grey.shade700,
            ),
            tooltip: 'Mute / Unmute',
            onPressed: voiceState.isConnected ? () => notifier.toggleMute() : null,
          ),

          // Main Call / Voice Toggle Action Button
          GestureDetector(
            onTap: () {
              if (voiceState.isConnected) {
                notifier.stopSession();
              } else {
                notifier.startSession();
              }
            },
            child: Container(
              width: 68,
              height: 68,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: voiceState.isConnected
                      ? <Color>[Colors.red.shade600, Colors.red.shade800]
                      : <Color>[Colors.green.shade600, Colors.green.shade800],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: (voiceState.isConnected ? Colors.red : Colors.green).withAlpha(80),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Icon(
                voiceState.isConnected ? Icons.call_end : Icons.mic,
                color: Colors.white,
                size: 32,
              ),
            ),
          ),

          // Barge-in / Stop Speaking Button
          IconButton(
            icon: const Icon(Icons.stop_circle_outlined, color: Colors.orange),
            tooltip: isUrdu ? 'روکیں (Interrupt)' : 'Interrupt AI',
            onPressed: voiceState.isSpeaking ? () => notifier.interrupt() : null,
          ),
        ],
      ),
    );
  }
}
