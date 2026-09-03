import 'dart:math';
import 'package:flutter/material.dart';

import '../providers/voice_provider.dart';

/// Interactive pulsing circular voice visualizer that reacts in real-time to microphone and speaker amplitudes.
class VoiceVisualizerOrb extends StatefulWidget {
  const VoiceVisualizerOrb({
    super.key,
    required this.agentState,
    required this.micLevel,
    required this.speakerLevel,
    this.size = 180,
    this.onTap,
  });

  final VoiceAgentState agentState;
  final double micLevel;
  final double speakerLevel;
  final double size;
  final VoidCallback? onTap;

  @override
  State<VoiceVisualizerOrb> createState() => _VoiceVisualizerOrbState();
}

class _VoiceVisualizerOrbState extends State<VoiceVisualizerOrb> with SingleTickerProviderStateMixin {
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Color primaryColor;
    Color secondaryColor;
    String statusEmoji;

    switch (widget.agentState) {
      case VoiceAgentState.speaking:
        primaryColor = Colors.amber.shade700;
        secondaryColor = Colors.orange.shade400;
        statusEmoji = '🗣️';
        break;
      case VoiceAgentState.listening:
        primaryColor = Colors.green.shade700;
        secondaryColor = Colors.teal.shade400;
        statusEmoji = '👂';
        break;
      case VoiceAgentState.interrupted:
        primaryColor = Colors.deepOrange.shade600;
        secondaryColor = Colors.red.shade300;
        statusEmoji = '✋';
        break;
      case VoiceAgentState.idle:
        primaryColor = Colors.green.shade800;
        secondaryColor = Colors.green.shade500;
        statusEmoji = '🎙️';
        break;
    }

    final double activeLevel = widget.agentState == VoiceAgentState.speaking
        ? widget.speakerLevel
        : widget.micLevel;

    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedBuilder(
        animation: _animController,
        builder: (context, child) {
          final pulse = sin(_animController.value * 2 * pi) * 0.08;
          final dynamicScale = 1.0 + (activeLevel * 0.35) + pulse;

          return SizedBox(
            width: widget.size,
            height: widget.size,
            child: Stack(
              alignment: Alignment.center,
              children: <Widget>[
                // Outer glowing ambient ring
                Container(
                  width: widget.size * dynamicScale * 0.95,
                  height: widget.size * dynamicScale * 0.95,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: <Color>[
                        secondaryColor.withAlpha(80),
                        primaryColor.withAlpha(20),
                        Colors.transparent,
                      ],
                      stops: const <double>[0.3, 0.7, 1.0],
                    ),
                  ),
                ),

                // Middle breathing halo ring
                Container(
                  width: widget.size * 0.78 * (1.0 + activeLevel * 0.2),
                  height: widget.size * 0.78 * (1.0 + activeLevel * 0.2),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: <BoxShadow>[
                      BoxShadow(
                        color: primaryColor.withAlpha(120),
                        blurRadius: 24 + (activeLevel * 20),
                        spreadRadius: 4 + (activeLevel * 8),
                      ),
                    ],
                    gradient: LinearGradient(
                      colors: <Color>[
                        secondaryColor,
                        primaryColor,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                ),

                // Core orb
                Container(
                  width: widget.size * 0.58,
                  height: widget.size * 0.58,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                    boxShadow: <BoxShadow>[
                      BoxShadow(
                        color: Colors.black.withAlpha(30),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Center(
                    child: Text(
                      statusEmoji,
                      style: TextStyle(fontSize: widget.size * 0.24),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
