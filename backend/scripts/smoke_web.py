"""使用本机 Edge 运行完整 H5 演示；自动结束测试服务。"""

import json
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
EDGE = Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / (
    "Microsoft/Edge/Application/msedge.exe"
)


def main():
    ARTIFACTS.mkdir(exist_ok=True)
    report = ARTIFACTS / "browser-result.json"
    report.unlink(missing_ok=True)
    screenshot = ARTIFACTS / "web-demo.png"
    screenshot.unlink(missing_ok=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    environment = {**os.environ, "CAMPUS_DEMO": "1"}
    environment.pop("CAMPUS_KNOWLEDGE_DIR", None)
    if not EDGE.is_file():
        raise RuntimeError("未找到本机 Edge")
    harness = ROOT.parent / "web" / f".smoke-{uuid.uuid4().hex}.html"
    harness.write_text((ROOT / "scripts/web-smoke.html").read_text(encoding="utf-8"), encoding="utf-8")
    with (ARTIFACTS / "server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--serve", str(port)],
            cwd=ROOT, env=environment, stdout=log, stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("测试服务未启动，请检查 artifacts/server.log")
                try:
                    with urlopen(url + "/health", timeout=1):
                        break
                except URLError:
                    time.sleep(0.1)
            else:
                raise TimeoutError("测试服务启动超时")
            result = subprocess.run(
                [str(EDGE), "--headless=new", "--disable-gpu", "--no-first-run",
                 "--disable-extensions", "--no-proxy-server",
                 f"--user-data-dir={ARTIFACTS / 'edge-profile'}",
                 "--window-size=480,1000", "--virtual-time-budget=20000", "--dump-dom",
                 f"--screenshot={screenshot}",
                 url + "/web/" + harness.name],
                capture_output=True, timeout=60, check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            rendered = result.stdout.decode("utf-8", errors="replace")
            (ARTIFACTS / "edge.log").write_text(
                result.stderr.decode("utf-8", errors="replace"), encoding="utf-8"
            )
            (ARTIFACTS / "web-smoke-result.html").write_text(rendered, encoding="utf-8")
            # Windows Edge 启动器可能先返回，等待测试页回传结果后才关闭服务。
            for _ in range(300):
                if report.exists():
                    break
                time.sleep(0.1)
            else:
                raise TimeoutError("Edge 未回传结果，请检查 artifacts/server.log")
            assert json.loads(report.read_text(encoding="utf-8"))["status"] == "PASS"
            for _ in range(100):
                if screenshot.exists() and screenshot.stat().st_size > 0:
                    break
                time.sleep(0.1)
            else:
                raise TimeoutError("Edge 未输出截图")
            print("H5 smoke: card, checklist, category refusal and literal input passed")
        finally:
            harness.unlink(missing_ok=True)
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def serve(port: int):
    import uvicorn
    from fastapi import Request

    from campus_assistant.main import create_app
    from campus_assistant.repositories.knowledge import KnowledgeRepository

    application = create_app(KnowledgeRepository.load(ROOT / "examples"), demo_mode=True)

    @application.post("/_browser_result", include_in_schema=False)
    async def browser_result(request: Request):
        result = await request.json()
        (ARTIFACTS / "browser-result.json").write_text(json.dumps(result), encoding="utf-8")
        return {"ok": True}

    uvicorn.run(application, host="127.0.0.1", port=port)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        serve(int(sys.argv[2]))
    else:
        main()
