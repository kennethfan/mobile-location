#!/usr/bin/env python
# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
构建脚本 - 用于本地测试和GitHub Actions
"""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path


class Builder:
    def __init__(self, version=None):
        self.version = version or "1.0.0"
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"

    def clean(self):
        """清理构建文件"""
        for path in [self.dist_dir, self.build_dir]:
            if path.exists():
                for item in path.iterdir():
                    if item.is_file():
                        item.unlink()
                    else:
                        import shutil
                        shutil.rmtree(item)
                print(f"已清理: {path}")

    def install_dependencies(self):
        """安装依赖"""
        print("安装Python依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    def build_windows(self):
        """构建Windows版本"""
        print("构建Windows可执行文件...")

        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", "手机号查询工具",
            "--icon", str(self.project_root / "assets" / "location.png"),
            "--add-data", f"{self.project_root / 'README.md'};.",
            "--distpath", str(self.dist_dir / "windows"),
            str(self.src_dir / "gui.py")
        ]

        subprocess.run(cmd, check=True)
        print("Windows构建完成!")

    def build_linux(self):
        """构建Linux版本"""
        print("构建Linux可执行文件...")

        cmd = [
            "pyinstaller",
            "--onefile",
            "--name", "phone-query-tool",
            "--add-data", f"{self.project_root / 'README.md'}:.",
            "--distpath", str(self.dist_dir / "linux"),
            str(self.src_dir / "gui.py")
        ]

        subprocess.run(cmd, check=True)
        print("Linux构建完成!")

    def build_macos(self):
        """构建macOS版本"""
        print("构建macOS可执行文件...")

        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", "PhoneQueryTool",
            "--add-data", f"{self.project_root / 'README.md'}:.",
            "--osx-bundle-identifier", "com.yourcompany.phonequery",
            "--distpath", str(self.dist_dir / "macos"),
            str(self.src_dir / "gui.py")
        ]

        subprocess.run(cmd, check=True)
        print("macOS构建完成!")

    def build_all(self):
        """构建所有平台"""
        self.clean()
        self.install_dependencies()

        system = platform.system().lower()

        if system == "windows":
            self.build_windows()
        elif system == "linux":
            self.build_linux()
        elif system == "darwin":
            self.build_macos()
        else:
            print(f"不支持的系统: {system}")

    def package_release(self):
        """打包发布文件"""
        print("打包发布文件...")

        for platform_name in ["windows", "linux", "macos"]:
            platform_dir = self.dist_dir / platform_name
            if platform_dir.exists():
                import shutil
                package_name = f"phone-query-tool-v{self.version}-{platform_name}"
                shutil.make_archive(package_name, 'zip' if platform_name == 'windows' else 'gztar',
                                    root_dir=self.dist_dir, base_dir=platform_name)
                print(f"已创建: {package_name}")


def main():
    parser = argparse.ArgumentParser(description="构建手机号查询工具")
    parser.add_argument("--version", "-v", default="1.0.0", help="版本号")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")
    parser.add_argument("--package", action="store_true", help="打包发布文件")

    args = parser.parse_args()

    builder = Builder(args.version)

    if args.clean:
        builder.clean()
    elif args.package:
        builder.package_release()
    else:
        builder.build_all()


if __name__ == "__main__":
    main()
