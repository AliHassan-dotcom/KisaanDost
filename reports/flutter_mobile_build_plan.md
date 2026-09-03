# Flutter Mobile Build Plan

## Goal
Deliver a farmer-facing Android/iOS Flutter application that consumes the existing Kisaan Dost FastAPI backend (`/api/v1`). The web frontend is deprecated/reference-only.

## Technology stack
- **Framework:** Flutter (Dart, null safety)
- **State management:** Riverpod (`flutter_riverpod`)
- **Routing:** `go_router`
- **Secure storage:** `flutter_secure_storage`
- **Image picker:** `image_picker`
- **HTTP client:** `http`
- **Localization:** `flutter_localizations`, `intl`
- **Charts:** placeholder / service interface only (no chart library required for MVP)

## Project structure

```
mobile_app/
├── android/                  # Generated Flutter Android project
├── ios/                      # Generated Flutter iOS project
├── lib/
│   ├── main.dart             # App entry, providers, theme
│   ├── config/
│   │   └── app_config.dart   # API base URL, timeouts, env-aware settings
│   ├── models/
│   │   ├── user.dart
│   │   ├── user_role.dart
│   │   ├── farmer_profile.dart
│   │   ├── district.dart
│   │   ├── api_data_status.dart
│   │   ├── weather_summary.dart
│   │   ├── farm_health_summary.dart
│   │   ├── satellite_summary.dart
│   │   ├── market_price.dart
│   │   ├── pest_alert.dart
│   │   ├── disease_prediction.dart
│   │   └── advisory.dart
│   ├── routing/
│   │   └── app_router.dart   # go_router routes + route guards
│   ├── providers/
│   │   ├── auth_provider.dart
│   │   ├── profile_provider.dart
│   │   ├── dashboard_provider.dart
│   │   ├── weather_provider.dart
│   │   ├── scan_provider.dart
│   │   ├── market_provider.dart
│   │   ├── satellite_provider.dart
│   │   ├── pest_provider.dart
│   │   └── settings_provider.dart
│   ├── services/
│   │   ├── secure_storage_service.dart
│   │   └── http_client.dart
│   ├── repositories/
│   │   ├── auth_repository.dart
│   │   ├── auth_repository_impl.dart
│   │   ├── profile_repository.dart
│   │   ├── profile_repository_impl.dart
│   │   ├── dashboard_repository.dart
│   │   ├── dashboard_repository_impl.dart
│   │   ├── weather_repository.dart
│   │   ├── weather_repository_impl.dart
│   │   ├── scan_repository.dart
│   │   ├── scan_repository_impl.dart
│   │   ├── market_repository.dart
│   │   ├── market_repository_impl.dart
│   │   ├── satellite_repository.dart
│   │   ├── satellite_repository_impl.dart
│   │   ├── pest_repository.dart
│   │   ├── pest_repository_impl.dart
│   │   └── mock/             # Mock implementations for every repository
│   ├── screens/
│   │   ├── splash_screen.dart
│   │   ├── login_screen.dart
│   │   ├── register_screen.dart
│   │   ├── profile_setup_screen.dart
│   │   ├── dashboard_screen.dart
│   │   ├── scan_screen.dart
│   │   ├── weather_screen.dart
│   │   ├── irrigation_screen.dart
│   │   ├── pest_alerts_screen.dart
│   │   ├── satellite_screen.dart
│   │   ├── market_screen.dart
│   │   ├── settings_screen.dart
│   │   └── admin_placeholder_screen.dart
│   ├── widgets/
│   │   ├── kd_app_bar.dart
│   │   ├── greeting_header.dart
│   │   ├── status_badge.dart
│   │   ├── weather_card.dart
│   │   ├── farm_health_card.dart
│   │   ├── market_card.dart
│   │   ├── satellite_card.dart
│   │   ├── quick_action_tile.dart
│   │   ├── voice_assistant_button.dart
│   │   ├── district_selector.dart
│   │   └── language_toggle.dart
│   └── utils/
│       ├── validators.dart
│       ├── image_validator.dart
│       ├── error_mapper.dart
│       └── logger.dart
├── test/
│   ├── helpers/
│   │   └── test_container.dart
│   ├── mocks/
│   │   └── mock_secure_storage.dart
│   ├── unit/
│   │   ├── validators_test.dart
│   │   ├── image_validator_test.dart
│   │   ├── auth_provider_test.dart
│   │   ├── secure_storage_test.dart
│   │   ├── role_guard_test.dart
│   │   └── language_persistence_test.dart
│   └── widget/
│       ├── login_screen_test.dart
│       ├── dashboard_status_badge_test.dart
│       ├── offline_loading_error_test.dart
│       └── scan_screen_test.dart
├── pubspec.yaml
└── README.md
```

