import psutil

def get_running_processes():
    """Retrieve all active processes with resource utilization, sorted by CPU and Memory."""
    processes = []
    
    # Iterate through all running processes
    for p in psutil.process_iter(attrs=['pid', 'name', 'username', 'status', 'memory_percent']):
        try:
            # CPU usage calculation - interval=None returns usage since last call,
            # which is fast and does not block the request loop.
            cpu_percent = p.cpu_percent(interval=None)
            
            # Fetch attributes safely
            p_info = p.info
            pid = p_info['pid']
            name = p_info['name'] or "Unknown"
            username = p_info['username'] or "System"
            status = p_info['status'] or "unknown"
            
            # Memory percent
            mem_percent = p_info['memory_percent'] or 0.0
            # Calculate actual RAM usage (Resident Set Size)
            try:
                mem_bytes = p.memory_info().rss
                mem_mb = round(mem_bytes / (1024 * 1024), 1)
            except Exception:
                mem_mb = round((mem_percent / 100.0) * (psutil.virtual_memory().total) / (1024 * 1024), 1)

            processes.append({
                "pid": pid,
                "name": name,
                "username": username,
                "status": status.capitalize(),
                "cpu": cpu_percent,
                "memory_pct": round(mem_percent, 1),
                "memory_mb": mem_mb
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue
            
    # Sort processes: primary by CPU usage %, secondary by Memory MB usage
    processes.sort(key=lambda x: (x["cpu"], x["memory_mb"]), reverse=True)
    return processes

def kill_process(pid):
    """Terminate a process by its process ID (PID)."""
    try:
        process = psutil.Process(pid)
        process.terminate()  # Graceful kill
        return True, f"Process {pid} ({process.name()}) terminated successfully."
    except psutil.AccessDenied:
        # Try force kill if permissions allow
        try:
            process = psutil.Process(pid)
            process.kill() # Force kill
            return True, f"Process {pid} forced to terminate."
        except psutil.AccessDenied:
            return False, f"Permission Denied: Insufficient rights to terminate process {pid}."
    except psutil.NoSuchProcess:
        return False, f"Process {pid} does not exist or has already terminated."
    except Exception as e:
        return False, f"Failed to terminate process {pid}. Error: {str(e)}"
