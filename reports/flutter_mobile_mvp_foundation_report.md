# Flutter Mobile MVP Foundation Report

## Executive summary

The Kisaan Dost Flutter mobile application foundation is complete. The project passes static analysis, the full unit and widget test suite, and produces a debug Android APK. The web frontend has been left untouched as deprecated/reference-only, while all reusable backend, API, and data logic remains intact.

Key results:

- `flutter analyze`: No issues found
- `flutter test`: 31 tests passed
- `flutter build apk --debug`: succeeded, produced `build/app/outputs/flutter-apk/app-debug.apk`
- One environment-specific build blocker was identified and resolved (see Build blockers and fixes).

## Project location

All mobile source code lives under `mobile_app/`. The existing `web/`, `backend/`, `scripts/`, `tests/`, `app/`, `docs/`, and data pipelines under `Kisaan_Dost_Data/` were not modified.

## Architecture

The app follows a layered architecture designed for testability and a clean swap between offline mock data and live API consumption.

| Layer | Responsibility |
|-------|----------------|
| `config/` | Environment flags, API base URL, HTTPS enforcement |
| `models/` | Immutable data classes and the `ApiDataStatus` enum |
| `services/` | `FlutterSecureStorageService` wrapper and centralized `HttpClient` |
| `repositories/` | Abstract repository interfaces and live `*_impl.dart` implementations |
| `repositories/mock/` | Mock implementations returning deterministic `ApiDataStatus.mock` data |
| `providers/` | Riverpod providers: auth, dashboard, scan, weather, market, satellite, pest, profile, settings |
| `routing/` | `go_router` configuration with auth and role guards |
| `screens/` | Farmer-facing UI screens and the admin placeholder |
| `widgets/` | Shared UI components (cards, badges, selectors, quick actions) |
| `utils/` | Validators, image validation, error mapping, logging |

State management uses `flutter_riverpod`:

- `StateNotifier` for auth and settings because they require explicit event-driven state transitions.
- `AsyncNotifier`/`AsyncValue` for data screens that map naturally to load/error/success states.

Navigation uses `go_router` with named routes. Redirect logic sends unauthenticated users to `/login` and non-admin users away from `/admin`.

## Technology stack

Dependencies declared in `mobile_app/pubspec.yaml`:

- Flutter SDK `^3.12.2`
- `flutter_riverpod: ^2.6.1`
- `go_router: ^14.6.0`
- `flutter_secure_storage: ^10.0.0`
- `image_picker: ^1.1.2`
- `http: ^1.2.2`
- `intl: ^0.20.0`
- `flutter_localizations` (SDK)
- Dev: `flutter_test`, `flutter_lints: ^6.0.0`, `mocktail: ^1.0.4`

## Mock / live toggle

The repository providers choose between mock and live implementations at startup based on the `USE_MOCKS` compile-time variable:

```bash
flutter run --dart-define=USE_MOCKS=true
```

Mock repositories implement the same abstract interfaces as live repositories and return deterministic data tagged with `ApiDataStatus.mock`. This lets the UI be developed and tested without a running backend. Live repositories call the FastAPI `/api/v1` endpoints and tag responses as `ApiDataStatus.live` or `ApiDataStatus.error`.

## Security rules implemented

1. **Token storage only**: the JWT access token is stored in `flutter_secure_storage`; passwords are never persisted.
2. **No password logic in UI**: screens send raw credentials only over HTTPS to the backend login/register endpoints.
3. **Centralized token injection**: `HttpClient` reads the token from secure storage and attaches `Authorization: Bearer <token>`.
4. **401 handling**: `HttpClient` intercepts 401 responses, clears the token, and logs the user out.
5. **HTTPS enforcement**: `main.dart` asserts `AppConfig.apiBaseUrl.startsWith('https')` whenever `AppConfig.requireHttps` is true, which is intended for release builds.
6. **No secrets in source**: API URLs come from `--dart-define`; no keys or credentials are hard-coded.

## Screens delivered

- Splash: restores session from secure storage and routes to dashboard or login.
- Login: phone/password with validation and error mapping.
- Register: name, phone, password, role selector.
- Profile setup/edit: name, district, crop, farm size, irrigation type, language.
- Dashboard: greeting, language toggle, weather/farm-health/market/satellite cards, quick actions, voice-assistant button.
- Scan: image picker, preview, repository call, confidence display, uncertainty warning.
- Weather: district selector, current summary, historical placeholder.
- Irrigation: advisory card with safe fallback when data is missing.
- Pest alerts: filter UI and pending-report message.
- Satellite: NDVI/NDWI/soil-moisture cards with mock/unavailable labels.
- Market: crop selection and price card.
- Settings: language, notifications, theme, logout.
- Admin placeholder: role guard reserved for future admin features.

## Test coverage

The test suite is organized under `mobile_app/test/`:

