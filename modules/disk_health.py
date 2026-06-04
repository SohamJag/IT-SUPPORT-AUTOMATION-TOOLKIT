import os
import psutil
import matplotlib
# Use Agg backend for matplotlib to generate files without window environment (essential for web servers)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def get_disk_health():
    """Scan disk partitions and retrieve health/usage parameters."""
    drives = []
    
    # Scan all partitions
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        # Fallback if partition scan fails
        partitions = []

    # If no partitions are returned (sometimes on virtual containers), use '/' root directory
    if not partitions:
        try:
            drives.append(get_partition_details("/", "/"))
        except Exception:
            pass
    else:
        for p in partitions:
            # Skip loop devices, cdroms, or empty mountpoints
            if 'cdrom' in p.opts or p.fstype == '' or 'loop' in p.device:
                continue
            
            # Avoid docker/snap mounts on Linux
            if p.mountpoint.startswith('/var/lib/docker') or p.mountpoint.startswith('/snap'):
                continue
                
            try:
                drive_details = get_partition_details(p.device, p.mountpoint)
                drives.append(drive_details)
            except Exception:
                # Permission errors on specific partitions
                continue
                
    return drives

def get_partition_details(device, mountpoint):
    """Retrieve details for a single partition."""
    usage = psutil.disk_usage(mountpoint)
    
    total_gb = round(usage.total / (1024**3), 2)
    used_gb = round(usage.used / (1024**3), 2)
    free_gb = round(usage.free / (1024**3), 2)
    percent = usage.percent
    
    # Alert Logic: if usage > 90, Critical, else if usage > 75 Warning, else Healthy
    status = "Healthy"
    status_class = "text-success border-success"
    if percent > 90:
        status = "Critical"
        status_class = "text-danger border-danger"
    elif percent > 75:
        status = "Warning"
        status_class = "text-warning border-warning"
        
    return {
        "device": device,
        "mountpoint": mountpoint,
        "total": total_gb,
        "used": used_gb,
        "free": free_gb,
        "percent": percent,
        "status": status,
        "status_class": status_class
    }

def generate_disk_chart(drives, output_dir):
    """Generate a disk usage pie chart using matplotlib and save it to output_dir."""
    if not drives:
        return None
        
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        chart_path = os.path.join(output_dir, "disk_usage.png")
        
        # We'll display details for the main system partition
        main_drive = drives[0]
        # Find mountpoint '/' or 'C:\' if available, otherwise just use the first one
        for d in drives:
            if d['mountpoint'] == '/' or 'C:' in d['device'].upper():
                main_drive = d
                break
                
        labels = ['Used Space', 'Free Space']
        sizes = [main_drive['used'], main_drive['free']]
        
        # Sleek dark-mode matching colors: Neon Green and Dark Grey
        colors = ['#10b981', '#2d3748']
        text_color = '#ffffff'
        
        fig, ax = plt.subplots(figsize=(6, 4.5), facecolor='#1f1f23')
        ax.set_facecolor('#1f1f23')
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=140, 
            colors=colors,
            textprops=dict(color=text_color),
            wedgeprops=dict(width=0.4, edgecolor='#1f1f23', linewidth=3) # Donut chart
        )
        
        # Style labels and autopct texts
        for text in texts:
            text.set_color(text_color)
            text.set_fontsize(11)
        for autotext in autotexts:
            autotext.set_color(text_color)
            autotext.set_fontsize(11)
            autotext.set_weight('bold')
            
        ax.set_title(f"Storage Breakdown: {main_drive['device']} ({main_drive['mountpoint']})", color='#10b981', fontsize=12, fontweight='bold', pad=15)
        plt.tight_layout()
        
        # Save file
        plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='#1f1f23')
        plt.close()
        return "disk_usage.png"
    except Exception as e:
        print(f"Error generating disk chart: {e}")
        return None
