#!/usr/bin/env python3
"""
Validate requirements.txt for cross-platform compatibility.
Checks Windows, macOS, and Linux compatibility.
"""

import requests
import json
import re
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet

# Packages to validate from requirements.txt
PACKAGES = {
    "fastapi": ">=0.109.0",
    "uvicorn": ">=0.27.0",
    "python-multipart": ">=0.0.6",
    "python-docx": ">=0.8.11",
    "openpyxl": ">=3.0.0",
    "pydantic": ">=2.6.0",
    "streamlit": ">=1.28.0",
    "requests": ">=2.31.0",
    "pandas": ">=2.0.0",
    "anthropic": ">=0.7.0",
}

PYPI_API = "https://pypi.org/pypi/{}/json"

def get_package_info(package_name):
    """Fetch package info from PyPI."""
    try:
        response = requests.get(PYPI_API.format(package_name), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"⚠️  Could not fetch {package_name}: {e}")
        return None

def check_wheel_support(releases):
    """Check if package has wheels for Windows, macOS, and Linux."""
    platforms = {
        "windows": False,
        "macos": False,
        "linux": False,
        "universal": False,
    }

    for release in releases:
        filename = release.get("filename", "").lower()

        # Check for universal wheels
        if "py3-none-any" in filename or "py2.py3-none-any" in filename:
            platforms["universal"] = True

        # Check for wheels (not just source distributions)
        if ".whl" in filename:
            if "win_amd64" in filename or "win32" in filename:
                platforms["windows"] = True
            if "macosx" in filename or "macos" in filename:
                platforms["macos"] = True
            if "manylinux" in filename or "linux" in filename:
                platforms["linux"] = True

    return platforms

def is_pure_python(package_data):
    """Check if package is pure Python (no C extensions)."""
    info = package_data.get("info", {})
    requires_dist = info.get("requires_dist", [])

    # Pure Python packages typically don't have platform-specific extensions
    classifiers = info.get("classifiers", [])
    for classifier in classifiers:
        if "Pure Python" in classifier or "pure python" in classifier.lower():
            return True

    return False

def validate_requirements():
    """Validate all packages."""
    print("=" * 80)
    print("VALIDATING REQUIREMENTS.TXT FOR CROSS-PLATFORM COMPATIBILITY")
    print("=" * 80)
    print()

    results = {
        "compatible": [],
        "partial": [],
        "warning": [],
        "error": [],
    }

    for package, spec in PACKAGES.items():
        print(f"Checking: {package} {spec}")

        data = get_package_info(package)
        if not data:
            results["error"].append(f"{package}: Could not fetch PyPI data")
            print(f"  ❌ ERROR: Could not fetch PyPI data\n")
            continue

        info = data.get("info", {})
        releases = data.get("releases", {})

        # Get latest version matching spec
        spec_set = SpecifierSet(spec)
        available_versions = [v for v in releases.keys() if v in spec_set]
        available_versions.sort(key=pkg_version.parse, reverse=True)

        if not available_versions:
            results["error"].append(f"{package}: No versions match {spec}")
            print(f"  ❌ ERROR: No versions match {spec}\n")
            continue

        latest = available_versions[0]
        latest_releases = releases.get(latest, [])

        # Check platforms
        platforms = check_wheel_support(latest_releases)
        is_pure = is_pure_python(data)

        # Determine status
        has_all = platforms["universal"] or (
            platforms["windows"] and platforms["macos"] and platforms["linux"]
        )

        print(f"  Version: {latest}")
        print(f"  Pure Python: {'✅ Yes' if is_pure else '❌ No (native extensions)'}")
        print(f"  Wheels:")
        print(f"    Windows: {'✅' if platforms['windows'] or platforms['universal'] else '❌'}")
        print(f"    macOS:   {'✅' if platforms['macos'] or platforms['universal'] else '❌'}")
        print(f"    Linux:   {'✅' if platforms['linux'] or platforms['universal'] else '❌'}")

        if has_all or platforms["universal"] or is_pure:
            print(f"  Status: ✅ COMPATIBLE")
            results["compatible"].append(f"{package}=={latest}")
        elif platforms["windows"] and (platforms["macos"] or platforms["linux"]):
            print(f"  Status: ⚠️  PARTIAL (missing one platform)")
            results["partial"].append(f"{package}=={latest}")
        else:
            print(f"  Status: ❌ WARNING (incomplete platform support)")
            results["warning"].append(f"{package}=={latest}")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Compatible:     {len(results['compatible'])} packages")
    print(f"⚠️  Partial:        {len(results['partial'])} packages")
    print(f"⚠️  Warnings:       {len(results['warning'])} packages")
    print(f"❌ Errors:         {len(results['error'])} packages")
    print()

    if results["compatible"]:
        print("✅ FULLY COMPATIBLE PACKAGES:")
        for pkg in results["compatible"]:
            print(f"   {pkg}")
        print()

    if results["partial"]:
        print("⚠️  PARTIAL COMPATIBILITY:")
        for pkg in results["partial"]:
            print(f"   {pkg}")
        print()

    if results["warning"]:
        print("⚠️  WARNINGS:")
        for pkg in results["warning"]:
            print(f"   {pkg}")
        print()

    if results["error"]:
        print("❌ ERRORS:")
        for err in results["error"]:
            print(f"   {err}")
        print()

    # Overall recommendation
    print("=" * 80)
    if len(results["error"]) > 0:
        print("❌ RECOMMENDATION: Fix errors before using")
    elif len(results["warning"]) > 0:
        print("⚠️  RECOMMENDATION: Review warnings, may need OS-specific alternatives")
    elif len(results["partial"]) > 0:
        print("⚠️  RECOMMENDATION: Should work but verify on all platforms")
    else:
        print("✅ RECOMMENDATION: Requirements.txt is cross-platform compatible!")
    print("=" * 80)

if __name__ == "__main__":
    validate_requirements()
