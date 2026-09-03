# Android & Local Backend Setup Guide

- **Project:** Kisaan Dost MVP
- **Timestamp (UTC):** `2026-09-01T20:25:00+00:00`
- **Scope:** Complete guide for connecting the Flutter Android application to the local FastAPI backend in both Emulator and Physical Device configurations.

---

## 1. Overview of Operating Modes

The Kisaan Dost mobile application supports two operating modes controlled at compile time via `--dart-define`:

| Mode | `--dart-define` Flags | Description |
|---|---|---|
| **Mock Mode** | `USE_MOCKS=true` | Runs with local mock data generators. No backend or network connectivity required. Ideal for UI and layout demos. |
| **Live Mode (Emulator)** | `USE_MOCKS=false`<br>`API_BASE_URL=http://10.0.2.2:8000` | Connects directly to the local FastAPI backend running on the host machine. |
| **Live Mode (Physical Device)** | `USE_MOCKS=false`<br>`API_BASE_URL=http://<HOST_LAN_IP>:8000` | Connects over Wi-Fi / Local Area Network to the development host. |
| **Live Mode (Secure Tunnel)** | `USE_MOCKS=false`<br>`API_BASE_URL=https://<tunnel>.ngrok-free.app` | Connects over an HTTPS secure tunnel. |

---

## 2. Step-by-Step Local Backend Setup

### Step 1: Start FastAPI
From the repository root on the host machine:

```powershell
python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
```

> **Why `0.0.0.0`?** Binding to `0.0.0.0` allows the server to accept connections from both `127.0.0.1` (localhost), the Android emulator virtual router (`10.0.2.2`), and external physical devices on the local subnet.

### Step 2: Verify Backend Health
Open a browser or terminal on the host machine:

```powershell
curl http://localhost:8000/health
# Response: {"status":"ok","timestamp":"...","app":"Kisaan Dost MVP"}
```

---

## 3. Connecting from Android Emulator

Android emulators run inside a virtual network isolated from the host. In this environment:
- `127.0.0.1` refers to the emulator device itself.
- `10.0.2.2` is the special virtual router alias provided by Android to reach the host's `127.0.0.1`.

### Run Command:
From the `mobile_app` directory:

```bash
flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

---

## 4. Connecting from a Physical Android Device

### Step 1: Verify Host LAN IP
On Windows PowerShell:
```powershell
ipconfig
# Locate the IPv4 Address under your active Wi-Fi or Ethernet adapter (e.g., 192.168.1.105)
```

### Step 2: Ensure Firewall & Network Reachability
- Connect your Android phone to the **same Wi-Fi network** as your development PC.
- Ensure Windows Defender Firewall allows incoming TCP connections on port `8000` for Private Networks.
- Test connection from phone's browser by navigating to `http://<HOST_LAN_IP>:8000/health`.

### Step 3: Run Flutter on Physical Device
```bash
flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=http://<HOST_LAN_IP>:8000
```

### Alternative: Reverse Port Forwarding via ADB
If connecting via USB cable with USB Debugging enabled:
```powershell
adb reverse tcp:8000 tcp:8000
```
Then you can run the app using `localhost`:
```bash
flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=http://localhost:8000
```

---

## 5. Security & Build Policies

1. **Cleartext Traffic Policy:**
   - Development builds permit local HTTP communication to `10.0.2.2` and private LAN subnets.
   - Main manifest [`mobile_app/android/app/src/main/AndroidManifest.xml`](file:///d:/KisaanDost/mobile_app/android/app/src/main/AndroidManifest.xml) includes `<uses-permission android:name="android.permission.INTERNET"/>`.
2. **Release Build HTTPS Enforcement:**
   - In release builds, `AppConfig.requireHttps` asserts that `API_BASE_URL` begins with `https://`.
   - Cleartext HTTP is disallowed for production/release APKs.
3. **No Embedded Secrets Policy:**
   - Default configurations use placeholder or loopback URLs; no production tokens, private keys, or API secrets are committed in source code.
   - JWT tokens are stored exclusively in `flutter_secure_storage` and cleared immediately upon logout or HTTP 401.

---

## 6. Common Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `SocketException: Connection refused (OS Error: errno = 111)` | Backend not running or wrong IP | Verify `uvicorn` is running with `--host 0.0.0.0 --port 8000`. In emulator, ensure using `http://10.0.2.2:8000`. |
| `SocketException: Connection timed out` | Host firewall blocking port 8000 | Add an inbound firewall rule in Windows Defender for port 8000 TCP on Private Networks. |
| `HTTP 401 Unauthorized` | Missing or expired JWT token | Stored token has expired. Log in again; app automatically clears token and routes to `/login`. |
| `HTTP 503 Disease model not available` | Model path resolution failed | Verify `app/config/settings.py` points to `Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt`. |
