# Kisaan Dost — Flutter Mobile MVP

Farmer-facing Flutter application for the Kisaan Dost platform. Provides crop-disease scanning, weather, market prices, satellite health, pest alerts, and advisory services.

## Architecture

- **State management:** `flutter_riverpod` (`AsyncNotifier` for data screens, `StateNotifier` for auth/settings).
- **Routing:** `go_router` with auth and admin guards.
- **Security:** JWT access token stored in `flutter_secure_storage`; no passwords or database logic in the app.
- **Networking:** Centralized `HttpClient` with token injection, 401 handling, and multipart upload for scans.
- **Data layer:** Abstract repositories with live (`*_impl.dart`) and mock (`mock/*`) implementations toggled via `--dart-define=USE_MOCKS=true`.

## Project Structure

```
lib/
  config/              App configuration and environment flags (AppConfig)
  models/              Data models and ApiDataStatus enum
  repositories/        Abstract repository interfaces + live implementations
  repositories/mock/   Mock implementations for offline development
  services/            Secure storage and HTTP client
  providers/           Riverpod providers for screens
  routing/             go_router configuration with role guards
  screens/             UI screens (auth, dashboard, scan, weather, pest, etc.)
  widgets/             Shared widgets (cards, badges, selectors)
  utils/               Validators, error mapping, image validation, logger
```

## Running the Application

### 1. Prerequisites

- Flutter SDK `^3.12.2` (Verified with Flutter 3.29.0 / Dart 3.7.0).
- From `mobile_app/` directory:

  ```bash
  flutter pub get
  ```

### 2. Mock Mode (Offline / Standalone UI Walkthrough)

Run the app without requiring a live backend server:

```bash
flutter run --dart-define=USE_MOCKS=true
```

### 3. Live Mode — Android Emulator

Start the FastAPI backend from the project root:

```bash
python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
```

Run Flutter with Android Emulator loopback:

```bash
flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

*Note: `10.0.2.2` is the special alias to the host loopback interface (`127.0.0.1`) within Android emulators.*

### 4. Live Mode — Physical Android Device

1. Connect your physical Android device to the same Wi-Fi / Local Area Network as your development machine.
2. Find your machine's LAN IP address (e.g., `192.168.1.50`).
3. Ensure backend is running on `0.0.0.0:8000`.
4. Run Flutter pointing to your host LAN IP:

```bash
flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=http://<YOUR_LAN_IP>:8000
```

*For secure tunnels (e.g., ngrok / cloudflare tunnel) or staging environments:*
```bash
flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=https://<tunnel-subdomain>.ngrok-free.app
```

## Build Modes & Security

- **Debug:** `flutter run` (Allows local HTTP development to `10.0.2.2` or local LAN).
- **Profile:** `flutter run --profile`
- **Release:** Release builds enforce HTTPS via `AppConfig.requireHttps`. Build with a trusted HTTPS endpoint:

  ```bash
  flutter build apk --release --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=https://api.kisaandost.pk
  ```

## Verification & Testing

```bash
# Static analysis
flutter analyze

# Unit and widget test suite
flutter test
```

## Configuration Flags

| Flag | Default | Allowed Values | Purpose |
|------|---------|----------------|---------|
| `API_BASE_URL` | `http://10.0.2.2:8000` | URL string | Backend base URL (must be HTTPS in release builds) |
| `USE_MOCKS` | `false` | `true`, `false` | Toggle between compile-time mock and live repositories |

## Localization

The app supports English (`en`) and Urdu (`ur`). Language preferences are stored in secure storage and persisted across sessions.
