# Android Build Troubleshooting Guide — Impeller & Security Policy Workaround

- **Project:** Kisaan Dost Agricultural Platform (Mobile Client)
- **Target OS:** Android (SDK 34+)
- **Flutter Framework:** 3.x+ (Dart 3.x+)

---

## 1. Problem Description & Root Cause

### Symptom:
When running `flutter run` or building an APK in Android Studio / CLI, the build fails at `:app:compileFlutterBuildDebug` or `:app:compileFlutterBuildRelease` with the following error:

```text
ProcessException: An Application Control policy has been blocked this file
  .../bin/cache/artifacts/engine/android-arm64-release/impellerc.exe
Command: .../impellerc.exe --sl=... --spirv=...
Task :app:compileFlutterBuildDebug FAILED
```

### Root Cause:
1. Windows Application Control (WDAC), AppLocker, or enterprise antivirus policies block Flutter's temporary native execution of `impellerc.exe` (the offline shader compiler for the Impeller rendering backend).
2. Because `impellerc.exe` is blocked by OS policy, shader pre-compilation fails and aborts Gradle compilation.

---

## 2. Permanent Solution: Disable Impeller (Fallback to Skia)

Disabling Impeller switches Flutter back to the mature, highly optimized **Skia** rendering engine, which does not require offline `impellerc.exe` shader compilation.

### Step 1: Update `AndroidManifest.xml`
In `mobile_app/android/app/src/main/AndroidManifest.xml`, ensure the following metadata elements are inside the `<application>` tag:

```xml
<application
    android:label="kisaan_dost"
    android:name="${applicationName}"
    android:icon="@mipmap/ic_launcher">

    <!-- Disable Impeller and force Skia renderer -->
    <meta-data
        android:name="io.flutter.embedded_views_preview"
        android:value="true" />
    <meta-data
        android:name="flutter.enable-impeller"
        android:value="false" />

    <!-- Activity definitions -->
    ...
</application>
```

### Step 2: Update `gradle.properties`
In `mobile_app/android/gradle.properties`, add Java module opens to prevent JVM reflective access warnings and memory bottlenecks:

```properties
org.gradle.jvmargs=-Xmx8G -XX:MaxMetaspaceSize=4G -XX:ReservedCodeCacheSize=512m -XX:+HeapDumpOnOutOfMemoryError --add-opens java.base/java.lang=ALL-UNNAMED
android.useAndroidX=true
```

### Step 3: Use `--no-enable-impeller` CLI Flag

When building or running from the command line:

#### Debug Run on Physical Device (e.g. Vivo V2318):
```bash
flutter run --no-enable-impeller
```

#### Release APK Build:
```bash
flutter build apk --release --no-enable-impeller
```

---

## 3. Alternative Security Policy Exclusions (Optional)

If Impeller is desired in the future:
1. **Windows Security Exclusion:** Add the Flutter SDK root directory (e.g. `D:\flutter`) and Android SDK directory (`%LOCALAPPDATA%\Android\Sdk`) to Windows Defender *Virus & threat protection settings > Exclusions*.
2. **AppLocker / WDAC Rule:** Create a path rule allowing binaries inside `D:\flutter\bin\cache\artifacts\engine\**\impellerc.exe`.

---

## 4. Build Verification & Device Compatibility

| Parameter | Recommended Specification |
|---|---|
| **Android SDK Version** | `compileSdkVersion 34`, `targetSdkVersion 34`, `minSdkVersion 21` |
| **Java Development Kit** | OpenJDK 17 or 21 (`--add-opens java.base/java.lang=ALL-UNNAMED`) |
| **Renderer** | Skia Engine (`flutter.enable-impeller=false`) |
| **Physical Device Verification** | Verified on ARM64 devices (including Vivo V2318) |
| **Shader Compilation** | Zero runtime shader errors, faster incremental build times |
