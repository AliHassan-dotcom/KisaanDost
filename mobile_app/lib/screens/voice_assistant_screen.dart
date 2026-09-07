import 'package:flutter/material.dart';

import '../config/env_config.dart';
import '../models/voice_chat_message.dart';
import '../services/greeting_handler.dart';
import '../services/optimized_tts_service.dart';
import '../services/real_ai_research_agent.dart';
import '../services/real_market_service.dart';
import '../services/real_pest_service.dart';
import '../services/real_satellite_service.dart';
import '../services/real_spray_service.dart';
import '../services/real_weather_service.dart';
import '../widgets/kd_app_bar.dart';

/// Standalone production screen connecting real agricultural services and voice synthesis
class VoiceAssistantScreen extends StatefulWidget {
  final String userLocation;

  const VoiceAssistantScreen({
    super.key,
    this.userLocation = 'Lahore',
  });

  @override
  State<VoiceAssistantScreen> createState() => _VoiceAssistantScreenState();
}

class _VoiceAssistantScreenState extends State<VoiceAssistantScreen> {
  late RealWeatherService _weatherService;
  late RealPestService _pestService;
  late RealMarketService _marketService;
  late RealSprayService _sprayService;
  late RealSatelliteService _satelliteService;
  late RealAiResearchAgent _researchAgent;
  final OptimizedTtsService _ttsService = OptimizedTtsService();

  final List<VoiceChatMessage> _messages = <VoiceChatMessage>[];
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isThinking = false;
  bool _isSpeaking = false;

  final List<String> _suggestions = const <String>[
    '🌾 Aaj ka mausam kya hai?',
    '🐛 Wheat mein keeda lag gaya, kya spray karun?',
    '📈 Wheat ka rate kya hai Lahore mandi mein?',
    '💧 Zameen ki nami kitni hai?',
    '🌱 Gandum ke liye pehli khaad konsi dalen?',
  ];

  @override
  void initState() {
    super.initState();

    // Initialize all real services
    _weatherService = RealWeatherService();
    _pestService = RealPestService();
    _marketService = RealMarketService();
    _sprayService = RealSprayService();
    _satelliteService = RealSatelliteService();

    // Initialize AI research agent with real services
    _researchAgent = RealAiResearchAgent(
      weatherService: _weatherService,
      pestService: _pestService,
      marketService: _marketService,
      sprayService: _sprayService,
      satelliteService: _satelliteService,
      googleApiKey: EnvConfig.googleApiKey,
      googleSearchEngineId: EnvConfig.googleSearchEngineId,
    );

    _ttsService.initialize();
  }

  @override
  void dispose() {
    _ttsService.stop();
    _textController.dispose();
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

  Future<void> onFarmerSpoke(String spokenText) async {
    final text = spokenText.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(
        VoiceChatMessage(
          id: 'user_${DateTime.now().millisecondsSinceEpoch}',
          sender: 'user',
          text: text,
          timestamp: DateTime.now(),
        ),
      );
      _isThinking = true;
    });
    _scrollToBottom();

    String response;

    // Check if greeting
    if (GreetingHandler.isGreeting(text)) {
      response = GreetingHandler.getGreetingResponse(text);
    } else {
      // Use real AI research agent
      response = await _researchAgent.answerQuestion(text, widget.userLocation);
    }

    if (!mounted) return;

    setState(() {
      _isThinking = false;
      _isSpeaking = true;
      _messages.add(
        VoiceChatMessage(
          id: 'ai_${DateTime.now().millisecondsSinceEpoch}',
          sender: 'assistant',
          text: response,
          timestamp: DateTime.now(),
        ),
      );
    });
    _scrollToBottom();

    await _ttsService.speak(response);

    if (mounted) {
      setState(() {
        _isSpeaking = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const KdAppBar(
        title: 'KisaanDost Voice AI (Real Data)',
      ),
      body: SafeArea(
        child: Column(
          children: <Widget>[
            // Status Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: Colors.green.shade50,
              child: Row(
                children: <Widget>[
                  Icon(Icons.verified, color: Colors.green.shade700, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'Real Datasets Online • Location: ${widget.userLocation}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.green.shade800,
                    ),
                  ),
                ],
              ),
            ),

            // Main Conversation & Interaction Area
            Expanded(
              child: SingleChildScrollView(
                controller: _scrollController,
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: <Widget>[
                    // Center Avatar Orb
                    Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: _isThinking
                              ? <Color>[Colors.amber.shade400, Colors.amber.shade700]
                              : (_isSpeaking
                                  ? <Color>[Colors.blue.shade400, Colors.blue.shade700]
                                  : <Color>[Colors.green.shade500, Colors.green.shade800]),
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        boxShadow: <BoxShadow>[
                          BoxShadow(
                            color: (_isSpeaking ? Colors.blue : Colors.green).withAlpha(60),
                            blurRadius: 16,
                            offset: const Offset(0, 6),
                          ),
                        ],
                      ),
                      child: Icon(
                        _isThinking
                            ? Icons.hourglass_top
                            : (_isSpeaking ? Icons.volume_up : Icons.mic),
                        color: Colors.white,
                        size: 48,
                      ),
                    ),

                    const SizedBox(height: 12),

                    Text(
                      _isThinking
                          ? 'Real datasets search kar raha hoon...'
                          : (_isSpeaking
                              ? 'KisaanDost jawab de raha hai...'
                              : 'KisaanDost Voice AI'),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),

                    const SizedBox(height: 16),

                    // Suggestion Chips
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _suggestions.map((chip) {
                        return ActionChip(
                          avatar: const Icon(Icons.touch_app, size: 14, color: Colors.green),
                          label: Text(chip, style: const TextStyle(fontSize: 12)),
                          onPressed: () => onFarmerSpoke(chip),
                        );
                      }).toList(),
                    ),

                    const SizedBox(height: 16),

                    // Transcript List
                    ..._messages.map((msg) {
                      final isUser = msg.isUser;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.8,
                          ),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isUser ? Colors.green.shade800 : Colors.white,
                            borderRadius: BorderRadius.circular(12),
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
                                isUser ? 'Aap (Farmer)' : 'KisaanDost AI',
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
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),

            // Bottom Input Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: Colors.black.withAlpha(15),
                    blurRadius: 8,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      onSubmitted: (val) {
                        final t = _textController.text;
                        _textController.clear();
                        onFarmerSpoke(t);
                      },
                      decoration: InputDecoration(
                        hintText: 'Sawal poochiye ya type karein...',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    style: IconButton.styleFrom(backgroundColor: Colors.green),
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: () {
                      final t = _textController.text;
                      _textController.clear();
                      onFarmerSpoke(t);
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
