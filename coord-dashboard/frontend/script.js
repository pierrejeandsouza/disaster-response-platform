const API_BASE = "http://127.0.0.1:8000";

async function fetchJSON(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`${response.status}: ${body}`);
    }
    return response.json();
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadSummary() {
    const grid = document.getElementById("summaryGrid");
    try {
        const summary = await fetchJSON(`${API_BASE}/dashboard-summary`);
        grid.innerHTML = `
            <div class="summary-card">
                <div class="value">${summary.active_incidents}</div>
                <div class="label">Active incidents</div>
            </div>
            <div class="summary-card">
                <div class="value">${summary.people_needing_help}</div>
                <div class="label">People needing help</div>
            </div>
            <div class="summary-card">
                <div class="value">${summary.available_resources}</div>
                <div class="label">Units available</div>
            </div>
            <div class="summary-card">
                <div class="value">${summary.pending_count}</div>
                <div class="label">Waiting on a unit</div>
            </div>
        `;
    } catch (err) {
        grid.innerHTML = `<p class="empty-state">Could not load summary: ${escapeHtml(err.message)}</p>`;
    }
}

async function loadRanked() {
    const container = document.getElementById("rankedList");
    try {
        const ranked = await fetchJSON(`${API_BASE}/emergency-requests/ranked`);
        if (ranked.length === 0) {
            container.innerHTML = `<p class="empty-state">Board is clear. Every request has a unit assigned.</p>`;
            return;
        }
        container.innerHTML = ranked.map(r => `
            <div class="item-card severity-${r.severity}">
                <div class="item-title">
                    <span>${escapeHtml(r.location)} -- ${escapeHtml(r.request_type)}</span>
                    <span class="badge badge-${r.status}">${r.severity}</span>
                </div>
                <div class="item-meta">${r.people_affected} people affected -- ${escapeHtml(r.description || "")}</div>
            </div>
        `).join("");
    } catch (err) {
        container.innerHTML = `<p class="empty-state">Could not load: ${escapeHtml(err.message)}</p>`;
    }
}

async function loadRequests() {
    const container = document.getElementById("requestsList");
    try {
        const requests = await fetchJSON(`${API_BASE}/emergency-requests`);
        if (requests.length === 0) {
            container.innerHTML = `<p class="empty-state">No requests logged yet.</p>`;
            return;
        }
        container.innerHTML = requests.map(r => `
            <div class="item-card severity-${r.severity}">
                <div class="item-title">
                    <span>${escapeHtml(r.location)} -- ${escapeHtml(r.request_type)}</span>
                    <span class="badge badge-${r.status}">${r.status}</span>
                </div>
                <div class="item-meta">${r.people_affected} people -- ${r.severity}</div>
                ${r.status === "ASSIGNED" ? `<button class="resolve-btn" data-id="${r.id}">Mark resolved</button>` : ""}
            </div>
        `).join("");

        container.querySelectorAll(".resolve-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                await fetchJSON(`${API_BASE}/emergency-requests/${btn.dataset.id}/resolve`, { method: "POST" });
                await refreshAll();
            });
        });
    } catch (err) {
        container.innerHTML = `<p class="empty-state">Could not load: ${escapeHtml(err.message)}</p>`;
    }
}

async function loadResources() {
    const container = document.getElementById("resourcesList");
    try {
        const resources = await fetchJSON(`${API_BASE}/resources`);
        if (resources.length === 0) {
            container.innerHTML = `<p class="empty-state">No units registered yet.</p>`;
            return;
        }
        container.innerHTML = resources.map(r => `
            <div class="item-card" style="border-left-color: ${r.available ? 'var(--low)' : 'var(--critical)'}">
                <div class="item-title">
                    <span>${escapeHtml(r.name)}</span>
                    <span class="badge" style="color:${r.available ? 'var(--low)' : 'var(--critical)'}; border-color:${r.available ? 'var(--low)' : 'var(--critical)'}">
                        ${r.available ? "Available" : "In use"}
                    </span>
                </div>
                <div class="item-meta">${escapeHtml(r.resource_type)} -- ${escapeHtml(r.location)} -- capacity ${r.capacity}</div>
            </div>
        `).join("");
    } catch (err) {
        container.innerHTML = `<p class="empty-state">Could not load: ${escapeHtml(err.message)}</p>`;
    }
}

async function refreshAll() {
    await Promise.all([loadSummary(), loadRanked(), loadRequests(), loadResources()]);
}

document.getElementById("refreshBtn").addEventListener("click", refreshAll);

document.getElementById("requestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const statusEl = document.getElementById("requestFormStatus");
    const payload = {
        location: form.location.value,
        request_type: form.request_type.value,
        people_affected: parseInt(form.people_affected.value, 10),
        severity: form.severity.value,
        description: form.description.value,
    };
    try {
        const result = await fetchJSON(`${API_BASE}/emergency-requests`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        statusEl.textContent = result.assigned_resource
            ? `Submitted and auto-assigned to ${result.assigned_resource.name}.`
            : `Submitted. No unit free yet -- added to the incident board.`;
        statusEl.className = "form-status success";
        form.reset();
        await refreshAll();
    } catch (err) {
        statusEl.textContent = `Error: ${err.message}`;
        statusEl.className = "form-status error";
    }
});

document.getElementById("resourceForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const statusEl = document.getElementById("resourceFormStatus");
    const payload = {
        name: form.name.value,
        resource_type: form.resource_type.value,
        location: form.location.value,
        capacity: parseInt(form.capacity.value, 10),
    };
    try {
        await fetchJSON(`${API_BASE}/resources`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        statusEl.textContent = "Unit registered.";
        statusEl.className = "form-status success";
        form.reset();
        await refreshAll();
    } catch (err) {
        statusEl.textContent = `Error: ${err.message}`;
        statusEl.className = "form-status error";
    }
});

refreshAll();
setInterval(refreshAll, 10000);
