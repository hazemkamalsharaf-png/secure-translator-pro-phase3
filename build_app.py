import os
import shutil
import subprocess

def build():
    project_root = os.path.abspath(os.getcwd())
    dist_dir = os.path.join(project_root, "dist")
    build_dir = os.path.join(project_root, "build")
    spec_file = os.path.join(project_root, "SecureTranslatorPro.spec")
    app_name = "SecureTranslatorPro"

    # مسح الفولدرات القديمة وملف الـ spec اللي مسبب المشكلة
    for item in [dist_dir, build_dir, spec_file]:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)

    print(f"🚀 Starting build for {app_name}...")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",            
        "--windowed",          
        f"--name={app_name}",
        "--paths", project_root,             # الإضافة السحرية لتعريف مسار المشروع
        "--collect-submodules", "ui",        # إجبار الأداة على سحب فولدر الواجهة
        "--collect-submodules", "core",      # إجبار الأداة على سحب فولدر المحرك
        "--add-data", f"{os.path.join(project_root, 'data')};data", 
        "--collect-all", "customtkinter",    
        f"main.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Build Successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed during PyInstaller execution.")

if __name__ == "__main__":
    build()