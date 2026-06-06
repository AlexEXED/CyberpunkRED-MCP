#!/usr/bin/env python3
"""build_release.py — 构建 CPRED MCP Server 发布包

用法:
    python build_release.py               # 自动读取 mcp_server/VERSION
    python build_release.py 3.2.0         # 指定版本号

输出:
    release/cyberpunk-red-mcp-v{version}.tar.gz
    release/cyberpunk-red-mcp-v{version}.zip

打包内容（仅 mcp_server/ 下的核心文件）:
    server.py loader.py requirements.txt README.md VERSION
    data/rules/ data/random_tables/ data/source_config.json
"""

import io
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "mcp_server"
RELEASE = ROOT / "release"

PACKAGE_ITEMS = [
    "server.py",
    "loader.py",
    "requirements.txt",
    "README.md",
    "VERSION",
    "data",
]


def get_version() -> str:
    """从命令行参数或 VERSION 文件读取版本号"""
    if len(sys.argv) > 1:
        return sys.argv[1].lstrip("v")
    ver_file = SERVER / "VERSION"
    if ver_file.exists():
        return ver_file.read_text().strip()
    sys.exit("错误: 未找到 VERSION 文件，请指定版本号参数")


def collect_files() -> list[tuple[str, bytes]]:
    """收集打包文件，返回 (归档内相对路径, 字节内容) 列表"""
    result = []
    for name in PACKAGE_ITEMS:
        path = SERVER / name
        if path.is_file():
            result.append((name, path.read_bytes()))
        elif path.is_dir():
            for f in sorted(path.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(SERVER).as_posix()
                    if "__pycache__" in rel:
                        continue
                    result.append((rel, f.read_bytes()))
    return result


def build_tarball(files: list[tuple[str, bytes]], version: str) -> Path:
    """构建 .tar.gz"""
    RELEASE.mkdir(parents=True, exist_ok=True)
    outpath = RELEASE / f"cyberpunk-red-mcp-v{version}.tar.gz"
    with tarfile.open(outpath, "w:gz") as tar:
        for arcname, content in files:
            info = tarfile.TarInfo(name=f"cyberpunk-red-mcp/{arcname}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    print(f"  ✓ {outpath.name} ({outpath.stat().st_size:,} bytes)")
    return outpath


def build_zip(files: list[tuple[str, bytes]], version: str) -> Path:
    """构建 .zip"""
    RELEASE.mkdir(parents=True, exist_ok=True)
    outpath = RELEASE / f"cyberpunk-red-mcp-v{version}.zip"
    with zipfile.ZipFile(outpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, content in files:
            zf.writestr(f"cyberpunk-red-mcp/{arcname}", content)
    print(f"  ✓ {outpath.name} ({outpath.stat().st_size:,} bytes)")
    return outpath


def main():
    version = get_version()
    print(f"构建发布包 v{version} ...")
    files = collect_files()
    print(f"  收集 {len(files)} 个文件")
    build_tarball(files, version)
    build_zip(files, version)
    print(f"完成 → {RELEASE.absolute()}")


if __name__ == "__main__":
    main()
