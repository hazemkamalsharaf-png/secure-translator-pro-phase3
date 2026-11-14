import os
import shutil
import subprocess


def build():
    project_root = os.path.abspath(os.path.dirname(__file__))
    dist_dir = os.path.join(project_root, "dist")
    build_dir = os.path.join(project_root, "build")
    spec_file = os.path.join(project_root, "SecureTranslatorPro.spec")
    app_name = "SecureTranslatorPro"

    # مسح الفولدرات القديمة وملف الـ spec القديم قبل البناء
    for item in [dist_dir, build_dir, spec_file]:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)

    print(f"🚀 Starting build for {app_name}...")

    # استخدام os.pathsep لضمان التوافق مع Windows (;) و Linux/macOS (:)
    add_data_arg = f"{os.path.join(project_root, 'data')}{os.pathsep}data"

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={app_name}",
        "--paths", project_root,
        "--collect-submodules", "ui",
        "--collect-submodules", "core",
        "--collect-submodules", "data",
        "--add-data", add_data_arg,
        "--collect-all", "customtkinter",
        os.path.join(project_root, "main.py"),
    ]

    try:
        subprocess.run(cmd, check=True, cwd=project_root)
        print("\n✅ Build Successful!")
    except subprocess.CalledProcessError:
        print("\n❌ Build Failed during PyInstaller execution.")


if __name__ == "__main__":
    build()