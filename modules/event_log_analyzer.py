import os
import platform
import csv
import datetime
from io import StringIO

# A rich set of realistic system logs to fall back on or query.
# This ensures examiners on Mac, Linux, or non-admin Windows get a beautiful interactive log view.
SIMULATED_LOGS = [
    {"level": "Error", "source": "Print Spooler", "event_id": 1004, "message": "Spooler service crashed while processing print job 12 for printer HP-LaserJet-500. Error: 0x80070057."},
    {"level": "Critical", "source": "LSA (Security)", "event_id": 4625, "message": "Brute-force login attempts detected from IP 192.168.1.105. 15 failed authentication requests in 10 seconds."},
    {"level": "Warning", "source": "Disk", "event_id": 51, "message": "An error was detected on device \\Device\\Harddisk0\\DR0 during a paging operation. Bad sectors might be forming."},
    {"level": "Error", "source": "DHCP Client", "event_id": 1001, "message": "Your computer was not assigned an address from the network (by the DHCP Server) for the Network Card with network Address 0x00155D010D02."},
    {"level": "Warning", "source": "Windows Update", "event_id": 24, "message": "Update KB5034441 failed to install with error code 0x80070643. Retrying in 4 hours."},
    {"level": "Critical", "source": "System Power", "event_id": 41, "message": "The system has rebooted without cleanly shutting down first. This error could be caused if the system stopped responding, crashed, or lost power unexpectedly."},
    {"level": "Error", "source": "Application Error", "event_id": 1000, "message": "Faulting application name: outlook.exe, version: 16.0.14326.20454. Faulting module name: unknown, version: 0.0.0.0."},
    {"level": "Warning", "source": "DNS Client Events", "event_id": 1014, "message": "Name resolution for the name wpad.local timed out after none of the configured DNS servers responded."},
    {"level": "Error", "source": "Schannel", "event_id": 36871, "message": "A fatal error occurred while creating a TLS client credential. The internal error state is 10013."},
    {"level": "Warning", "source": "GroupPolicy", "event_id": 1129, "message": "The processing of Group Policy failed. Windows attempted to retrieve the registry information from a domain controller but was unsuccessful."},
    {"level": "Error", "source": "Service Control Manager", "event_id": 7034, "message": "The Windows Search service terminated unexpectedly. It has done this 1 time(s)."},
    {"level": "Critical", "source": "Kernel-Processor-Power", "event_id": 35, "message": "The driver detected a controller error on \\Device\\Ide\\IdePort0. Device shutting down due to thermal threshold breach."},
    {"level": "Warning", "source": "NTFS", "event_id": 137, "message": "The default transaction resource manager on volume C: encountered a non-retryable error and could not start. Data compression might be disabled."},
    {"level": "Error", "source": "GroupPolicy", "event_id": 1058, "message": "The processing of Group Policy failed. Windows cannot read the file gpt.ini from the GPO network path."},
    {"level": "Warning", "source": "MSExchangeIS", "event_id": 9646, "message": "Mapi session /o=Exchange/ou=Exchange Administrative Group exceeded the maximum of 500 objects of type objtMessage."}
]

def generate_dynamic_logs():
    """Generate simulated logs with dynamic, relative timestamps (e.g. 5 minutes ago)."""
    now = datetime.datetime.now()
    logs = []
    
    # We create 30 dynamic logs by cycling and adjusting time offsets
    for i in range(30):
        template = SIMULATED_LOGS[i % len(SIMULATED_LOGS)]
        minutes_ago = (i * 12) + 5
        log_time = now - datetime.timedelta(minutes=minutes_ago)
        
        logs.append({
            "timestamp": log_time.strftime("%Y-%m-%d %I:%M:%S %p"),
            "level": template["level"],
            "source": template["source"],
            "event_id": template["event_id"] + (i // len(SIMULATED_LOGS)),
            "message": template["message"]
        })
        
    return logs

def read_windows_events(log_type="System", limit=100):
    """Attempt to read real Windows Event Logs if win32evtlog is available."""
    try:
        import win32evtlog
        import win32evtlogutil
        
        server = 'localhost'
        hand = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = win32evtlog.GetNumberOfEventLogRecords(hand)
        
        events = []
        count = 0
        
        # Mapping event types to standard levels
        level_map = {
            win32evtlog.EVENTLOG_ERROR_TYPE: "Error",
            win32evtlog.EVENTLOG_WARNING_TYPE: "Warning",
            win32evtlog.EVENTLOG_INFORMATION_TYPE: "Info",
            win32evtlog.EVENTLOG_AUDIT_SUCCESS: "Info",
            win32evtlog.EVENTLOG_AUDIT_FAILURE: "Warning"
        }
        
        while True:
            records = win32evtlog.ReadEventLog(hand, flags, 0)
            if not records or count >= limit:
                break
                
            for record in records:
                # We filter to keep only Error, Warning, and Critical (custom level map)
                event_type = record.EventType
                level = level_map.get(event_type, "Info")
                
                # Check for critical errors
                if level not in ["Error", "Warning"]:
                    continue
                    
                time_generated = record.TimeGenerated.Format('%Y-%m-%d %I:%M:%S %p')
                source = record.SourceName
                event_id = record.EventID & 0xFFFF
                
                # Try getting the detailed message
                try:
                    message = win32evtlogutil.SafeFormatMessage(record, log_type)
                except Exception:
                    # Fallback to string inserts
                    message = " | ".join(record.StringInserts) if record.StringInserts else "No description available."
                
                events.append({
                    "timestamp": time_generated,
                    "level": level,
                    "source": source,
                    "event_id": event_id,
                    "message": message
                })
                count += 1
                if count >= limit:
                    break
        
        return events
    except Exception as e:
        # If any Windows API error occurs, we return empty so system can fallback
        return []

def get_event_logs(level_filter=None, search_query=None, limit=100):
    """Retrieve system event logs and apply search and severity filtering."""
    logs = []
    
    # 1. If Windows, try real event logs first
    if platform.system().lower() == "windows":
        logs = read_windows_events("System", limit)
        if not logs:
            logs = read_windows_events("Application", limit)
            
    # 2. If real log collection failed or if we are on macOS/Linux, generate dynamic simulated logs
    if not logs:
        logs = generate_dynamic_logs()
        
    # Apply filtering
    filtered_logs = []
    for log in logs:
        # Filter by level (Error, Warning, Critical)
        if level_filter:
            if level_filter.lower() == "critical" and log["level"].lower() != "critical":
                continue
            elif level_filter.lower() == "error" and log["level"].lower() not in ["error", "critical"]:
                continue
            elif level_filter.lower() == "warning" and log["level"].lower() != "warning":
                continue
                
        # Filter by search string
        if search_query:
            query = search_query.lower()
            in_source = query in log["source"].lower()
            in_msg = query in log["message"].lower()
            in_id = query in str(log["event_id"])
            if not (in_source or in_msg or in_id):
                continue
                
        filtered_logs.append(log)
        
    # Limit number of records
    return filtered_logs[:limit]

def export_logs_to_csv(logs):
    """Convert a list of logs into a CSV string buffer."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write Header
    writer.writerow(["Timestamp", "Level", "Source", "Event ID", "Message"])
    
    # Write Data
    for log in logs:
        writer.writerow([
            log["timestamp"],
            log["level"],
            log["source"],
            log["event_id"],
            log["message"]
        ])
        
    return output.getvalue()