- `helpers/test_container.dart`: reusable `ProviderContainer` with overrides and automatic disposal.
- `mocks/mock_secure_storage.dart`: in-memory secure storage for tests.
- `unit/validators_test.dart`: phone, password, name, and farm-size validation.
- `unit/image_validator_test.dart`: extension, size, dimension, and existence checks.
- `unit/auth_provider_test.dart`: login, register, logout, restore session.
- `unit/secure_storage_test.dart`: read/write/delete token operations.
- `unit/role_guard_test.dart`: admin access control logic.
- `unit/language_persistence_test.dart`: language change and persistence.
- `widget/login_screen_test.dart`: validation errors and login button behavior.
- `widget/dashboard_status_badge_test.dart`: status badge rendering per `ApiDataStatus`.
- `widget/offline_loading_error_test.dart`: loading, error, and empty states.
- `widget/scan_screen_test.dart`: scan button and provider loading state.
- `widget_test.dart`: top-level smoke test verifying the app renders the splash screen.

Total: 31 tests, all passing.

## Quality checks

### `flutter analyze`

Result: `No issues found!`

The following categories of warnings were resolved during the foundation build:

- `prefer_initializing_formals` in repository and service constructors.
- Unused imports in `pest_repository_impl.dart` and `app_router.dart`.
- Deprecated `value:` parameter on `DropdownButtonFormField` replaced with `initialValue:`.
- Deprecated `encryptedSharedPreferences: true` removed from `AndroidOptions`.
- `ImageValidator.validate(...)` signature changed to named optional parameters.

### `flutter test`

Result: 31 tests passed.

Notable test fixes:

- Riverpod `ProviderContainer` does not propagate async `StateNotifier` state updates without an active listener. Added a no-op listener in `language_persistence_test.dart` before awaiting initialization.
- Login screen test found two "Login" strings (app bar + button); scoped the finder to `ElevatedButton`.
- Scan screen provider starts in a loading state; added `pumpAndSettle()` before asserting the Scan button.
- Dashboard test found two "Weather" texts; asserted "Quick Actions" instead.
- Splash screen used a 1-second timer that left a pending timer in widget tests; replaced with `Future.microtask(() => restoreSession())`.

### `flutter build apk --debug`

Result: succeeded.

Output: `mobile_app/build/app/outputs/flutter-apk/app-debug.apk`.

## Build blockers and fixes

**Blocker**: the first debug build failed inside the Kotlin daemon with an error about being unable to close incremental caches. The root cause was that the project lives on `D:\KisaanDost` while the Flutter pub cache lives on `C:\Users\...\AppData\Local\Pub\Cache`; Kotlin incremental compilation on Windows cannot handle plugin sources and project outputs on different drive roots.

**Fix applied**:

1. `flutter clean` to remove stale incremental caches.
2. Disabled Kotlin incremental compilation in `mobile_app/android/gradle.properties`:

   ```properties
   kotlin.incremental=false
   kotlin.incremental.android=false
   ```

3. Re-ran `flutter build apk --debug`; the APK built successfully.

This fix is environment-specific and does not require moving the project or the pub cache.

## Outstanding items and next steps

1. **Release build**: validate `flutter build apk --release` with a real HTTPS endpoint and ProGuard/R8 rules if minification is enabled.
2. **iOS build**: generate and validate the iOS project on macOS/Xcode.
3. **Integration tests**: add end-to-end tests against a local FastAPI backend using `test_container.dart` overrides.
4. **Backend wiring**: confirm all `/api/v1` endpoints return payloads matching the Flutter models.
5. **Asset pipeline**: add launcher icons, splash branding, and any image assets when design assets are available.
6. **Charts**: the build plan reserved satellite trends and admin charts for a future iteration; no chart library is included in the MVP.

## Files created or updated

Created:

- `mobile_app/lib/main.dart`
- `mobile_app/lib/config/app_config.dart`
- `mobile_app/lib/models/*`
- `mobile_app/lib/services/*`
- `mobile_app/lib/repositories/*` and `mobile_app/lib/repositories/mock/*`
- `mobile_app/lib/providers/*`
- `mobile_app/lib/routing/app_router.dart`
- `mobile_app/lib/screens/*`
- `mobile_app/lib/widgets/*`
- `mobile_app/lib/utils/*`
- `mobile_app/test/helpers/test_container.dart`
- `mobile_app/test/mocks/mock_secure_storage.dart`
- `mobile_app/test/unit/*`
- `mobile_app/test/widget/*`
- `mobile_app/test/widget_test.dart`
- `mobile_app/README.md`
- `reports/flutter_mobile_mvp_foundation_report.md`

Updated:

- `mobile_app/pubspec.yaml` (dependency configuration)
- `mobile_app/android/gradle.properties` (Kotlin incremental compilation flags)

## Conclusion

The Flutter mobile MVP foundation is structurally complete, fully analyzed, tested, and builds a debug Android APK. The code is ready for integration testing against the FastAPI backend and for further UI/UX refinement.