## Architecture decisions

1. **Riverpod for state management**
   - `StateNotifier`/`AsyncValue` pattern for auth, profile, dashboard.
   - Scoped providers for repositories so tests can override with mocks.

2. **Repository pattern**
   - Abstract repository interfaces in `repositories/`.
   - Live implementations call `/api/v1`.
   - Mock implementations return static `ApiDataStatus.mock` data for offline development.

3. **Routing**
   - `go_router` with named routes.
   - Redirect logic: unauthenticated users go to `/login`; non-admin users blocked from `/admin`.

4. **Security**
   - `flutter_secure_storage` for JWT.
   - No password storage on device.
   - `http_client.dart` adds `Authorization: Bearer <token>` from secure storage.
   - 401 responses trigger logout and redirect to login.
   - Release build forces HTTPS via `app_config.dart` `requireHttps` flag.

5. **Localization**
   - English + Urdu using `AppLocalizations`.
   - Language preference persisted to device storage and sent in profile updates.

## API mapping

| Screen | Endpoint(s) |
|--------|-------------|
| Login | `POST /auth/login` |
| Register | `POST /auth/register` |
| Profile setup | `GET /profile`, `PATCH /profile` |
| Dashboard | `GET /dashboard` |
| Scan | `POST /crop-health/scan`, `GET /crop-health/history` |
| Weather | `GET /weather/districts`, `/weather/current`, `/weather/historical` |
| Market | `GET /market/summary`, `/market/history` |
| Pest alerts | `GET /pest-alerts/recent`, `POST /pest-alerts/advisory` |
| Satellite | No dedicated endpoint; data comes from `/dashboard` `satellite` field or mock repository |
| Admin | `GET /admin/users`, `/admin/audit`, `/admin/stats` |

## Screen requirements summary

1. **Splash** – restore token from secure storage; route to dashboard or login.
2. **Login** – phone/password, validation, error mapping, no raw exceptions.
3. **Register** – name, phone, password, role selector.
4. **Profile setup/edit** – name, district, crop, farm size, irrigation type, language.
5. **Dashboard** – greeting header, language toggle, weather/farm-health/market/satellite cards, quick-action tiles, voice-assistant button, status badges.
6. **Scan** – image picker, preview, abstract repository call, confidence + warning.
7. **Weather** – district selector, current summary, historical placeholder, status badge.
8. **Irrigation** – advisory card based on profile, safe fallback when data missing.
9. **Pest alerts** – filter + pending-report message.
10. **Satellite** – NDVI/NDWI/soil-moisture cards, trend placeholder, mock/unavailable labels.
11. **Market** – crop selection, price card, mock label.
12. **Settings** – language, notifications, theme, logout.
13. **Admin placeholder** – role guard, reserved for future charts.

## Test plan

- **Unit:** validators, image validator, secure storage wrapper, auth provider, role guard, language persistence.
- **Widget:** login validation, dashboard status badges, offline/loading/error states, scan image validation.
- **Integration (optional):** against local backend using `test_container.dart` overrides.

## CI/build checklist

- [ ] `flutter pub get`
- [ ] `flutter analyze` passes
- [ ] `flutter test` passes
- [ ] `flutter build apk --debug` succeeds (or blocker documented)
- [ ] No secrets/API keys in committed sources

## Out of scope

- Pesticide annual report parsing.
- GEE exports / satellite live feed.
- Live market price API integration.
- Running or retraining the PyTorch model in Flutter.
