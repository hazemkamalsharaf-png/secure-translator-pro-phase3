# =============================================================================
# Secure Translator Pro - Build & Release Script
# =============================================================================
# This script automates the full build pipeline:
# 1. PyInstaller build
# 2. Inno Setup installer creation
# 3. GitHub Release upload (optional)
# =============================================================================

import os
import subprocess
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
APP_NAME = "SecureTranslatorPro"


def run_command(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return result


def build_pyinstaller():
    """Step 1: Build executable with PyInstaller."""
    print("=" * 60)
    print("Step 1/3: Building with PyInstaller...")
    print("=" * 60)

    run_command(["python", "build_app.py"])

    # Verify build output
    exe_path = os.path.join(DIST_DIR, APP_NAME, f"{APP_NAME}.exe")
    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"Build failed: {exe_path} not found")

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"\n✅ PyInstaller build complete!")
    print(f"   Executable: {exe_path}")
    print(f"   Size: {size_mb:.2f} MB")


def create_installer():
    """Step 2: Create installer with Inno Setup."""
    print("\n" + "=" * 60)
    print("Step 2/3: Creating installer with Inno Setup...")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Run Inno Setup Compiler (iscc.exe)
    iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

    if not os.path.exists(iscc_path):
        print(f"\n⚠️  Inno Setup not found at: {iscc_path}")
        print("   Please install Inno Setup from: https://jrsoftware.org/isdl.php")
        print("   Or manually run: iscc installer.iss")
        return

    run_command([iscc_path, "installer.iss"])

    # Find the setup executable
    setup_exe = os.path.join(OUTPUT_DIR, f"{APP_NAME}_Setup.exe")
    if os.path.exists(setup_exe):
        size_mb = os.path.getsize(setup_exe) / (1024 * 1024)
        print(f"\n✅ Installer created successfully!")
        print(f"   Setup: {setup_exe}")
        print(f"   Size: {size_mb:.2f} MB")
    else:
        # List what's in output dir
        files = os.listdir(OUTPUT_DIR)
        print(f"\n⚠️  Installer build may have failed.")
        print(f"   Output directory contents: {files}")


def create_github_release():
    """Step 3 (Optional): Create GitHub Release."""
    print("\n" + "=" * 60)
    print("Step 3/3: Creating GitHub Release...")
    print("=" * 60)

    # Check for gh CLI
    try:
        run_command(["gh", "--version"])
    except RuntimeError:
        print("\n⚠️  GitHub CLI (gh) not found.")
        print("   Install from: https://cli.github.com/")
        print("   Or manually create release at:")
        print("   https://github.com/hazemkamalsharaf-png/secure-translator-pro-phase3/releases/new")
        return

    # Login check
    try:
        run_command(["gh", "auth", "status"])
    except RuntimeError:
        print("\n⚠️  Not logged into GitHub CLI.")
        print("   Run: gh auth login")
        return

    version = "v1.0.0"
    tag_name = version
    release_name = f"Secure Translator Pro {version}"
    description = f"""First stable release of Secure Translator Pro.

**Features:**
- 4-agent translation architecture (Style Profiler, Drafting, Critic, Cultural)
- Smart glossary filtering with context awareness
- RTL language support
- Cloud model selector
- Automatic recovery system
- Dark/Light theme support
- Professional UI with CustomTkinter

**Installation:**
Run `SecureTranslatorPro_Setup.exe` for automatic installation.

**Requirements:**
- Windows 10/11 (64-bit)
- Python 3.11+ (for source development)
"""

    # Create release
    run_command([
        "gh", "release", "create",
        tag_name,
        "--title", release_name,
        "--notes", description,
        "--prerelease"  # Mark as prerelease since it's v1.0.0
    ])

    # Upload installer
    setup_exe = os.path.join(OUTPUT_DIR, f"{APP_NAME}_Setup.exe")
    if os.path.exists(setup_exe):
        run_command([
            "gh", "release", "upload",
            tag_name,
            setup_exe
        ])
        print(f"\n✅ Uploaded: {setup_exe}")

    # Upload source distribution (optional)
    dist_folder = os.path.join(DIST_DIR, APP_NAME)
    if os.path.isdir(dist_folder):
        zip_name = f"{APP_NAME}_{version}_portable.zip"
        zip_path = os.path.join(OUTPUT_DIR, zip_name)

        print(f"\n📦 Creating portable ZIP: {zip_name}")
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", dist_folder)
        run_command([
            "gh", "release", "upload",
            tag_name,
            zip_path
        ])
        print(f"✅ Uploaded: {zip_path}")

    print(f"\n🎉 Release created: https://github.com/hazemkamalsharaf-png/secure-translator-pro-phase3/releases/tag/{tag_name}")


def main():
    """Run the full build pipeline."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🚀 Build started at {timestamp}")
    print(f"   Project: {PROJECT_ROOT}\n")

    try:
        # Step 1: PyInstaller
        build_pyinstaller()

        # Step 2: Inno Setup Installer
        create_installer()

        # Step 3: GitHub Release (uncomment if ready)
        # create_github_release()

        print("\n" + "=" * 60)
        print("✅ Build pipeline complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        raise


if __name__ == "__main__":
    main()
