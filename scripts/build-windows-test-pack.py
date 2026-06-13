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

2. 可选：双击 download-offline-components.cmd。
   它会把 Node.js 和 Git Bash 便携组件下载到当前文件夹。网络慢时，安装器会优先使用这些本地组件。

3. 双击 Hermes-zh-CN-Setup.exe。
   安装窗口会停留，失败时截图完整窗口。

4. 安装完成后重新打开 Hermes，检查桌面快捷方式和中文界面。

当前包包含的关键修复：
- 自动准备 Node.js 22，优先国内镜像，并有固定版本兜底。
- 自动准备便携 Git Bash，优先国内镜像，并有固定 MinGit 兜底。
- 支持把 Node.js / MinGit 压缩包放在 EXE 同目录，安装时优先读取本地组件。
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


DOWNLOAD_OFFLINE_COMPONENTS = r"""@echo off
setlocal
chcp 65001 >nul
title Hermes 中文增强离线组件下载
cd /d "%~dp0"
echo Hermes 中文增强离线组件下载
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$ProgressPreference='SilentlyContinue';" ^
  "function GetOne($name,$urls){ $out=Join-Path (Get-Location) $name; foreach($u in $urls){ try{ Write-Host ('正在下载 ' + $name + ': ' + $u); $curl=Get-Command curl.exe -ErrorAction SilentlyContinue; if($curl){ & $curl.Source -L --fail --connect-timeout 20 --max-time 360 --retry 2 --retry-delay 2 -o $out $u; if($LASTEXITCODE -ne 0){ throw ('curl.exe 退出码 ' + $LASTEXITCODE) } } else { Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $out -TimeoutSec 300 }; if((Test-Path $out) -and ((Get-Item $out).Length -gt 0)){ return }; throw '下载文件为空' } catch { Write-Host '当前入口不可用或过慢，正在切换下一个入口。' } }; throw ($name + ' 下载失败') };" ^
  "GetOne 'node-v22.22.3-win-x64.zip' @('https://cdn.npmmirror.com/binaries/node/v22.22.3/node-v22.22.3-win-x64.zip','https://nodejs.org/dist/v22.22.3/node-v22.22.3-win-x64.zip');" ^
  "GetOne 'MinGit-2.54.0-64-bit.zip' @('https://registry.npmmirror.com/-/binary/git-for-windows/v2.54.0.windows.1/MinGit-2.54.0-64-bit.zip','https://mirrors.tuna.tsinghua.edu.cn/github-release/git-for-windows/git/LatestRelease/MinGit-2.54.0-64-bit.zip')"
if errorlevel 1 (
  echo.
  echo 离线组件下载失败。可以稍后再试，也可以直接运行安装器。
  pause
  exit /b 1
)
echo.
echo 离线组件已准备好。现在可以运行 Hermes-zh-CN-Setup.exe。
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
    (pack_dir / "download-offline-components.cmd").write_text(DOWNLOAD_OFFLINE_COMPONENTS, encoding="utf-8")

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
