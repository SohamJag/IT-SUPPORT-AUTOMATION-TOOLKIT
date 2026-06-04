document.addEventListener('DOMContentLoaded', () => {
    console.log("IT Support Automation Toolkit Initialized.");
    
    // Auto-initialize bootstrap tooltips or popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ----------------------------------------------------
    // Module 3: Network Diagnostics Asynchronous Handler
    // ----------------------------------------------------
    const runNetTestBtn = document.getElementById('run-net-test-btn');
    if (runNetTestBtn) {
        runNetTestBtn.addEventListener('click', runNetworkDiagnostics);
    }

    // ----------------------------------------------------
    // Module 4: Service Controls Handler
    // ----------------------------------------------------
    setupServiceToggles();

    // ----------------------------------------------------
    // Module 5: Password Generator Handler
    // ----------------------------------------------------
    setupPasswordGenerator();

    // ----------------------------------------------------
    // Module 6: Event Log Filter & Search
    // ----------------------------------------------------
    setupEventLogFilters();

    // ----------------------------------------------------
    // Module 7: Process Monitor Search & Kill
    // ----------------------------------------------------
    setupProcessMonitor();

    // ----------------------------------------------------
    // Module 8: Software Inventory Filter
    // ----------------------------------------------------
    setupSoftwareFilters();

    // ----------------------------------------------------
    // Module 9: Report Generation Handler
    // ----------------------------------------------------
    setupReportGenerator();
});

/**
 * Run Network Connectivity tests via AJAX and update dashboard UI
 */
async function runNetworkDiagnostics() {
    const runBtn = document.getElementById('run-net-test-btn');
    const terminal = document.getElementById('net-terminal-output');
    
    if (!terminal) return;
    
    // Disable button and clear console
    runBtn.disabled = true;
    runBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running Diagnostics...';
    
    terminal.innerHTML = '<span class="text-muted">[INIT]</span> Initializing Network Socket Handlers...\n';
    
    // Step-by-step console emulation
    const logToTerminal = (text, delay) => {
        return new Promise(resolve => setTimeout(() => {
            terminal.innerHTML += text + '\n';
            terminal.scrollTop = terminal.scrollHeight;
            resolve();
        }, delay));
    };

    await logToTerminal('<span class="text-muted">[INFO]</span> Checking DNS Resolver tables for host: google.com...', 400);
    await logToTerminal('<span class="text-muted">[INFO]</span> Dispatching ICMP echo packets to core gateway...', 400);
    await logToTerminal('<span class="text-muted">[INFO]</span> Requesting handshake on HTTP port 80...', 300);
    
    try {
        const response = await fetch('/api/network_check');
        const data = await response.json();
        
        await logToTerminal('\n================ DIAGNOSTIC SUMMARY ================', 200);
        
        // 1. Internet connection
        if (data.internet.success) {
            await logToTerminal(`Internet Connectivity : <span class="text-success">[CONNECTED]</span>`, 150);
        } else {
            await logToTerminal(`Internet Connectivity : <span class="text-danger">[DISCONNECTED]</span>`, 150);
        }
        
        // 2. DNS
        if (data.dns.success) {
            await logToTerminal(`DNS Name Resolution   : <span class="text-success">[OK]</span> -> Resolved to Google IP`, 150);
        } else {
            await logToTerminal(`DNS Name Resolution   : <span class="text-danger">[FAILED]</span> -> Check dns client cache`, 150);
        }
        
        // 3. Ping
        if (data.ping.success) {
            await logToTerminal(`Ping Latency (Google) : <span class="text-success">[SUCCESS]</span> -> Average ${data.ping.latency} ms`, 150);
        } else {
            await logToTerminal(`Ping Latency (Google) : <span class="text-danger">[FAILED]</span> -> ICMP packets dropped or blocked`, 150);
        }
        
        // 4. Gateway
        if (data.gateway.success) {
            await logToTerminal(`Gateway Reachability  : <span class="text-success">[REACHABLE]</span> -> IP: ${data.gateway.ip} (Ping OK)`, 150);
        } else {
            await logToTerminal(`Gateway Reachability  : <span class="text-danger">[UNREACHABLE]</span> -> IP: ${data.gateway.ip} (Check local router)`, 150);
        }
        
        await logToTerminal('\n<span class="text-success">[DONE]</span> Diagnostics complete. All sockets closed.', 200);
        
        // Update the actual tables on the page if present
        updateNetworkUIElements(data);
        
    } catch (error) {
        await logToTerminal(`\n<span class="text-danger">[FATAL]</span> Socket diagnostic crash. Error: ${error.message}`, 100);
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="fas fa-play me-2"></i>Run Connectivity Diagnostics';
    }
}

