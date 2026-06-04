import os
import platform
import socket
import psutil
import uuid
import requests

def get_mac_address():
    """Retrieve the primary MAC address of the system."""
    try:
        # Find MAC address from psutil net interfaces (more reliable than uuid for actual active adapters)
        for interface, addrs in psutil.net_if_addrs().items():
            # Skip loopback
            if 'loop' in interface.lower() or 'lo' == interface.lower():
                continue
            for addr in addrs:
                if addr.family == psutil.AF_LINK or (hasattr(socket, 'AF_LINK') and addr.family == socket.AF_LINK):
                    return addr.address
                # On some platforms, MAC address is returned as family 17 or AF_LINK is not defined
                elif addr.family == 17:
                    return addr.address
    except Exception:
        pass
    
    # Fallback to uuid method
    try:
        mac_num = uuid.getnode()
        mac_str = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
        return mac_str
    except Exception:
        return "Unknown"

def get_local_ip():
    """Retrieve the local IP address of the primary active interface."""
    try:
        # Establish a dummy socket connection to Google DNS to determine routing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback to standard hostname resolution
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_public_ip():
    """Fetch public IP address via external HTTP API with fallback."""
    try:
        # Quick request to ipify
        response = requests.get("https://api.ipify.org?format=json", timeout=2.0)
        if response.status_code == 200:
            return response.json().get("ip", "Offline")
    except Exception:
        pass
    return "Offline"

def get_cpu_info():
    """Gather descriptive CPU info."""
    cpu_info = {
        "model": platform.processor() or "Unknown CPU",
        "cores_physical": psutil.cpu_count(logical=False) or 0,
        "cores_logical": psutil.cpu_count(logical=True) or 0,
        "current_usage": psutil.cpu_percent(interval=0.1)
    }
    
    # On macOS, platform.processor() might return 'i386' or empty, let's refine
    if platform.system() == "Darwin":
        try:
            import subprocess
            brand = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
            cpu_info["model"] = brand
        except Exception:
            pass
            
    return cpu_info

def get_system_info():
    """Consolidate hostname, username, OS, CPU, RAM, Disk, and Network Info."""
    # Username fallback checks
    username = os.environ.get("USER") or os.environ.get("USERNAME")
    if not username:
        try:
            import getpass
            username = getpass.getuser()
        except Exception:
            username = "System Engineer"

    # Virtual Memory
    vm = psutil.virtual_memory()
    ram_info = {
        "total": round(vm.total / (1024**3), 2),
        "used": round(vm.used / (1024**3), 2),
        "free": round(vm.free / (1024**3), 2),
        "percent": vm.percent
    }

    # Main disk usage
    try:
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": round(disk.total / (1024**3), 2),
            "used": round(disk.used / (1024**3), 2),
            "free": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        }
    except Exception:
        disk_info = {"total": 0, "used": 0, "free": 0, "percent": 0}

    # Formatted OS name
    os_name = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    
    if os_name == "Darwin":
        os_display = f"macOS {os_release}"
    elif os_name == "Windows":
        os_display = f"Windows {os_release}"
    elif os_name == "Linux":
        os_display = f"Linux {os_release}"
    else:
        os_display = f"{os_name} {os_release}"

    info = {
        "hostname": socket.gethostname(),
        "username": username,
        "os": os_display,
        "os_details": f"{os_name} {os_release} ({os_version})",
        "cpu": get_cpu_info(),
        "ram": ram_info,
        "disk": disk_info,
        "local_ip": get_local_ip(),
        "public_ip": get_public_ip(),
        "mac_address": get_mac_address()
    }
    
    return info
