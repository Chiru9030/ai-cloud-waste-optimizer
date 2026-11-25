// popup.js - Chrome Extension for Azure Cloud Waste Segregation
// Supports port 5001 (default on macOS to prevent AirPlay conflicts) and fallback 5000
const API_CANDIDATES = ['http://localhost:5001', 'http://localhost:5000', 'http://127.0.0.1:5001'];
let API_BASE = 'http://localhost:5001';

async function resolveApiEndpoint() {
  for (const url of API_CANDIDATES) {
    try {
      const res = await fetch(`${url}/recommendations`, { method: 'GET' });
      if (res.ok) {
        API_BASE = url;
        const link = document.querySelector('.dashboard-link');
        if (link) link.href = url;
        return url;
      }
    } catch (e) {
      // try next
    }
  }
  return API_BASE;
}
const scanBtn = document.getElementById("scanBtn");
const optimizeBtn = document.getElementById("optimizeBtn");
const resultsTable = document.getElementById("resultsTable");
const resultsBody = resultsTable.querySelector('tbody');
const tableContainer = document.getElementById("tableContainer");
const statusMsg = document.getElementById("status_msg");
const kpiWaste = document.getElementById("kpiWaste");
const kpiSavings = document.getElementById("kpiSavings");
const azureBadge = document.getElementById("azureBadge");

let recommendationsData = [];

// --- FUNCTIONALITY 1: SCAN & CLASSIFY ---
scanBtn.addEventListener("click", async () => {
  statusMsg.innerText = "Scanning Azure telemetry & executing AI classifier...";
  scanBtn.disabled = true;
  optimizeBtn.classList.add('hidden');
  resultsBody.innerHTML = '';

  try {
    await resolveApiEndpoint();
    const response = await fetch(`${API_BASE}/recommendations`);
    const data = await response.json();
    recommendationsData = data.results || [];

    if (data.azure && data.azure.is_connected) {
      azureBadge.innerText = "Azure Live";
      azureBadge.style.color = "#4ade80";
    } else {
      azureBadge.innerText = "Azure Simulated";
      azureBadge.style.color = "#38bdf8";
    }

    if (data.summary) {
      kpiWaste.innerText = `${data.summary.waste_count} / ${data.summary.total_resources}`;
      kpiSavings.innerText = `$${data.summary.total_monthly_savings.toFixed(0)}/mo`;
    }

    displayResults(recommendationsData);
    
    statusMsg.innerText = `Scan complete. Found ${data.summary ? data.summary.waste_count : 0} cloud waste targets.`;
    tableContainer.classList.remove('hidden');
    
    const actionable = recommendationsData.some(r => r.recommended_action && r.recommended_action !== 'RETAIN');
    if (actionable) {
      optimizeBtn.classList.remove('hidden');
    }

  } catch (error) {
    statusMsg.innerText = "Error: Backend not running on http://localhost:5000. Start app.py!";
    console.error("Fetch error:", error);
  } finally {
    scanBtn.disabled = false;
  }
});

function displayResults(data) {
  resultsBody.innerHTML = '';
  data.forEach(resource => {
    const row = resultsBody.insertRow();
    
    // Resource Column
    const resCell = row.insertCell();
    resCell.innerHTML = `
      <div class="res-name">${resource.resource_id}</div>
      <div class="res-sku">${resource.region || ''}</div>
    `;

    // SKU / CPU Column
    const skuCell = row.insertCell();
    skuCell.innerHTML = `
      <div style="font-weight:600">${resource.sku}</div>
      <div style="font-size:10px; color:#94a3b8">${resource.cpu_avg.toFixed(1)}% CPU</div>
    `;

    // Status Tag Column
    const statusCell = row.insertCell();
    const tagInfo = getBadgeInfo(resource.classification);
    statusCell.innerHTML = `<span class="tag-badge ${tagInfo.className}">${tagInfo.label}</span>`;

    // Savings Column
    const savingsCell = row.insertCell();
    const savings = resource.potential_monthly_savings || 0;
    savingsCell.innerHTML = savings > 0 
      ? `<span style="color:#4ade80; font-weight:700">+$${savings.toFixed(0)}</span>`
      : `<span style="color:#64748b">$0</span>`;

    // Action Column
    const actionCell = row.insertCell();
    const action = resource.recommended_action;
    if (action && action !== 'RETAIN') {
      const btn = document.createElement('button');
      btn.className = 'action-btn';
      btn.innerText = action;
      btn.onclick = () => executeSingleAction(resource.resource_id, action, actionCell);
      actionCell.appendChild(btn);
    } else {
      actionCell.innerHTML = `<span style="color:#64748b; font-size:10px">Optimal</span>`;
    }
  });
}

function getBadgeInfo(classification) {
  switch(classification) {
    case 'IDLE_WASTE': return { label: 'IDLE', className: 'tag-idle' };
    case 'OVERPROVISIONED': return { label: 'RESIZE', className: 'tag-under' };
    case 'ORPHANED_STORAGE': return { label: 'ORPHAN', className: 'tag-storage' };
    case 'OPTIMIZED': return { label: 'DONE', className: 'tag-done' };
    default: return { label: 'HEALTHY', className: 'tag-optimal' };
  }
}

// --- FUNCTIONALITY 2: INDIVIDUAL ACTION REMEDIATION ---
async function executeSingleAction(id, action, cell) {
  cell.innerHTML = `<span style="color:#38bdf8; font-size:10px">Applying...</span>`;
  try {
    const res = await fetch(`${API_BASE}/api/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_id: id, action: action })
    });
    const result = await res.json();
    if (result.success) {
      cell.innerHTML = `<span style="color:#4ade80; font-size:10px; font-weight:700">Applied</span>`;
      statusMsg.innerText = `Azure action executed: ${action} on ${id}`;
      // Trigger scan to update numbers
      setTimeout(() => scanBtn.click(), 600);
    } else {
      cell.innerHTML = `<span style="color:#f87171; font-size:10px">Failed</span>`;
    }
  } catch (err) {
    cell.innerHTML = `<span style="color:#f87171; font-size:10px">Error</span>`;
  }
}

// --- FUNCTIONALITY 3: BULK OPTIMIZATION ---
optimizeBtn.addEventListener("click", async () => {
  statusMsg.innerText = "Executing bulk Azure FinOps optimization...";
  optimizeBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/optimize-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const result = await res.json();
    if (result.success) {
      statusMsg.innerText = result.message;
      setTimeout(() => scanBtn.click(), 600);
    }
  } catch (err) {
    statusMsg.innerText = "Error executing bulk optimization.";
  } finally {
    optimizeBtn.disabled = false;
  }
});