function updateNetworkUIElements(data) {
    const setStatus = (idPrefix, success, text) => {
        const badge = document.getElementById(`${idPrefix}-badge`);
        const row = document.getElementById(`${idPrefix}-row`);
        
        if (badge) {
            badge.className = success ? 'status-pill status-active' : 'status-pill status-critical';
            badge.innerHTML = success ? '<span class="pulse-indicator"></span>' + text : '<span class="pulse-indicator red"></span>' + text;
        }
    };
    
    setStatus('net-internet', data.internet.success, data.internet.status);
    setStatus('net-dns', data.dns.success, data.dns.status);
    setStatus('net-ping', data.ping.success, data.ping.status);
    setStatus('net-gateway', data.gateway.success, data.gateway.status);
}

/**
 * Configure service start/stop actions
 */
function setupServiceToggles() {
    const serviceContainer = document.getElementById('services-list-container');
    if (!serviceContainer) return;
    
    serviceContainer.addEventListener('click', async (e) => {
        const toggleBtn = e.target.closest('.service-toggle-btn');
        if (!toggleBtn) return;
        
        const serviceName = toggleBtn.getAttribute('data-service');
        const currentStatus = toggleBtn.getAttribute('data-status');
        const action = currentStatus === 'Running' ? 'stop' : 'start';
        
        // Confirm stop action for critical services
        if (action === 'stop' && !confirm(`Are you sure you want to stop service '${serviceName}'? It may affect local system services.`)) {
            return;
        }
        
        // Show loading state
        toggleBtn.disabled = true;
        const originalText = toggleBtn.innerHTML;
        toggleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        try {
            const response = await fetch('/api/service/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service_name: serviceName, action: action })
            });
            const data = await response.json();
            
            if (data.success) {
                // Show notification and refresh the window
                alert(data.message);
                window.location.reload();
            } else {
                alert(data.message);
            }
        } catch (error) {
            alert(`Error communicating with backend: ${error.message}`);
        } finally {
            toggleBtn.disabled = false;
            toggleBtn.innerHTML = originalText;
        }
    });
}

/**
 * Configure password generator controls
 */
function setupPasswordGenerator() {
    const genBtn = document.getElementById('generate-pw-btn');
    if (!genBtn) return;
    
    const lengthInput = document.getElementById('pw-length');
    const lengthVal = document.getElementById('pw-length-val');
    const includeSymbols = document.getElementById('pw-symbols');
    const includeNumbers = document.getElementById('pw-numbers');
    const includeUpper = document.getElementById('pw-upper');
    const includeLower = document.getElementById('pw-lower');
    const outputField = document.getElementById('pw-output');
    
    const strengthText = document.getElementById('pw-strength-text');
    const strengthBar = document.getElementById('pw-strength-bar');
    const copyBtn = document.getElementById('copy-pw-btn');
    
    // Sync slider value text
    if (lengthInput && lengthVal) {
        lengthInput.addEventListener('input', () => {
            lengthVal.textContent = lengthInput.value;
        });
    }
    
    const fetchNewPassword = async () => {
        const length = parseInt(lengthInput.value);
        const sym = includeSymbols.checked;
        const num = includeNumbers.checked;
        const upper = includeUpper.checked;
        const lower = includeLower.checked;
        
        try {
            const response = await fetch('/api/generate_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ length, symbols: sym, numbers: num, uppercase: upper, lowercase: lower })
            });
            const data = await response.json();
            
            outputField.value = data.password;
            
            // Update Strength indicator
            strengthText.textContent = `Strength: ${data.strength}`;
            strengthBar.className = `progress-bar strength-bar ${data.strength_class}`;
            strengthBar.style.width = `${data.strength_pct}%`;
        } catch (error) {
            console.error("Failed to generate password:", error);
        }
    };
    
    genBtn.addEventListener('click', fetchNewPassword);
    
    if (copyBtn && outputField) {
        copyBtn.addEventListener('click', () => {
            if (!outputField.value) return;
            navigator.clipboard.writeText(outputField.value)
                .then(() => {
                    const originalText = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="fas fa-check me-1"></i>Copied';
                    setTimeout(() => {
                        copyBtn.innerHTML = originalText;
                    }, 1500);
                })
                .catch(err => {
                    alert("Failed to copy text: " + err);
                });
        });
    }
}

/**
 * Configure local and remote event log operations
 */
