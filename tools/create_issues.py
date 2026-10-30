#!/usr/bin/env python3
"""为 ai-personal-profile 创建标签与 6 个待办 Issue。

用法（Windows Git Bash / macOS / Linux 均可）：
    GH_TOKEN=ghp_xxxx python tools/create_issues.py

可选环境变量：
    OWNER   默认 2295593737
    REPO    默认 ai-personal-profile

脚本可重复执行：已存在的同名 Issue 会跳过，不会产生重复。
需要令牌具有 Issues: write 权限（classic PAT 勾 repo 即可）。
"""

import json
import os
import sys
import urllib.error
import urllib.request

OWNER = os.environ.get("OWNER", "2295593737")
REPO = os.environ.get("REPO", "ai-personal-profile")
TOKEN = os.environ.get("GH_TOKEN", "").strip()

if not TOKEN:
    sys.exit("缺少 GH_TOKEN。示例：GH_TOKEN=ghp_xxx python tools/create_issues.py")

API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))

LABELS = [
    ("profile", "0366d6", "档案内容的补充或修订"),
    ("待填充", "d4c5f9", "章节尚为示例条目，等待填入真实内容"),
    ("阻塞", "b60205", "缺少信息或权限，暂时无法推进"),
]

ISSUES = [
    ("[档案] 1. 个人简介与背景", "01-intro.md"),
    ("[档案] 2. 工作与学习习惯", "02-habits.md"),
    ("[档案] 3. 沟通风格偏好", "03-communication.md"),
    ("[档案] 4. 常用工具与技术栈", "04-toolchain.md"),
    ("[档案] 5. 项目经验与成果", "05-projects.md"),
    ("[档案] 6. 长期目标", "06-goals.md"),
]


def call(method, path, payload=None):
    url = f"{API}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body


def ensure_labels():
    for name, color, desc in LABELS:
        status, _ = call("POST", f"/repos/{OWNER}/{REPO}/labels",
                         {"name": name, "color": color, "description": desc})
        if status in (201, 422):  # 422 = 已存在
            print(f"  标签 {name}: {'已就绪' if status == 201 else '已存在'}")
        else:
            print(f"  标签 {name}: 失败 {status}")


def existing_titles():
    status, data = call("GET", f"/repos/{OWNER}/{REPO}/issues?state=all&per_page=100")
    if status != 200 or not isinstance(data, list):
        return set()
    return {i.get("title") for i in data if "pull_request" not in i}


def main():
    status, _ = call("GET", f"/repos/{OWNER}/{REPO}")
    if status != 200:
        sys.exit(f"无法访问 {OWNER}/{REPO}（HTTP {status}）。请检查令牌权限。")

    print("==> 创建标签")
    ensure_labels()

    print("==> 创建 Issue")
    have = existing_titles()
    created = 0
    for title, filename in ISSUES:
        if title in have:
            print(f"  跳过（已存在）：{title}")
            continue
        path = os.path.join(HERE, "issues", filename)
        with open(path, encoding="utf-8") as f:
            body = f.read()
        status, data = call("POST", f"/repos/{OWNER}/{REPO}/issues",
                            {"title": title, "body": body, "labels": ["profile", "待填充"]})
        if status == 201:
            print(f"  已创建：{title} -> {data['html_url']}")
            created += 1
        else:
            print(f"  失败：{title}（HTTP {status}）{data}")

    print(f"\n完成，新建 {created} 个 Issue。")
    print(f"看板：https://github.com/{OWNER}/{REPO}/issues")


if __name__ == "__main__":
    main()
