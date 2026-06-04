import socket
import subprocess
import platform
import re
from ping3 import ping

def ping_host(host):
    """Ping a host using ping3, falling back to system subprocess ping if needed."""
    try:
        # Try ping3 (requires raw socket permissions, might fail on some user environments)
        latency = ping(host, timeout=1)
        if latency is not None:
            return round(latency * 1000, 2)
    except Exception:
        pass
    
    # Fallback to subprocess ping (works without raw socket permission)
    try:
        current_os = platform.system().lower()
        if "windows" in current_os:
            cmd = ["ping", "-n", "1", "-w", "1000", host]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", host]
            
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=1.5).decode()
        
        # Parse output for latency
        if "windows" in current_os:
            match = re.search(r"time[=<]([0-9]+)ms", output)
            if match:
                return float(match.group(1))
        else:
            # Unix-like output format: round-trip min/avg/max/stddev = 12.34/12.34/12.34/0.00 ms
            match = re.search(r"min/avg/max/(?:mdev|stddev) = \d+\.\d+/(\d+\.\d+)/", output)
            if match:
                return float(match.group(1))
            # Fallback regex for mac/linux
            match = re.search(r"time=(\d+(?:\.\d+)?)", output)
            if match:
                return float(match.group(1))
        return 1.0  # Return fallback latency if ping succeeded but wasn't parsed
    except Exception:
        return None

def get_default_gateway():
    """Retrieve the system's default gateway IP address."""
    current_os = platform.system().lower()
    
    # Method 1: OS-specific commands
    try:
        if "windows" in current_os:
            # Parse route print output
            output = subprocess.check_output("route print", shell=True).decode()
            for line in output.splitlines():
                if "0.0.0.0" in line and "Active Routes:" not in line:
                    parts = line.split()
                    # Route line: Network Destination | Netmask | Gateway | Interface | Metric
                    if len(parts) >= 4:
                        gateway = parts[2]
                        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", gateway) and gateway != "0.0.0.0":
                            return gateway
        elif "darwin" in current_os:
            # macOS: route -n get default
            output = subprocess.check_output("route -n get default", shell=True).decode()
            match = re.search(r"gateway:\s*(\S+)", output)
            if match:
                return match.group(1)
        else:
            # Linux: parse ip route show
            output = subprocess.check_output("ip route show", shell=True).decode()
            match = re.search(r"default via (\S+)", output)
            if match:
                return match.group(1)
    except Exception:
        pass

    # Method 2: Smart fallback using local IP
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Usually gateway is the .1 address on the subnet
        if local_ip and local_ip != "127.0.0.1":
            octets = local_ip.split('.')
            if len(octets) == 4:
                return f"{octets[0]}.{octets[1]}.{octets[2]}.1"
    except Exception:
        pass
        
    return "192.168.1.1"

def run_network_diagnostic():
    """Execute all network diagnostic steps and compile the results."""
    # 1. Internet connection check (HTTP port 80 check is highly reliable)
    internet_connected = False
    try:
        # Quick socket connection attempt
        socket.setdefaulttimeout(1.5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53)) # Google DNS
        s.close()
        internet_connected = True
    except Exception:
        pass
        
    # 2. DNS Resolution
    dns_resolved = False
    dns_ips = []
    try:
        ips = socket.gethostbyname_ex("google.com")[2]
        if ips:
            dns_resolved = True
            dns_ips = ips
    except Exception:
        pass

    # 3. Ping Test to google.com
    ping_latency = ping_host("google.com")

    # 4. Gateway reachability
    gateway_ip = get_default_gateway()
    gateway_ping = ping_host(gateway_ip)
    
    # Calculate overall statuses
    results = {
        "internet": {
            "status": "Connected" if internet_connected else "Not Connected",
            "success": internet_connected
        },
        "dns": {
            "status": f"Success (IPs: {', '.join(dns_ips[:2])})" if dns_resolved else "Failed",
            "success": dns_resolved
        },
        "ping": {
            "status": f"Success ({ping_latency} ms)" if ping_latency is not None else "Failed",
            "latency": ping_latency,
            "success": ping_latency is not None
        },
        "gateway": {
            "ip": gateway_ip,
            "status": f"Reachable ({gateway_ping} ms)" if gateway_ping is not None else "Unreachable",
            "success": gateway_ping is not None
        }
    }
    
    return results
