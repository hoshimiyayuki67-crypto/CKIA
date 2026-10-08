"""配置 Flutter 生成的 Android 平台目录，供本地与 CI 共用。"""

import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID)
manifest = Path(__file__).resolve().parents[1] / "mobile/android/app/src/main/AndroidManifest.xml"
root = ET.parse(manifest)
application = root.getroot().find("application")
if application is None:
    raise ValueError("Android application 配置缺失")
application.set(f"{{{ANDROID}}}label", "校园万事通")
application.set(f"{{{ANDROID}}}icon", "@drawable/campus_icon")
application.set(f"{{{ANDROID}}}allowBackup", "false")
drawable = manifest.parent / "res" / "drawable"
drawable.mkdir(parents=True, exist_ok=True)
(drawable / "campus_icon.xml").write_text('''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#257E67"
        android:pathData="M24,0 L84,0 Q108,0 108,24 L108,84 Q108,108 84,108 L24,108 Q0,108 0,84 L0,24 Q0,0 24,0 Z" />
    <path android:fillColor="#FFFFFF"
        android:pathData="M20,48 L54,30 L88,48 L54,66 Z M32,60 L32,75 Q54,88 76,75 L76,60 L54,72 Z M86,51 L90,51 L90,74 L86,74 Z" />
</vector>
''', encoding="utf-8")
if not any(
    permission.get(f"{{{ANDROID}}}name") == "android.permission.INTERNET"
    for permission in root.getroot().findall("uses-permission")
):
    ET.SubElement(root.getroot(), "uses-permission", {f"{{{ANDROID}}}name": "android.permission.INTERNET"})
root.write(manifest, encoding="utf-8", xml_declaration=True)
for permission in ("POST_NOTIFICATIONS", "RECEIVE_BOOT_COMPLETED"):
    full = "android.permission." + permission
    if not any(node.get(f"{{{ANDROID}}}name") == full
               for node in root.getroot().findall("uses-permission")):
        ET.SubElement(root.getroot(), "uses-permission", {f"{{{ANDROID}}}name": full})
for receiver, actions in (
    ("ScheduledNotificationReceiver", ()),
    ("ScheduledNotificationBootReceiver", ("android.intent.action.BOOT_COMPLETED",
                                          "android.intent.action.MY_PACKAGE_REPLACED")),
):
    full = "com.dexterous.flutterlocalnotifications." + receiver
    if not any(node.get(f"{{{ANDROID}}}name") == full for node in application.findall("receiver")):
        node = ET.SubElement(application, "receiver", {f"{{{ANDROID}}}name": full,
                                                      f"{{{ANDROID}}}exported": "false"})
        if actions:
            intent = ET.SubElement(node, "intent-filter")
            for action in actions:
                ET.SubElement(intent, "action", {f"{{{ANDROID}}}name": action})
queries = root.getroot().find("queries")
if queries is None:
    queries = ET.SubElement(root.getroot(), "queries")
for scheme in ("https", "http"):
    intent = ET.SubElement(queries, "intent")
    ET.SubElement(intent, "action", {f"{{{ANDROID}}}name": "android.intent.action.VIEW"})
    ET.SubElement(intent, "data", {f"{{{ANDROID}}}scheme": scheme})
root.write(manifest, encoding="utf-8", xml_declaration=True)
(drawable / "campus_notification.xml").write_text('''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M2,9 L12,3 L22,9 L12,15 Z M6,13 L6,18 Q12,22 18,18 L18,13 L12,17 Z" />
</vector>\n''', encoding="utf-8")
raw = manifest.parent / "res" / "raw"
raw.mkdir(parents=True, exist_ok=True)
(raw / "keep.xml").write_text('''<resources xmlns:tools="http://schemas.android.com/tools"
    tools:keep="@drawable/campus_notification,@drawable/campus_icon" />\n''', encoding="utf-8")
gradle = manifest.parents[2] / "build.gradle.kts"
content = gradle.read_text(encoding="utf-8")
content = content.replace("minSdk = flutter.minSdkVersion", "minSdk = 24")
if "isCoreLibraryDesugaringEnabled" not in content:
    content = content.replace("compileOptions {", "compileOptions {\n        isCoreLibraryDesugaringEnabled = true")
if "text-recognition-chinese" not in content:
    content += '''
dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
    implementation("com.google.mlkit:text-recognition-chinese:16.0.1")
}
'''
gradle.write_text(content, encoding="utf-8")
rules = gradle.parent / "campus-proguard-rules.pro"
rules.write_text('''# The OCR plugin references optional scripts; this app only calls Chinese.
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**
''', encoding="utf-8")
if "campus-proguard-rules.pro" not in content:
    content += '''
android {
    buildTypes {
        getByName("release") {
            proguardFiles("campus-proguard-rules.pro")
        }
    }
}
'''
    gradle.write_text(content, encoding="utf-8")
print("Android configured: offline Chinese OCR, local reminders, private storage")