function setupEventLogFilters() {
    const searchForm = document.getElementById('event-log-form');
    if (!searchForm) return;
    
    const levelFilter = document.getElementById('log-level');
    const searchQuery = document.getElementById('log-search');
    const logsTableBody = document.getElementById('logs-table-body');
    const exportBtn = document.getElementById('export-logs-csv');
    
    const queryLogs = async (e) => {
        if (e) e.preventDefault();
        
        const lvl = levelFilter.value;
        const query = searchQuery.value;
        
        logsTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><i class="fas fa-spinner fa-spin me-2"></i>Querying system log tables...</td></tr>';
        
        try {
            const params = new URLSearchParams({ level: lvl, search: query });
            const response = await fetch(`/api/event_logs/query?${params.toString()}`);
            const logs = await response.json();
            
            if (logs.length === 0) {
                logsTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4"><i class="fas fa-info-circle me-2"></i>No event logs found matching criteria.</td></tr>';
                return;
            }
            
            logsTableBody.innerHTML = logs.map(log => {
                let lvlClass = 'text-warning';
                if (log.level.toLowerCase() === 'error' || log.level.toLowerCase() === 'critical') {
                    lvlClass = 'text-danger fw-bold';
                }
                return `
                    <tr>
                        <td class="text-muted" style="white-space: nowrap;">${log.timestamp}</td>
                        <td class="${lvlClass}">${log.level}</td>
                        <td><strong>${log.source}</strong></td>
                        <td class="terminal-text">${log.event_id}</td>
                        <td>${log.message}</td>
                    </tr>
                `;
            }).join('');
            
        } catch (error) {
            logsTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4"><i class="fas fa-exclamation-triangle me-2"></i>Failed to fetch logs: ${error.message}</td></tr>`;
        }
    };
    
    searchForm.addEventListener('submit', queryLogs);
    
    // Set Export Link dynamically based on search filters
    if (exportBtn) {
        exportBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const lvl = levelFilter.value;
            const query = searchQuery.value;
            const params = new URLSearchParams({ level: lvl, search: query });
            window.location.href = `/api/event_logs/export?${params.toString()}`;
        });
    }
}

/**
 * Configure Process monitor search and process termination triggers
 */
function setupProcessMonitor() {
    const processSearch = document.getElementById('process-search');
    const processTableBody = document.getElementById('process-table-body');
    if (!processTableBody) return;
    
    // Client-side search filter
    if (processSearch) {
        processSearch.addEventListener('input', () => {
            const query = processSearch.value.toLowerCase();
            const rows = processTableBody.querySelectorAll('tr');
            
            rows.forEach(row => {
                const name = row.querySelector('.process-name').textContent.toLowerCase();
                const pid = row.querySelector('.process-pid').textContent.toLowerCase();
                const user = row.querySelector('.process-user').textContent.toLowerCase();
                
                if (name.includes(query) || pid.includes(query) || user.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Handle process termination (End Task)
    processTableBody.addEventListener('click', async (e) => {
        const killBtn = e.target.closest('.kill-process-btn');
        if (!killBtn) return;
        
        const pid = parseInt(killBtn.getAttribute('data-pid'));
        const name = killBtn.getAttribute('data-name');
        
        if (!confirm(`WARNING: Are you sure you want to end task '${name}' (PID: ${pid})? Stopping crucial tasks might cause system instability.`)) {
            return;
        }
        
        killBtn.disabled = true;
        killBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        try {
            const response = await fetch('/api/process/kill', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pid: pid })
            });
            const data = await response.json();
            
            if (data.success) {
                // Dynamically remove row with nice CSS transition
                const row = killBtn.closest('tr');
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                }, 300);
            } else {
                alert(data.message);
                killBtn.disabled = false;
                killBtn.innerHTML = '<i class="fas fa-times me-1"></i>End Task';
            }
        } catch (error) {
            alert("Error communicating with backend: " + error.message);
            killBtn.disabled = false;
            killBtn.innerHTML = '<i class="fas fa-times me-1"></i>End Task';
        }
    });
}

/**
 * Configure local client software list search
 */
function setupSoftwareFilters() {
    const swSearch = document.getElementById('software-search');
    const swTableBody = document.getElementById('software-table-body');
    if (!swTableBody) return;
    
    if (swSearch) {
        swSearch.addEventListener('input', () => {
            const query = swSearch.value.toLowerCase();
            const rows = swTableBody.querySelectorAll('tr');
            
            rows.forEach(row => {
                const name = row.querySelector('.software-name').textContent.toLowerCase();
                const ver = row.querySelector('.software-version').textContent.toLowerCase();
                
                if (name.includes(query) || ver.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Configure full consolidated PDF/CSV report generation
 */
function setupReportGenerator() {
    const generateBtn = document.getElementById('generate-report-btn');
    if (!generateBtn) return;
    
    const formatSelect = document.getElementById('report-format');
    const reportHistoryTable = document.getElementById('reports-history-body');
    
    generateBtn.addEventListener('click', async () => {
        const format = formatSelect.value;
        
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Compiling Diagnostics...';
        
        try {
            const response = await fetch('/api/generate_report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: format })
            });
            const data = await response.json();
            
            if (data.success) {
                alert("Report Generated successfully!");
                
                // Prompt download
                window.location.href = `/reports/download/${data.report_id}`;
                
                // Reload history logs after a short wait
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                alert("Failed to generate report: " + data.message);
            }
        } catch (error) {
            alert("Error communicating with backend: " + error.message);
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-file-export me-2"></i>Generate & Export System Report';
        }
    });
}
