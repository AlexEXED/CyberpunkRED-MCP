# -*- coding: utf-8 -*-
"""build_release.py — 构建神谕引擎发布包

打包 oracle/ 目录的公开内容（README + 模板），不含版权数据。

用法:
    python build_release.py            # 自动读取 oracle/VERSION
    python build_release.py 1.0.0      # 指定版本

输出:
    release/oracle-engine-v{version}.tar.gz
    release/oracle-engine-v{version}.zip
"""

import io
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORACLE = ROOT / "oracle"
RELEASE = ROOT / "release"

PACKAGE_ITEMS = [
    "README.md",
    "template.json",
]


def get_version() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1].lstrip("v").lstrip("oracle-")
    ver_file = ORACLE / "VERSION"
    if ver_file.exists():
        return ver_file.read_text().strip()
    return "1.0.0"


def collect_files() -> list[tuple[str, bytes]]:
    result = []
    for name in PACKAGE_ITEMS:
        path = ORACLE / name
        if path.is_file():
            result.append((name, path.read_bytes()))
    return result


def build_tarball(files, version) -> Path:
    RELEASE.mkdir(parents=True, exist_ok=True)
    outpath = RELEASE / f"oracle-engine-v{version}.tar.gz"
    with tarfile.open(outpath, "w:gz") as tar:
        for arcname, content in files:
            info = tarfile.TarInfo(name=f"oracle-engine/{arcname}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    print(f"  ✓ {outpath.name} ({outpath.stat().st_size:,} bytes)")
    return outpath


def build_zip(files, version) -> Path:
    RELEASE.mkdir(parents=True, exist_ok=True)
    outpath = RELEASE / f"oracle-engine-v{version}.zip"
    with zipfile.ZipFile(outpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, content in files:
            zf.writestr(f"oracle-engine/{arcname}", content)
    print(f"  ✓ {outpath.name} ({outpath.stat().st_size:,} bytes)")
    return outpath


def main():
    version = get_version()
    print(f"构建神谕引擎发布包 v{version} ...")
    files = collect_files()
    print(f"  收集 {len(files)} 个文件: {[f[0] for f in files]}")
    build_tarball(files, version)
    build_zip(files, version)
    print(f"完成 → {RELEASE.absolute()}")


if __name__ == "__main__":
    main()
