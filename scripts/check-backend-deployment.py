"""验证 HTTP(S) 后端健康、演示状态和无依据拒答，无第三方依赖。"""

import argparse
import json
import uuid
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    with urlopen(base + "/health", timeout=15) as response:
        health = json.load(response)
    assert health["status"] == "ok", health
    assert health["demo_mode"] is False, "服务器不应开启虚构演示数据"
    payload = {"question": "deployment_probe_" + uuid.uuid4().hex}
    request = Request(
        base + "/api/v1/chat", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=15) as response:
        answer = json.load(response)
    assert answer["status"] == "refusal", answer
    assert answer["card"] is None and answer["sources"] == [], answer
    print(f"Backend smoke passed: health=ok, demo=false, knowledge={health['knowledge_status']}")


if __name__ == "__main__":
    main()
