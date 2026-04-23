/**
 * Mini-Ultra Web GUI
 * Frontend JavaScript for the chat interface.
 */

const API_BASE = window.location.origin;
let isProcessing = false;

// ── Initialization ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    setInterval(checkHealth, 30000);
    document.getElementById("messageInput").focus();
});

// ── Health Check ────────────────────────────────────────────────
async function checkHealth() {
    try {
        const resp = await fetch(`${API_BASE}/health`);
        const data = await resp.json();
        const dot = document.getElementById("statusDot");
        const text = document.getElementById("statusText");

        if (data.status === "running") {
            dot.className = "status-dot";
            text.textContent = `Online · ${data.tools_loaded} tools · ${data.llm_connected ? "LLM connected" : "LLM offline"}`;
        } else {
            dot.className = "status-dot offline";
            text.textContent = `Status: ${data.status}`;
        }
    } catch (e) {
        document.getElementById("statusDot").className = "status-dot offline";
        document.getElementById("statusText").textContent = "Disconnected";
    }
}

// ── Message Handling ────────────────────────────────────────────
function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();
    if (!message || isProcessing) return;

    // Hide welcome
    const welcome = document.getElementById("welcome");
    if (welcome) welcome.style.display = "none";

    // Add user message
    addMessage(message, "user");
    input.value = "";
    input.style.height = "auto";

    // Show typing indicator
    isProcessing = true;
    document.getElementById("sendBtn").disabled = true;
    const typingEl = showTyping();

    try {
        const resp = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });

        const data = await resp.json();
        removeTyping(typingEl);

        if (data.error) {
            addMessage(data.error, "agent error");
        } else {
            addMessage(data.response, "agent");
        }
    } catch (e) {
        removeTyping(typingEl);
        addMessage(`Connection error: ${e.message}`, "agent error");
    } finally {
        isProcessing = false;
        document.getElementById("sendBtn").disabled = false;
        input.focus();
    }
}

function sendQuick(text) {
    document.getElementById("messageInput").value = text;
    sendMessage();
}

// ── UI Helpers ──────────────────────────────────────────────────
function addMessage(text, type) {
    const container = document.getElementById("chatContainer");
    const div = document.createElement("div");
    div.className = `message ${type}`;

    // Simple markdown-like formatting
    let formatted = escapeHtml(text);
    // Code blocks
    formatted = formatted.replace(/```(\w*)\n?([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Bold
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // Line breaks
    formatted = formatted.replace(/\n/g, "<br>");

    div.innerHTML = formatted;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function showTyping() {
    const container = document.getElementById("chatContainer");
    const div = document.createElement("div");
    div.className = "typing-indicator";
    div.innerHTML = "<span></span><span></span><span></span>";
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function removeTyping(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

// ── Actions ─────────────────────────────────────────────────────
async function resetConversation() {
    try {
        await fetch(`${API_BASE}/conversation/reset`, { method: "POST" });
        const container = document.getElementById("chatContainer");
        container.innerHTML = "";
        const welcome = document.getElementById("welcome");
        if (welcome) welcome.style.display = "block";
        addMessage("Conversation reset.", "system");
    } catch (e) {
        addMessage("Failed to reset conversation.", "system");
    }
}

async function toggleInfo() {
    const panel = document.getElementById("infoPanel");
    panel.classList.toggle("open");

    if (panel.classList.contains("open")) {
        try {
            const resp = await fetch(`${API_BASE}/health`);
            const data = await resp.json();

            let html = "";
            html += infoItem("Status", data.status);
            html += infoItem("Uptime", formatUptime(data.uptime_seconds));
            html += infoItem("Tools", data.tool_names?.join(", ") || "None");
            html += infoItem("LLM Connected", data.llm_connected ? "Yes" : "No");
            html += infoItem("LLM Provider", data.config?.llm_provider || "N/A");
            html += infoItem("LLM Model", data.config?.llm_model || "N/A");
            html += infoItem("Memory", data.memory_enabled ? `${data.memory_stats?.total || 0} entries` : "Disabled");
            html += infoItem("Conversation", `${data.conversation_length} messages`);

            document.getElementById("infoContent").innerHTML = html;
        } catch (e) {
            document.getElementById("infoContent").innerHTML = "<p>Failed to load info.</p>";
        }
    }
}

async function runDiagnosis() {
    addMessage("Running self-diagnosis...", "system");
    try {
        const resp = await fetch(`${API_BASE}/diagnosis`);
        const data = await resp.json();
        addMessage("Diagnosis Results:\n```\n" + JSON.stringify(data, null, 2) + "\n```", "agent");
    } catch (e) {
        addMessage(`Diagnosis failed: ${e.message}`, "agent error");
    }
}

function infoItem(label, value) {
    return `<div class="info-item"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
}
