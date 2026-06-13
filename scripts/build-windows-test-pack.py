#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT.parent.parent / "promo_work" / "hermes-zh-cn" / "outputs"


FILES = {
    "Hermes-zh-CN-Setup.exe": ROOT / "Hermes-zh-CN-Setup.exe",
    "HermesZhCNSetup.exe": ROOT / "HermesZhCNSetup.exe",
    "install.ps1": ROOT / "install.ps1",
    "install.sh": ROOT / "install.sh",
    "install-windows.cmd": ROOT / "install-windows.cmd",
    "scripts/verify-windows.ps1": ROOT / "scripts" / "verify-windows.ps1",
}


README = """Hermes 中文增强 Windows 测试包

测试顺序：

1. 双击 run-self-check.cmd。
   看到“windows verification passed”或没有红色错误后继续。

2. 双击 Hermes-zh-CN-Setup.exe。
   安装窗口会停留，失败时截图完整窗口。

3. 安装完成后重新打开 Hermes，检查桌面快捷方式和中文界面。

当前包包含的关键修复：
- 自动准备 Node.js 22，优先国内镜像，并有固定版本兜底。
- 自动准备便携 Git Bash，优先国内镜像，并有固定 MinGit 兜底。
- 备用安装入口使用 main，避免回到旧安装器。

如果失败，请把窗口文字和 CHECKSUMS.json 一起发回。
"""


RUN_SELF_CHECK = """@echo off
setlocal
chcp 65001 >nul
title Hermes 中文增强 Windows 自检
cd /d "%~dp0"
echo Hermes 中文增强 Windows 自检
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\\verify-windows.ps1" -BaseUrl "https://raw.githubusercontent.com/fresh-claw/hermes-cn/main"
if errorlevel 1 (
  echo.
  echo 自检失败。请把这个窗口截图发给小马。
  pause
  exit /b 1
)
echo.
echo 自检完成。现在可以运行 Hermes-zh-CN-Setup.exe。
pause
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="windows-test-pack-20260613-main-fallback")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    pack_dir = args.output_root / args.name
    zip_path = pack_dir.with_suffix(".zip")
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    if zip_path.exists():
        zip_path.unlink()
    pack_dir.mkdir(parents=True)

    file_rows = []
    for rel, src in FILES.items():
        if not src.exists():
            raise SystemExit(f"missing source file: {src}")
        dst = pack_dir / rel
        copy_file(src, dst)
        file_rows.append({"file": rel, "size": dst.stat().st_size, "sha256": sha256(dst)})

    (pack_dir / "README.txt").write_text(README, encoding="utf-8")
    (pack_dir / "run-self-check.cmd").write_text(RUN_SELF_CHECK, encoding="utf-8")

    manifest = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": str(ROOT),
        "files": file_rows,
        "expected": {
            "windows_exe_sha256": sha256(pack_dir / "Hermes-zh-CN-Setup.exe"),
            "install_ps1_sha256": sha256(pack_dir / "install.ps1"),
            "install_sh_sha256": sha256(pack_dir / "install.sh"),
            "verify_windows_sha256": sha256(pack_dir / "scripts" / "verify-windows.ps1"),
        },
    }
    (pack_dir / "CHECKSUMS.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(pack_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(pack_dir).as_posix())

    result = {
        "directory": str(pack_dir),
        "zip": str(zip_path),
        "zip_size": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "windows_exe_sha256": manifest["expected"]["windows_exe_sha256"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
