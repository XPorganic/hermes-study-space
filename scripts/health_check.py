#!/usr/bin/env python3
"""Hermes 研究日志服务器健康检查脚本 — 如果服务器挂了则自动重启"""
import subprocess, sys, os, time
from datetime import datetime

LOG_DIR = os.path.expanduser("~/hermes-study-space")
LOG_FILE = os.path.join(LOG_DIR, "health_check.log")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def check_and_restart():
    # 1. 检查进程是否存在
    result = subprocess.run(
        ["pgrep", "-f", "python3.*server\\.py"],
        capture_output=True, text=True, timeout=10
    )
    running_pids = result.stdout.strip().split()
    
    # 2. 检查端口是否可达
    curl = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", "5", "http://localhost:8765/"],
        capture_output=True, text=True, timeout=10
    )
    http_code = curl.stdout.strip()

    if http_code and http_code not in ("000", ""):
        log(f" ✅ 服务器正常 (PID={', '.join(running_pids)}, HTTP {http_code})")
        return True
    
    # 3. 有进程但端口不通 → 杀僵尸
    if running_pids:
        for pid in running_pids:
            subprocess.run(["kill", pid], timeout=5)
            log(f" 🗡️ 杀死僵尸进程 PID={pid}")
        time.sleep(1)
    
    # 4. 重启
    server_script = os.path.join(LOG_DIR, "server.py")
    if not os.path.exists(server_script):
        log(f" ❌ 找不到 {server_script}，无法重启")
        return False
    
    with open(os.path.join(LOG_DIR, "server.log"), "a") as lf:
        subprocess.Popen(
            ["python3", server_script],
            cwd=LOG_DIR,
            stdout=lf, stderr=lf,
            start_new_session=True
        )
    
    # 等待启动
    time.sleep(3)
    
    # 验证
    verify = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", "5", "http://localhost:8765/"],
        capture_output=True, text=True, timeout=10
    )
    new_code = verify.stdout.strip()
    if new_code and new_code not in ("000", ""):
        log(f" ✅ 自愈成功！服务器已重启 (HTTP {new_code})")
        return True
    else:
        log(f" ❌ 自愈失败，端口仍不可达")
        return False

if __name__ == "__main__":
    log("═══ 健康检查开始 ═══")
    ok = check_and_restart()
    sys.exit(0 if ok else 1)
