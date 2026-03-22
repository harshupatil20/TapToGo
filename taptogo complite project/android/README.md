# NFC Integration for TapToGo Android Build

## 1. Add NFC to AndroidManifest.xml

After running `flet build apk`, edit the generated `build/android/.../app/src/main/AndroidManifest.xml`:

**Inside `<manifest>` add:**
```xml
<uses-permission android:name="android.permission.NFC"/>
<uses-feature android:name="android.hardware.nfc" android:required="false"/>
```

**Inside the MainActivity `<activity>` add:**
```xml
<intent-filter>
    <action android:name="android.nfc.action.NDEF_DISCOVERED"/>
    <action android:name="android.nfc.action.TAG_DISCOVERED"/>
    <action android:name="android.nfc.action.TECH_DISCOVERED"/>
    <category android:name="android.intent.category.DEFAULT"/>
</intent-filter>
```

## 2. Replace MainActivity.kt

Replace the generated MainActivity.kt with the version in this folder. The Kotlin file writes the NFC tag UID (e.g. `04:A3:2F:BC`) to `filesDir/nfc_scan.tmp`. The Flet Tap screen polls this file every second.

Path: `android/app/src/main/kotlin/com/taptogo/taptogo/MainActivity.kt`

**Note:** Update the package name in MainActivity.kt if your org/project in pyproject.toml differs (e.g. `com.taptogo.taptogo`).

## 3. Build

```bash
cd taptogo
flet build apk
```

Then apply the manifest and MainActivity changes above to the generated project, and rebuild with Flutter/Android Studio if needed. Or use a custom template via `--template-dir` pointing to a modified copy of the flet-build-template.
