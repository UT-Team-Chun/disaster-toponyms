"""サードパーティライセンス情報を生成するスクリプト。"""

import json
import re
import subprocess
import sys
from pathlib import Path

PLATFORM_MARKERS = [
    "sys_platform",
    "platform_system",
    "platform_machine",
    "os_name",
]


def get_editable_packages() -> list[str]:
    """編集可能パッケージ（自プロジェクト）の一覧を取得。"""
    result = subprocess.run(
        ["uv", "pip", "list", "--editable"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")
    # ヘッダー2行をスキップ
    return [line.split()[0] for line in lines[2:] if line.strip()]


def get_platform_specific_packages() -> list[str]:
    """uv.lockからOS依存パッケージを抽出。"""
    lock_files = list(Path(".").rglob("uv.lock"))
    platform_packages: set[str] = set()

    pattern = re.compile(r'\{\s*name\s*=\s*"([^"]+)".*marker\s*=\s*"([^"]+)"')

    for lock_file in lock_files:
        content = lock_file.read_text()
        for match in pattern.finditer(content):
            pkg_name, marker = match.groups()
            if any(m in marker for m in PLATFORM_MARKERS):
                platform_packages.add(pkg_name)

    return list(platform_packages)


def run_pip_licenses(exclude_packages: list[str]) -> list[dict]:
    """pip-licensesを実行してライセンス情報を取得。"""
    cmd = [
        "uv",
        "run",
        "--with",
        "pip-licenses",
        "pip-licenses",
        "--format=json",
        "--with-authors",
        "--with-license-file",
        "--no-license-path",
        "--with-notice-file",
    ]
    if exclude_packages:
        cmd.extend(["--ignore-packages", *exclude_packages])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def clean_value(value: str) -> str:
    """UNKNOWNを空文字に変換。"""
    return "" if value == "UNKNOWN" else value


def generate_txt(licenses: list[dict]) -> str:
    """ライセンス情報をテキスト形式に変換。"""
    sections = []
    for pkg in licenses:
        name = pkg.get("Name", "")
        version = pkg.get("Version", "")
        license_type = pkg.get("License", "")
        author = clean_value(pkg.get("Author", ""))
        license_text = clean_value(pkg.get("LicenseText", ""))
        notice_text = clean_value(pkg.get("NoticeText", ""))

        section = f"""{"=" * 60}
{name} {version}
{"=" * 60}
License: {license_type}
Author: {author}

{license_text}
"""
        if notice_text:
            section += f"\nNotice:\n{notice_text}\n"

        sections.append(section)

    return "\n".join(sections)


def main() -> None:
    print("Fetching editable packages...")
    editable_packages = get_editable_packages()
    print("Editable packages to exclude:", editable_packages)

    print("Detecting platform-specific packages...")
    platform_packages = get_platform_specific_packages()
    print("Platform-specific packages to exclude:", platform_packages)

    exclude_packages = list(set(editable_packages + platform_packages))

    print("Running pip-licenses...")
    licenses = run_pip_licenses(exclude_packages)

    print("Writing ThirdPartyNotices.txt...")
    txt_content = generate_txt(licenses)
    with open("ThirdPartyNotices.txt", "w", encoding="utf-8") as f:
        f.write(txt_content)

    print(f"✅ Generated ThirdPartyNotices.txt ({len(licenses)} packages)")


if __name__ == "__main__":
    sys.exit(main() or 0)
