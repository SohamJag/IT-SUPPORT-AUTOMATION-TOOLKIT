import subprocess
import platform
import psutil

# Define services to check per OS
SERVICES_CONFIG = {
    "windows": [
        {"name": "Spooler", "display": "Print Spooler", "desc": "Handles print jobs in the queue."},
        {"name": "wuauserv", "display": "Windows Update", "desc": "Enables detection, download, and installation of updates."},
        {"name": "Dhcp", "display": "DHCP Client", "desc": "Registers and updates IP addresses and DNS records."},
        {"name": "Dnscache", "display": "DNS Client", "desc": "Caches DNS names and registers full computer name."}
    ],
    "darwin": [
        {"name": "org.cups.cupsd", "process_name": "cupsd", "display": "CUPS (Print Spooler)", "desc": "Enables printing services on macOS."},
        {"name": "com.openssh.sshd", "process_name": "sshd", "display": "SSH Daemon", "desc": "Allows secure remote login connections."},
        {"name": "org.apache.httpd", "process_name": "httpd", "display": "Apache Web Server", "desc": "Standard built-in web server daemon."},
        {"name": "com.apple.mDNSResponder", "process_name": "mDNSResponder", "display": "mDNSResponder (DNS Client)", "desc": "Handles DNS queries and discovery on macOS."}
    ],
    "linux": [
        {"name": "cups", "process_name": "cupsd", "display": "CUPS (Print Spooler)", "desc": "Handles printing services on Linux."},
        {"name": "ssh", "process_name": "sshd", "display": "SSH Server", "desc": "Enables secure shell connections."},
        {"name": "nginx", "process_name": "nginx", "display": "Nginx Web Server", "desc": "High performance HTTP web server."},
        {"name": "systemd-resolved", "process_name": "systemd-resolved", "display": "Systemd Resolved", "desc": "Network name resolution manager."}
    ]
}

def get_services():
    """Retrieve service statuses based on the host operating system."""
    current_os = platform.system().lower()
    
    # Map OS name to our config keys
    os_key = "linux"
    if "windows" in current_os:
        os_key = "windows"
    elif "darwin" in current_os:
        os_key = "darwin"
        
    services = SERVICES_CONFIG.get(os_key, SERVICES_CONFIG["linux"])
    results = []
    
    for s in services:
        status = "Stopped"
        
        # Check status based on platform
        if os_key == "windows":
            status = get_windows_service_status(s["name"])
        elif os_key == "darwin":
            status = get_macos_service_status(s["name"], s.get("process_name"))
        else: # linux
            status = get_linux_service_status(s["name"], s.get("process_name"))
            
        results.append({
            "name": s["name"],
            "display": s["display"],
            "desc": s["desc"],
            "status": status,
            "status_class": "bg-success" if status == "Running" else "bg-secondary"
        })
        
    return results

def get_windows_service_status(service_name):
    """Query service status on Windows."""
    try:
        output = subprocess.check_output(f"sc query {service_name}", shell=True).decode()
        if "RUNNING" in output:
            return "Running"
    except Exception:
        pass
    
    # Fallback to checking running processes
    return check_process_running_by_name(service_name)

def get_macos_service_status(label, process_name):
    """Query service status on macOS."""
    try:
        output = subprocess.check_output(f"launchctl list", shell=True).decode()
        for line in output.splitlines():
            if label in line:
                # launchctl list output format: PID Status Label
                parts = line.split()
                if len(parts) >= 3 and parts[0].isdigit() and int(parts[0]) > 0:
                    return "Running"
    except Exception:
        pass
        
    # Check if process is in system process list
    if process_name:
        return check_process_running_by_name(process_name)
    return "Stopped"

def get_linux_service_status(service_name, process_name):
    """Query service status on Linux."""
    try:
        output = subprocess.check_output(f"systemctl is-active {service_name}", shell=True).decode().strip()
        if output == "active":
            return "Running"
    except Exception:
        pass
        
    # Check process list fallback
    if process_name:
        return check_process_running_by_name(process_name)
    return "Stopped"

def check_process_running_by_name(process_name):
    """Fallback utility to check if a process is active using psutil."""
    try:
        for p in psutil.process_iter(['name']):
            if process_name.lower() in p.info['name'].lower():
                return "Running"
    except Exception:
        pass
    return "Stopped"

def toggle_service(service_name, action):
    """Attempt to toggle service state. Action can be 'start' or 'stop'."""
    current_os = platform.system().lower()
    
    if action not in ["start", "stop"]:
        return False, "Invalid action"
        
    try:
        if "windows" in current_os:
            # sc start/stop
            cmd = f"sc {action} {service_name}"
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        elif "darwin" in current_os:
            # launchctl start/stop
            cmd = f"launchctl {action} {service_name}"
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        else: # Linux
            # systemctl start/stop
            cmd = f"systemctl {action} {service_name}"
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            
        return True, f"Service successfully requested to {action}."
    except subprocess.CalledProcessError as e:
        output = e.output.decode() if e.output else ""
        if "access is denied" in output.lower() or "permission denied" in output.lower() or "not privileged" in output.lower():
            return False, "Access Denied: Administrative privileges (Run as Administrator / sudo) are required to control services."
        return False, f"Failed to {action} service. Error: {output.strip() or str(e)}"
    except Exception as e:
        return False, f"Failed to {action} service. Error: {str(e)}"
