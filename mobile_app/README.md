# Kisaan Dost — Flutter Mobile MVP & Real-Time Gemini Live Voice AI

Farmer-facing Flutter application for the Kisaan Dost platform. Provides real-time multimodal voice intelligence via Google Gemini Live, crop-disease scanning, weather forecasting, mandi market prices, satellite vegetation health (NDVI/NDWI), pest advisories, and smart irrigation schedules.

---

## 🎙️ Real-Time Gemini Live Voice Assistant

The app features a bidirectional, real-time voice AI assistant designed specifically for Pakistani farmers.

### 1. Key Technical Highlights
- **Model:** `gemini-2.0-flash-exp` (Gemini Multimodal Live API).
- **Protocol:** Bidirectional WebSocket (`wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent`).
- **Audio Pipeline:**
  - **Input Capture:** 16kHz 16-bit Mono PCM streamed directly from the microphone in ~120ms slices.
  - **Output Playback:** 24kHz PCM streamed audio responses with custom RIFF WAV synthesizer and ultra-low latency playback.
- **Barge-in / Interruption:**
  - Proactive client-side RMS speech detection stops AI playback immediately when the farmer speaks.
  - Full server-side `serverContent.interrupted` signal handling.
- **Languages:** Natural Urdu (اردو), Roman Urdu (e.g. *"Gandum me spray kab karein"*), English, and natural code-switching.
- **Farmer Persona:** Warm, respectful, empathetic agricultural advisor (*"KisaanDost"*) using conversational terminology and actionable advice.

---

## 🏗️ Architecture

```
lib/
  config/
    app_config.dart          # App endpoints and network fallback list
    gemini_live_config.dart  # Gemini Live WebSocket URL, model, voice, system prompt
  models/
    voice_chat_message.dart  # Live conversation transcript model
    user_role.dart, etc.     # Core domain models
  services/
    audio_service.dart       # 16kHz PCM mic recorder, RMS calculator, 24kHz player, barge-in
    gemini_live_service.dart # BidiGenerateContent WebSocket client & parser
    http_client.dart         # Multi-network retry & fallback HTTP client
  providers/
    voice_provider.dart      # Riverpod VoiceNotifier & VoiceState
    auth_provider.dart       # Secure authentication state
    dashboard_provider.dart  # Agricultural data provider
  screens/
    voice_screen.dart        # Real-time Voice AI Screen with visualizer, suggestions, controls
    dashboard_screen.dart    # Main dashboard with Hero Voice AI banner & quick tiles
    scan_screen.dart         # PyTorch CNN leaf disease scanner
    satellite_screen.dart    # Sentinel-2 MSI 10m telemetry & NDVI/NDWI gauges
  widgets/
    voice_visualizer_orb.dart # Multi-layered organic pulsing glowing aura visualizer
    greeting_header.dart, etc.# Shared agricultural UI widgets
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Flutter SDK `^3.12.2` (Verified with Flutter 3.29 / Dart 3.7).
- Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/).

### 2. Environment Configuration
Copy `.env.example` to `.env` in `mobile_app/`:

```bash
cp .env.example .env
```

Add your Gemini API Key in `mobile_app/.env`:
```ini
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
GEMINI_LIVE_MODEL=models/gemini-2.0-flash-exp
API_BASE_URL=http://192.168.1.7:8000
```

*Note: You can also enter or update your Gemini API Key directly inside the app by tapping the ⚙️ Settings icon on the Voice Screen.*

### 3. Install Dependencies & Run Tests
```bash
flutter pub get
flutter analyze
flutter test
```
*(All 84 unit and widget tests pass).*

### 4. Run the Application
```bash
# Debug mode on connected physical device or emulator
flutter run

# Or build debug APK
flutter build apk --debug
```

---

## 🧪 Testing Checklist

- [x] **Live Audio Capture:** Verify 16kHz Mono PCM microphone stream starts cleanly without permission crashes.
- [x] **Gemini WebSocket Handshake:** Verify `setup` payload sends correct model, audio modality, prebuilt voice, and farmer system prompt.
- [x] **Audio Playback:** Verify 24kHz incoming PCM audio streams smoothly through device speaker.
- [x] **Barge-In / Interruption:** Verify that speaking while the assistant is talking immediately cuts off audio playback and switches state to listening.
- [x] **Language Code-Switching:** Test Urdu, Roman Urdu, and English prompts.
- [x] **UI Visualizer:** Verify `VoiceVisualizerOrb` glows emerald green when listening and golden amber when speaking.
- [x] **Settings Dialog:** Verify user can configure API key and switch voices (`Aoede`, `Puck`, `Kore`, `Fenrir`, `Charon`).

---

## 🔒 Security Best Practices

1. **Never Commit API Keys:** `.env` and `.env.*` are added to `.gitignore`.
2. **Ephemeral Token Proxy (Production Architecture):**
   - In production environments, client apps should request short-lived ephemeral session tokens from the backend (`/api/v1/voice/session-token`) instead of storing long-lived master API keys on device.
3. **Secure Storage:** User credentials and JWT access tokens are stored strictly in hardware-backed `FlutterSecureStorage`.
4. **HTTPS Enforcement:** Production release builds assert HTTPS endpoints via `AppConfig.requireHttps`.
