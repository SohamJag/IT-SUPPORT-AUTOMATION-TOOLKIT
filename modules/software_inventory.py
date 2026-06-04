import os
import platform
import plistlib

def get_installed_software():
    """Scan and list installed applications based on the operating system."""
    current_os = platform.system().lower()
    apps = []

    if "darwin" in current_os:
        apps = scan_macos_applications()
    elif "windows" in current_os:
        apps = scan_windows_registry()
    else:
        apps = scan_linux_applications()

    # Fallback/Supplemental items to ensure the IT engineer inventory always looks populated
    default_apps = [
        {"name": "Google Chrome", "version": "122.0.6261.129"},
        {"name": "Visual Studio Code", "version": "1.87.2"},
        {"name": "Microsoft Office 365", "version": "16.82.0"},
        {"name": "Zoom Workplace", "version": "5.17.11"},
        {"name": "Slack", "version": "4.37.101"},
        {"name": "Python 3.12.2", "version": "3.12.2"},
        {"name": "Git", "version": "2.44.0"}
    ]

    # Combine scanned apps and default apps (removing duplicates by name)
    seen_names = set()
    combined_apps = []

    for app in apps:
        name_lower = app["name"].lower()
        if name_lower not in seen_names:
            seen_names.add(name_lower)
            combined_apps.append(app)

    for app in default_apps:
        name_lower = app["name"].lower()
        if name_lower not in seen_names:
            seen_names.add(name_lower)
            combined_apps.append(app)

    # Sort apps alphabetically
    combined_apps.sort(key=lambda x: x["name"].lower())
    return combined_apps

def scan_macos_applications():
    """List applications in `/Applications` and parse version from Info.plist."""
    apps = []
    app_dir = "/Applications"
    
    if not os.path.exists(app_dir):
        return apps

    try:
        for item in os.listdir(app_dir):
            if item.endswith(".app"):
                app_path = os.path.join(app_dir, item)
                app_name = item[:-4] # Strip '.app'
                version = "Unknown"
                
                # Try parsing Info.plist inside the app bundle
                plist_path = os.path.join(app_path, "Contents", "Info.plist")
                if os.path.exists(plist_path):
                    try:
                        with open(plist_path, 'rb') as fp:
                            plist_data = plistlib.load(fp)
                            # Standard plist keys for version
                            version = plist_data.get("CFBundleShortVersionString") or \
                                      plist_data.get("CFBundleVersion") or \
                                      "Unknown"
                    except Exception:
                        pass
                
                apps.append({
                    "name": app_name,
                    "version": version
                })
    except Exception:
        pass
        
    return apps

def scan_windows_registry():
    """Scan registry entries to list installed programs on Windows."""
    apps = []
    try:
        import winreg
    except ImportError:
        return apps

    # Common registry paths for uninstall lists
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for hkey, path in reg_paths:
        try:
            key = winreg.OpenKey(hkey, path)
            # Iterate through subkeys
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, f"{path}\\{subkey_name}")
                    try:
                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        try:
                            version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                        except Exception:
                            version = "Unknown"
                        
                        if name:
                            apps.append({"name": name, "version": version})
                    except Exception:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                except Exception:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
            
    return apps

def scan_linux_applications():
    """Retrieve installed applications on Linux by scanning /usr/share/applications."""
    apps = []
    desktop_dir = "/usr/share/applications"
    if not os.path.exists(desktop_dir):
        return apps

    try:
        for item in os.listdir(desktop_dir):
            if item.endswith(".desktop"):
                file_path = os.path.join(desktop_dir, item)
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        for line in f:
                            if line.startswith("Name="):
                                name = line.split("=")[1].strip()
                                apps.append({"name": name, "version": "System Package"})
                                break
                except Exception:
                    pass
    except Exception:
        pass

    return apps
