# Android Splash Screen Startup & Hang Diagnosis Report

- **Project:** Kisaan Dost Mobile Application
- **Task:** Splash Screen Hang Diagnosis & Lifecycle Hardening
- **Timestamp (UTC):** `2026-09-02T10:57:00+00:00`
- **Status:** **RESOLVED & VERIFIED**

---

## 1. Executive Summary & Root Cause Analysis

### Identified Root Causes

1. **GoRouter Instance Recreation & Trapped Splash Redirect Loop:**
   - In `app_router.dart`, `appRouterProvider` directly watched `authProvider` via `ref.watch(authProvider)`.
   - On every authentication state mutation (`isLoading: true` $\to$ `isLoading: false`), `appRouterProvider` tore down and rebuilt a brand new `GoRouter` instance with `initialLocation: AppRoutes.splash`.
   - The redirect function evaluated `location == AppRoutes.splash`, but because `location == AppRoutes.splash` was grouped as an auth route, `redirect` returned `null` for unauthenticated states.
   - Consequently, `context.go(AppRoutes.login)` called from `SplashScreen`'s `ref.listen` was discarded when `GoRouter` recreated itself and remounted `SplashScreen`, causing an indefinite splash loop.

2. **Absence of `isInitialized` State in `AuthState`:**
   - `AuthState` previously had only `isLoading` (defaulting to `false`). On app bootstrap before `restoreSession()` began, `redirect` could not distinguish between a freshly booted uninitialized state and an unauthenticated initialized state.
   - Adding `isInitialized: true` upon session restoration completion allows the router to guarantee that the splash screen displays during initialization and immediately navigates away as soon as initialization completes.

3. **Unbounded Network Calls on Physical Devices:**
   - `AuthRepositoryImpl.restoreSession()` previously attempted an HTTP `/auth/me` call using the emulator loopback `http://10.0.2.2:8000`. On physical hardware (Vivo V2318), `10.0.2.2` was unreachable, causing long TCP handshake stalls.
   - Session restoration now uses a bounded 3-second timeout and catches all socket/timeout/platform exceptions gracefully, instantly falling back to unauthenticated mode so the login screen renders immediately.

4. **SecureStorage Platform Keystore Stalls:**
   - `FlutterSecureStorageService` methods now feature comprehensive `try-catch` blocks protecting against Android Keystore / `PlatformException` corruption, ensuring corrupted keystores never block app bootstrap.

---

## 2. Changed Files & Modifications

| File | Change Description |
|---|---|
| [`mobile_app/lib/utils/logger.dart`](file:///d:/KisaanDost/mobile_app/lib/utils/logger.dart) | Added `Logger.startup(...)` stage logging gated by `kDebugMode` for Android Logcat observability. |
| [`mobile_app/lib/main.dart`](file:///d:/KisaanDost/mobile_app/lib/main.dart) | Added structured bootstrap logging. |
| [`mobile_app/lib/services/secure_storage_service.dart`](file:///d:/KisaanDost/mobile_app/lib/services/secure_storage_service.dart) | Added try-catch exception handling around Keystore reads/writes. |
| [`mobile_app/lib/repositories/auth_repository_impl.dart`](file:///d:/KisaanDost/mobile_app/lib/repositories/auth_repository_impl.dart) | Bounded session verification with 3s timeout and safe fallback to `null` on network errors. |
| [`mobile_app/lib/providers/auth_provider.dart`](file:///d:/KisaanDost/mobile_app/lib/providers/auth_provider.dart) | Added `isInitialized` flag to `AuthState` and lifecycle logging to `AuthNotifier`. |
| [`mobile_app/lib/routing/app_router.dart`](file:///d:/KisaanDost/mobile_app/lib/routing/app_router.dart) | Replaced router-recreation pattern with `RouterNotifier` and `refreshListenable`, resolving redirect rules. |
| [`mobile_app/lib/screens/splash_screen.dart`](file:///d:/KisaanDost/mobile_app/lib/screens/splash_screen.dart) | Hardened lifecycle with clean reactive listener, error states, retry action, and fallback buttons. |
| [`mobile_app/test/widget/splash_navigation_test.dart`](file:///d:/KisaanDost/mobile_app/test/widget/splash_navigation_test.dart) | Added automated test suite covering session success, empty storage, and unreachable backend. |

---

## 3. Before vs. After Startup Behavior

```
BEFORE:
App Launch -> SplashScreen mounts -> restoreSession() triggers -> authProvider updates
  -> appRouterProvider recreates GoRouter -> Reset to initialLocation ('/')
  -> SplashScreen remounts -> Infinite loop or 20s stall on unreachable 10.0.2.2:8000 -> HANGS

AFTER:
App Launch -> Logger: [STARTUP] Bootstrap -> RouterNotifier monitors AuthState
  -> SplashScreen mounts -> restoreSession() verifies token within 3s
  -> If valid token: AuthState(user: user, isInitialized: true) -> Router redirects to /dashboard
  -> If no token or network offline: AuthState(user: null, isInitialized: true) -> Router redirects to /login
  -> If error occurs: User receives friendly retry button and "Continue to Login"
  -> Never hangs on splash screen.
```

---

## 4. Test & Verification Results

| Suite | Command | Result |
|---|---|---|
| **Splash Navigation Tests** | `flutter test test/widget/splash_navigation_test.dart` | **3 / 3 PASS** |
| **Full Flutter Test Suite** | `flutter test` (all unit & widget tests) | **79 / 79 PASS (16.0s)** |
| **Flutter Static Analysis** | `flutter analyze` | **0 issues (CLEAN)** |
| **Handoff Completeness Gate** | `python scripts/check_handoff_completeness.py` | **COMPLETE (`safe_for_feature_continuation: true`)** |
