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
print("Android application label, campus icon and INTERNET permission configured")
