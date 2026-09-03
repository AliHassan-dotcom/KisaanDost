# Mobile MVP Demo Guide

## Prerequisites

- Backend source: `app/` (not legacy `backend/`).
- Flutter source: `mobile_app/` (not legacy `mobile/`).
- Flutter SDK is available at `D:\flutter\bin\flutter.bat` in the verification environment.
- Use mock mode for a reliable UI-only walkthrough, or the live backend path for supported APIs. The currently configured crop model path is unavailable, so live scan behavior can safely return an unavailable/error state until Priority 0 configuration work is completed.

## 1. Start the Backend

From repository root:

```bash
python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
```

Health check: `http://localhost:8000/health`. API contracts are under `/api/v1`.

## 2. Configure and Run Flutter

Android emulator, live backend:

```bash
cd mobile_app
D:\flutter\bin\flutter.bat run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

UI-only mock walkthrough:

```bash
D:\flutter\bin\flutter.bat run --dart-define=USE_MOCKS=true
```

A physical device needs the host machine LAN IP instead of `10.0.2.2`. A release build requires an HTTPS endpoint and release signing; neither is part of this frozen demo package.

## 3. Judge Walkthrough

1. **Register/login as a farmer.** This is live-backend dependent unless mock mode is selected. Tokens are stored using Flutter secure storage.
2. **Set the profile district and crop.** Profile data drives district-aware dashboard, weather, irrigation, and pest requests.
3. **Open Dashboard.** Explain that cards show their source/status. Weather can be historical NASA POWER data or clearly labeled mock fallback.
4. **Open Crop Scan and select an image.** The image is validated for file name, extension, claimed image type, and size before upload. Explain that predictions are limited to PlantVillage Pepper bell/Potato/Tomato classes; confidence under 0.75 is uncertain; a prediction does not prescribe pesticide use. In current live configuration, model-path unavailability is an expected safe unavailable state.
5. **Open Weather.** Explain historical monthly NASA POWER coverage, the district coverage caveat, and visible mock/unavailable fallback labels.
6. **Open Irrigation.** Treat it as dashboard guidance based on available weather/profile context, not a live irrigation-control system.
7. **Open Pest Alerts / Advisory.** Show the source title, page, section, excerpt, safety notice, and citation tile. Explain that this is report-extracted data, no dose is shown without explicit report text, and the local source PDF is not portable with the repository snapshot.
8. **Open Satellite and Market.** Explain these are currently mock/placeholder surfaces; no GEE or verified market integration is claimed.
9. **Logout.** The stored access token is removed from secure storage.

## Data Dependency Labels

| Demo area | Dependency/status |
|---|---|
| Login/profile/dashboard | Live backend or mock repository, depending on `USE_MOCKS`. |
| Crop scan | Live backend and correctly configured local model; otherwise safe unavailable state. |
| Weather | Historical NASA POWER CSV when district coverage exists; labeled mock fallback otherwise. |
| Irrigation | Profile/weather-derived guidance; not real-time control. |
| Pest advisory | Live backend plus report-extracted facts/chunks; citations are report-derived. |
| Satellite/market | Mock/placeholder data. |
| Urdu | Locale selection exists; product copy requires further localization work. |

## Verification Before a Demo

```bash
D:\flutter\bin\flutter.bat analyze
D:\flutter\bin\flutter.bat test
```

Final freeze results: analysis clean and 44 Flutter unit/widget tests passing. The preserved debug APK is at `mobile_app/build/app/outputs/flutter-apk/app-debug.apk`; it was not rebuilt during freeze.
