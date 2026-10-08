"""配置 Flutter 生成的 Android 平台目录，供本地与 CI 共用。"""

from pathlib import Path
import xml.etree.ElementTree as ET

ANDROID = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID)
manifest = Path(__file__).resolve().parents[1] / "mobile/android/app/src/main/AndroidManifest.xml"
root = ET.parse(manifest)
application = root.getroot().find("application")
if application is None:
    raise ValueError("Android application 配置缺失")
application.set(f"{{{ANDROID}}}label", "校园万事通")
if not any(
    permission.get(f"{{{ANDROID}}}name") == "android.permission.INTERNET"
    for permission in root.getroot().findall("uses-permission")
):
    ET.SubElement(root.getroot(), "uses-permission", {f"{{{ANDROID}}}name": "android.permission.INTERNET"})
root.write(manifest, encoding="utf-8", xml_declaration=True)
print("Android application label and INTERNET permission configured")
