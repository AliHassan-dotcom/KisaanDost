# Kisaan Dost Mobile (Flutter)

The farmer app — Android-first, Urdu-first, low-bandwidth, offline-tolerant.

**Read before writing code:** [docs/PRD.md](../docs/PRD.md) · [docs/RULES.md §2.2, §4](../docs/RULES.md)

## Core constraints

- Show decisions, not data: status + reason + action. Never raw NDVI values.
- Map is optional — pin + radius is a first-class flow (PRD.md F2.2).
- Every screen must render from the local cache when offline, with data dates.
- Budgets: APK < 25 MB, cold start < 3 s on a 2 GB RAM device.

## Layout

```
lib/
├── main.dart
├── core/
│   ├── config/        environment, API base URL
│   ├── network/       dio client, interceptors, ApiResult (code-based branching)
│   ├── errors/        error-code → bilingual message mapping
│   ├── storage/       secure storage (tokens), cached dashboard cache
│   ├── l10n/          ur/en string catalogs (zero hardcoded strings)
│   └── theme/         M3 theme, RTL-safe styling
├── features/          feature-first modules
│   ├── auth/          phone + OTP
│   ├── onboarding/    language pick, first farm
│   ├── dashboard/     the one-screen daily summary
│   ├── farm/          farm list, AOI draw (map) & pin+radius
│   ├── weather/       forecast card (module-level error states)
│   ├── crop_health/   status, reason, action
│   ├── prices/        mandi rates + "as of" dates
│   ├── alerts/        alert center
│   └── settings/      language, notifications
└── shared/            reusable widgets + utils
```

## Run

```bash
flutter pub get
flutter run                  # device/emulator
flutter test
flutter analyze
```
