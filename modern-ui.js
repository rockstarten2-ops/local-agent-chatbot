const API_BASE_URL = "http://localhost:8000/api/agents";
const PENDING_UPLOADS_STORAGE_KEY = "localAgentPendingUploads";
const CHAT_HISTORY_STORAGE_KEY = "localAgentChatHistory";

let documents = {};
let conversationHistory = [];
let historyRuns = [];
let activeTrace = { traceId: null, events: [] };
let attachments = [];
let isBusyUploading = false;
let isQueryInProgress = false;
let selectedHistoryTraceId = null;
let pendingUploadsPoller = null;

const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const fileInput = document.getElementById("file-input");
const plusUploadBtn = document.getElementById("plus-upload-btn");
const documentsList = document.getElementById("documents-list");
const clearAllBtn = document.getElementById("clear-all-btn");
const clearChatBtn = document.getElementById("clear-chat-btn");
const routeBadge = document.getElementById("route-badge");
const timelineList = document.getElementById("timeline-list");
const historyList = document.getElementById("history-list");
const inputLockMessage = document.getElementById("input-lock-message");
const forceWebToggle = document.getElementById("force-web-toggle");
const webProviderSelect = document.getElementById("web-provider-select");
const attachmentChips = document.getElementById("attachment-chips");
const processingAnimation = document.getElementById("processing-animation");
const processingText = document.getElementById("processing-text");
const agentProcessing = document.getElementById("agent-processing-indicator");
const indicatorAgent = document.getElementById("indicator-agent");
const indicatorAction = document.getElementById("indicator-action");
const flowStepper = document.getElementById("flow-stepper");
const activeRunSummary = document.getElementById("active-run-summary");
const uploadProgress = document.getElementById("upload-progress");
const uploadStatus = document.getElementById("upload-status");
const progressFill = document.getElementById("progress-fill");
const documentProcessingList = document.getElementById("document-processing-list");
const processingDocs = document.getElementById("processing-docs");

document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    restoreChatHistory();
    restorePendingUploads();
    loadDocuments();
    loadHistory();
    renderAttachmentChips();
    renderFlowStepper([]);
    startPendingUploadsPolling();
});

function setupEventListeners() {
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    });
    sendBtn.addEventListener("click", sendMessage);
    plusUploadBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFileSelect);
    clearAllBtn.addEventListener("click", clearAllDocuments);
    clearChatBtn.addEventListener("click", clearAllChat);
}

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/agents`);
        if (!response.ok) throw new Error(`Failed to load documents: ${response.statusText}`);
        const data = await response.json();
        documents = {};
        if (Array.isArray(data.agents)) {
            data.agents.forEach((agent) => {
                documents[agent.collection_name] = {
                    name: agent.filename,
                    type: agent.file_type,
                    chunks: agent.chunks_count,
                    collectionName: agent.collection_name,
                };
            });
        }
        renderDocuments();
    } catch (error) {
        addMessage("assistant", `Failed loading documents: ${error.message}`);
    }
}

function renderDocuments() {
    const isEmpty = Object.keys(documents).length === 0;
    clearAllBtn.style.display = isEmpty ? "none" : "block";
    if (isEmpty) {
        documentsList.innerHTML = '<p class="empty-state">No documents uploaded yet</p>';
        return;
    }

    documentsList.innerHTML = Object.entries(documents).map(([key, doc]) => `
        <div class="document-item">
            <div>
                <div class="document-item-name">${escapeHTML(doc.name)}</div>
                <small>${doc.type.toUpperCase()} • ${doc.chunks} chunks</small>
            </div>
            <button type="button" class="document-item-delete" onclick="deleteDocument('${key}')">Delete</button>
        </div>
    `).join("");
}

async function handleFileSelect() {
    const files = Array.from(fileInput.files || []);
    if (!files.length) return;

    files.forEach((file) => {
        attachments.push({
            id: `${file.name}-${file.size}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
            file,
            name: file.name,
            status: "queued",
            progress: 0,
            message: "Queued",
        });
    });
    persistPendingUploads();
    renderAttachmentChips();
    setUploadBusy(true);

    for (const item of attachments.filter((a) => a.status === "queued")) {
        await processSingleUpload(item);
    }

    fileInput.value = "";
    await loadDocuments();
    setUploadBusy(false);
}

async function processSingleUpload(item) {
    updateAttachment(item.id, { status: "uploading", progress: 20, message: "Uploading" });
    uploadProgress.style.display = "block";
    uploadStatus.textContent = `Uploading ${item.name}...`;
    progressFill.style.width = "20%";
    showProcessingPanel();

    try {
        const formData = new FormData();
        formData.append("file", item.file);
        const response = await fetch(`${API_BASE_URL}/upload`, { method: "POST", body: formData });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || response.statusText);
        }

        const data = await response.json();
        updateAttachment(item.id, { status: "chunking", progress: 80, message: "Chunking + indexing" });
        uploadStatus.textContent = `Chunking ${item.name}...`;
        progressFill.style.width = "85%";
        showProcessingPanel();

        await wait(300);
        updateAttachment(item.id, { status: "ready", progress: 100, message: "Ready" });
        progressFill.style.width = "100%";
        addMessage("assistant", `Uploaded **${item.name}**\n- Type: ${data.file_type.toUpperCase()}\n- Chunks: ${data.chunks_count}`);
    } catch (error) {
        updateAttachment(item.id, { status: "error", progress: 0, message: "Failed" });
        addMessage("assistant", `Upload failed for ${item.name}: ${error.message}`);
    } finally {
        hideProcessingPanelIfIdle();
        setTimeout(() => {
            uploadProgress.style.display = "none";
            progressFill.style.width = "0%";
            uploadStatus.textContent = "";
        }, 400);
    }
}

function updateAttachment(id, updates) {
    attachments = attachments.map((item) => item.id === id ? { ...item, ...updates } : item);
    persistPendingUploads();
    renderAttachmentChips();
}

function renderAttachmentChips() {
    if (!attachmentChips) return;
    if (!attachments.length) {
        attachmentChips.innerHTML = "";
        return;
    }

    attachmentChips.innerHTML = attachments.slice(-8).map((item) => `
        <span class="attachment-chip ${item.status}">
            <span class="status-dot"></span>
            ${escapeHTML(item.name)}
            <span>(${escapeHTML(item.message)})</span>
        </span>
    `).join("");

    const activeItems = attachments.filter((item) => item.status === "uploading" || item.status === "chunking");
    if (activeItems.length) {
        documentProcessingList.style.display = "block";
        processingDocs.innerHTML = activeItems.map((item) => `
            <div class="processing-doc-item">${escapeHTML(item.name)} - ${escapeHTML(item.message)}</div>
        `).join("");
    } else {
        documentProcessingList.style.display = "none";
        processingDocs.innerHTML = "";
    }
}

function showProcessingPanel() {
    processingAnimation.style.display = "inline-flex";
    processingText.textContent = "Processing file chunks...";
    agentProcessing.style.display = "block";
    indicatorAgent.textContent = "Agent: File Processor";
    indicatorAction.textContent = "Uploading and chunking files";
}

function hideProcessingPanelIfIdle() {
    const stillBusy = attachments.some((item) => item.status === "uploading" || item.status === "chunking");
    if (!stillBusy) {
        processingAnimation.style.display = "none";
        agentProcessing.style.display = "none";
        persistPendingUploads();
    }
}

async function deleteDocument(collectionName) {
    try {
        const response = await fetch(`${API_BASE_URL}/agent/${collectionName}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Delete failed");
        delete documents[collectionName];
        renderDocuments();
        addMessage("assistant", "Document deleted.");
    } catch (error) {
        addMessage("assistant", `Delete failed: ${error.message}`);
    }
}

async function clearAllDocuments() {
    if (!confirm("Delete all documents?")) return;
    try {
        const promises = Object.keys(documents).map((key) => fetch(`${API_BASE_URL}/agent/${key}`, { method: "DELETE" }));
        await Promise.all(promises);
        documents = {};
        attachments = [];
        conversationHistory = [];
        persistChatHistory();
        persistPendingUploads();
        renderAttachmentChips();
        renderDocuments();
        resetTracePanels();
        chatMessages.innerHTML = "";
        await loadHistory();
        addMessage("assistant", "All documents cleared.");
    } catch (error) {
        addMessage("assistant", `Clear failed: ${error.message}`);
    }
}

function clearAllChat() {
    if (!confirm("Clear all chat messages?")) return;
    conversationHistory = [];
    persistChatHistory();
    chatMessages.innerHTML = "";
    resetTracePanels();
}

async function sendMessage() {
    if (isBusyUploading || isQueryInProgress) return;
    const message = chatInput.value.trim();
    if (!message) return;

    addMessage("user", message);
    chatInput.value = "";
    chatInput.style.height = "auto";
    isQueryInProgress = true;
    updateInputAvailability();
    resetTracePanels();

    const loadingDiv = document.createElement("div");
    loadingDiv.className = "chat-message assistant";
    loadingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-loading"><span></span><span></span><span></span></div>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        processingAnimation.style.display = "inline-flex";
        processingText.textContent = "Running multi-agent flow...";
        agentProcessing.style.display = "block";
        indicatorAgent.textContent = "Agent: Query Router";
        indicatorAction.textContent = "Determining best flow";

        const result = await processQuery(message);
        loadingDiv.remove();
        if (result.success) {
            addMessage("assistant", result.message, result.metadata);
            await loadHistory();
        } else {
            addMessage("assistant", result.message);
        }
    } catch (error) {
        loadingDiv.remove();
        addMessage("assistant", `Error: ${error.message}`);
    } finally {
        processingAnimation.style.display = "none";
        agentProcessing.style.display = "none";
        isQueryInProgress = false;
        updateInputAvailability();
        chatInput.focus();
    }
}

async function processQuery(query) {
    try {
        const data = await streamQuery(query);
        if (data && data.success === false) return { success: false, message: data.answer || "Query failed" };
        return formatFinalResponse(data);
    } catch (error) {
        return { success: false, message: `Error: ${error.message}` };
    }
}

async function streamQuery(query) {
    const forceWebSearch = Boolean(forceWebToggle?.checked);
    const webSearchProvider = (webProviderSelect?.value || "auto").toLowerCase();
    const response = await fetch(`${API_BASE_URL}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            query,
            use_llm: true,
            force_web_search: forceWebSearch,
            web_search_top_k: 6,
            web_search_provider: webSearchProvider,
        }),
    });
    if (!response.ok) throw new Error(`Stream request failed: ${response.statusText}`);
    if (!response.body) throw new Error("Streaming is not supported by this browser");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let finalResponse = null;

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const messages = buffer.split("\n\n");
        buffer = messages.pop() || "";

        for (const chunk of messages) {
            const parsed = parseSSEMessage(chunk);
            if (!parsed) continue;
            const { eventName, data } = parsed;
            handleStreamEvent(eventName, data);
            if (eventName === "final_response" && data.payload?.response) finalResponse = data.payload.response;
        }
    }

    if (!finalResponse) throw new Error("No final response received");
    return finalResponse;
}

function parseSSEMessage(raw) {
    const lines = raw.split("\n");
    let eventName = "message";
    let dataLine = "";
    lines.forEach((line) => {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        if (line.startsWith("data:")) dataLine += line.slice(5).trim();
    });
    if (!dataLine) return null;
    try {
        return { eventName, data: JSON.parse(dataLine) };
    } catch {
        return null;
    }
}

function handleStreamEvent(eventName, eventEnvelope) {
    const payload = eventEnvelope.payload || {};
    if (payload.trace_id) activeTrace.traceId = payload.trace_id;
    activeTrace.events.push({ eventName, payload, timestamp: eventEnvelope.timestamp || "" });

    appendTimelineEvent(eventName, payload);
    renderFlowStepper(activeTrace.events);

    if (eventName === "routing_decision") {
        updateRouteBadge(payload.route_type || payload.agent, payload.reason || "Routed");
        indicatorAgent.textContent = `Agent: ${friendlyRouteName(payload.route_type || payload.agent)}`;
        indicatorAction.textContent = payload.reason || "Processing";
    }
    if (eventName === "agent_started") {
        processingText.textContent = `${friendlyRouteName(payload.agent || "agent")} active...`;
    }
}

function appendTimelineEvent(eventName, payload) {
    if (timelineList.querySelector(".empty-state")) timelineList.innerHTML = "";
    const item = document.createElement("div");
    item.className = "timeline-item";
    item.innerHTML = `
        <div class="timeline-item-title">${escapeHTML(eventName.replace(/_/g, " "))}</div>
        <div class="timeline-item-body">${escapeHTML(summarizeEventPayload(eventName, payload))}</div>
    `;
    timelineList.appendChild(item);
    timelineList.scrollTop = timelineList.scrollHeight;
}

function summarizeEventPayload(eventName, payload) {
    if (eventName === "routing_decision") return `${friendlyRouteName(payload.route_type || payload.agent)} | ${payload.reason || "route selected"}`;
    if (eventName === "chapter_resolution") return `${payload.document || "Document"} | ${payload.mode || "resolved"} | chunks: ${payload.matched_chunks || 0}`;
    if (eventName === "retrieval_completed") return `${payload.document || "Document"} | ${payload.result_count || 0} chunks`;
    if (eventName === "summary_partial") return `${payload.document || "Document"} partial summary`;
    if (eventName === "web_search_started") {
        const provider = payload.provider_preference ? ` [${payload.provider_preference}]` : "";
        return `Running web search${provider} for "${payload.query || ""}"`;
    }
    if (eventName === "web_search_completed") {
        const provider = payload.provider_used ? ` via ${payload.provider_used}` : "";
        return `Web search complete${provider} | ${payload.result_count || 0} results`;
    }
    if (eventName === "agent_started") return `${friendlyRouteName(payload.agent || "agent")} started`;
    if (eventName === "error") return payload.message || "Error";
    return payload.document || payload.message || "processing";
}

function renderFlowStepper(events) {
    const steps = [
        { key: "query_received", label: "query received" },
        { key: "routing_decision", label: "routing decision" },
        { key: "web_search_completed", label: "web search" },
        { key: "agent_started", label: "agent execution" },
        { key: "final_response", label: "response completion" },
    ];
    const seen = new Set(events.map((event) => event.eventName));
    const active = steps.find((step) => !seen.has(step.key));

    flowStepper.innerHTML = steps.map((step) => {
        let cls = "pending";
        if (seen.has(step.key)) cls = "done";
        if (active && active.key === step.key) cls = "active";
        return `<div class="flow-step ${cls}">${step.label}</div>`;
    }).join("");
}

function formatFinalResponse(data) {
    const routeType = data.routing?.route_type || data.agent;
    let message = "";

    if (data.agent === "general_llm") {
        message = data.answer || "";
    } else if (["all_documents_summary", "single_document_summary", "chapter_summary"].includes(data.agent)) {
        message = "";
        (data.summaries || []).forEach((summary) => {
            const chapter = summary.chapters ? `\n_Targets: ${summary.chapters.join(", ")}_` : "";
            message += `**${summary.document}:**\n${summary.summary}${chapter}\n\n`;
        });
    } else if (data.agent === "document_retriever") {
        message = data.answer || "";
    } else if (data.agent === "internet_search") {
        message = data.answer || "";
    } else {
        message = data.answer || "Completed.";
    }

    indicatorAgent.textContent = `Agent: ${friendlyRouteName(routeType)}`;
    indicatorAction.textContent = data.routing?.reason || "Completed";

    return {
        success: true,
        message,
        metadata: {
            traceId: data.trace_id,
            agent: data.agent,
            routeType,
            routeReason: data.routing?.reason || "",
            routing: data.routing || {},
            events: activeTrace.events,
            results: data.results || [],
            webResults: data.web_results || [],
            webProvider: data.web_provider || data.web_provider_used || "",
            webProviderUsed: data.web_provider_used || data.web_provider || "",
            webFallbackUsed: Boolean(data.web_fallback_used),
            summaries: data.summaries || [],
        },
    };
}

function addMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${role}`;
    const avatar = role === "user" ? "You" : "AI";
    const formattedContent = role === "assistant" ? markdownToHTML(content) : escapeHTML(content);

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${formattedContent}</div>
    `;

    if (role === "assistant") {
        const contentEl = messageDiv.querySelector(".message-content");
        const metadataRow = document.createElement("div");
        metadataRow.className = "message-meta";

        const routeType = metadata.routeType || metadata.agent;
        if (routeType) metadataRow.innerHTML += `<span class="meta-chip">Agent: ${escapeHTML(friendlyRouteName(routeType))}</span>`;
        if (metadata.routeReason) metadataRow.innerHTML += `<span class="meta-chip">${escapeHTML(metadata.routeReason)}</span>`;
        if (metadata.webProviderUsed) metadataRow.innerHTML += `<span class="meta-chip">Web: ${escapeHTML(metadata.webProviderUsed)}</span>`;
        if (metadata.webFallbackUsed) metadataRow.innerHTML += `<span class="meta-chip">Fallback used</span>`;
        if (metadata.traceId) metadataRow.innerHTML += `<span class="meta-chip">Trace: ${escapeHTML(metadata.traceId.slice(0, 8))}</span>`;
        if (metadataRow.innerHTML) contentEl.appendChild(metadataRow);

        if (Array.isArray(metadata.results) && metadata.results.length > 0) {
            contentEl.appendChild(renderSourceCards(metadata.results));
        }
        if (Array.isArray(metadata.webResults) && metadata.webResults.length > 0) {
            contentEl.appendChild(renderWebSources(metadata.webResults));
        }

        if (Array.isArray(metadata.events) && metadata.events.length > 0) {
            contentEl.appendChild(renderTraceDrawer(metadata));
        }
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    conversationHistory.push({ role, content, metadata });
    persistChatHistory();
}

function renderSourceCards(results) {
    const details = document.createElement("details");
    details.className = "retrieved-chunks";
    details.innerHTML = `<summary>Retrieved chunks (${results.length})</summary>`;
    const list = document.createElement("div");
    list.className = "chunk-list";

    results.slice(0, 5).forEach((result) => {
        const similarity = Math.round((result.similarity || 0) * 100);
        const preview = (result.content || "").slice(0, 300);
        const item = document.createElement("div");
        item.className = "chunk-item";
        item.innerHTML = `
            <div class="chunk-head">
                <span>${escapeHTML(result.document || "Document")}</span>
                <span>${similarity}%</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width:${similarity}%"></div></div>
            <div class="chunk-preview">${escapeHTML(preview)}${preview.length >= 300 ? "..." : ""}</div>
        `;
        list.appendChild(item);
    });
    details.appendChild(list);
    return details;
}

function renderTraceDrawer(metadata) {
    const details = document.createElement("details");
    details.className = "trace-drawer";
    details.innerHTML = `<summary>Trace details</summary>`;
    const list = document.createElement("div");
    list.className = "trace-list";

    const route = metadata.routeType ? `Route: ${friendlyRouteName(metadata.routeType)}` : "Route unavailable";
    list.innerHTML += `<div class="trace-list-item">${escapeHTML(route)}</div>`;
    if (metadata.routeReason) list.innerHTML += `<div class="trace-list-item">${escapeHTML(metadata.routeReason)}</div>`;
    metadata.events.slice(-12).forEach((event) => {
        list.innerHTML += `<div class="trace-list-item">${escapeHTML(event.eventName)} ${event.timestamp ? `- ${event.timestamp}` : ""}</div>`;
    });

    details.appendChild(list);
    return details;
}

function renderWebSources(results) {
    const details = document.createElement("details");
    details.className = "web-sources";
    details.innerHTML = `<summary>Web sources (${results.length})</summary>`;
    const list = document.createElement("div");
    list.className = "web-source-list";

    results.slice(0, 8).forEach((result) => {
        const item = document.createElement("div");
        item.className = "web-source-item";
        const title = escapeHTML(result.title || "Untitled");
        const url = escapeHTML(result.url || "");
        const source = escapeHTML(result.source || "");
        const snippet = escapeHTML((result.snippet || "").slice(0, 320));
        item.innerHTML = `
            <div class="web-source-head">
                <a class="web-source-title" href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
                <span>#${result.rank || "-"}</span>
            </div>
            <div class="web-source-url">${source}</div>
            <div class="web-source-snippet">${snippet}${snippet.length >= 320 ? "..." : ""}</div>
        `;
        list.appendChild(item);
    });

    details.appendChild(list);
    return details;
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history?limit=40`);
        if (!response.ok) throw new Error(response.statusText);
        const data = await response.json();
        historyRuns = Array.isArray(data.history) ? data.history : [];
        renderHistory(historyRuns);
    } catch (error) {
        historyList.innerHTML = `<p class="empty-state">History unavailable: ${escapeHTML(error.message)}</p>`;
    }
}

function renderHistory(historyItems) {
    if (!historyItems.length) {
        historyList.innerHTML = '<p class="empty-state">No history yet</p>';
        return;
    }

    historyList.innerHTML = historyItems.map((item) => {
        const route = item.routing?.route_type || item.response?.agent || "unknown";
        const query = (item.query || "").slice(0, 90);
        const selectedClass = selectedHistoryTraceId === item.trace_id ? "is-selected" : "";
        return `
            <button type="button" class="history-item ${selectedClass}" data-trace-id="${escapeHTML(item.trace_id || "")}">
                <div class="history-item-route">${escapeHTML(friendlyRouteName(route))}</div>
                <div>${escapeHTML(query)}</div>
                <small>${Array.isArray(item.events) ? item.events.length : 0} events</small>
            </button>
        `;
    }).join("");

    historyList.querySelectorAll(".history-item").forEach((button) => {
        button.addEventListener("click", () => {
            const traceId = button.getAttribute("data-trace-id");
            selectedHistoryTraceId = traceId;
            renderHistory(historyRuns);
            showHistoryRunSummary(traceId);
        });
    });
}

function showHistoryRunSummary(traceId) {
    const item = historyRuns.find((run) => run.trace_id === traceId);
    if (!item) {
        activeRunSummary.innerHTML = '<p class="empty-state">No run selected.</p>';
        return;
    }
    const route = item.routing?.route_type || item.response?.agent || "unknown";
    const events = Array.isArray(item.events) ? item.events : [];
    const webResultCount = Array.isArray(item.response?.web_results) ? item.response.web_results.length : 0;
    activeRunSummary.innerHTML = `
        <div class="active-run-summary-item"><strong>Query</strong><br>${escapeHTML(item.query || "")}</div>
        <div class="active-run-summary-item"><strong>Route</strong><br>${escapeHTML(friendlyRouteName(route))}</div>
        <div class="active-run-summary-item"><strong>Events</strong><br>${events.length}</div>
        <div class="active-run-summary-item"><strong>Web Results</strong><br>${webResultCount}</div>
        <div class="active-run-summary-item"><strong>Completed</strong><br>${escapeHTML(item.completed_at || "N/A")}</div>
    `;
}

function updateRouteBadge(routeType, reason) {
    routeBadge.querySelector(".route-agent").textContent = friendlyRouteName(routeType || "general_llm");
    routeBadge.querySelector(".route-reason").textContent = reason || "Route selected";
}

function resetTracePanels() {
    activeTrace = { traceId: null, events: [] };
    timelineList.innerHTML = '<p class="empty-state">Run a query to see live flow</p>';
    updateRouteBadge("general_llm", "Waiting for query");
    renderFlowStepper([]);
    activeRunSummary.innerHTML = '<p class="empty-state">No run selected.</p>';
}

function setUploadBusy(isBusy) {
    isBusyUploading = isBusy;
    updateInputAvailability();
}

function updateInputAvailability() {
    const disabled = isBusyUploading || isQueryInProgress;
    chatInput.disabled = disabled;
    sendBtn.disabled = disabled;
    plusUploadBtn.disabled = disabled;
    fileInput.disabled = disabled;
    inputLockMessage.style.display = isBusyUploading ? "block" : "none";
}

function friendlyRouteName(routeType) {
    const map = {
        general_llm: "General LLM",
        document_retriever: "Document Retriever",
        internet_search: "Internet Search",
        all_documents_summary: "All Documents Summarizer",
        single_document_summary: "Single Document Summarizer",
        chapter_summary: "Chapter Summarizer",
    };
    return map[routeType] || "Agent";
}

function markdownToHTML(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/\n/g, "<br>")
        .replace(/^- (.+)$/gm, "<li>$1</li>")
        .replace(/(<li>.+<\/li>)/s, "<ul>$1</ul>")
        .replace(/^(\d+)\. (.+)$/gm, "<li>$2</li>");
}

function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
}

function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function persistChatHistory() {
    try {
        // Keep recent messages only to avoid unbounded storage growth.
        const recentMessages = conversationHistory.slice(-120);
        sessionStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(recentMessages));
    } catch {
        // Ignore storage issues.
    }
}

function restoreChatHistory() {
    try {
        const raw = sessionStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
        if (!raw) return;
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed) || parsed.length === 0) return;

        conversationHistory = [];
        chatMessages.innerHTML = "";
        parsed.forEach((entry) => {
            if (entry && typeof entry.role === "string" && typeof entry.content === "string") {
                addMessage(entry.role, entry.content, entry.metadata || {});
            }
        });
    } catch {
        // Ignore parse errors and continue with empty chat.
    }
}

function persistPendingUploads() {
    const pending = attachments
        .filter((item) => ["queued", "uploading", "chunking"].includes(item.status))
        .map((item) => ({
            id: item.id,
            name: item.name,
            status: item.status,
            progress: item.progress || 0,
            message: item.message || "Processing",
        }));
    try {
        sessionStorage.setItem(PENDING_UPLOADS_STORAGE_KEY, JSON.stringify(pending));
    } catch {
        // Ignore storage errors.
    }
}

function restorePendingUploads() {
    try {
        const raw = sessionStorage.getItem(PENDING_UPLOADS_STORAGE_KEY);
        if (!raw) return;
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return;

        const restored = parsed.map((item) => ({
            id: item.id || `${item.name}-${Date.now()}`,
            file: null,
            name: item.name || "Unknown file",
            status: item.status || "chunking",
            progress: item.progress || 0,
            message: item.message || "Processing",
        }));
        if (restored.length) {
            attachments = [...attachments, ...restored];
            setUploadBusy(true);
            renderAttachmentChips();
            showProcessingPanel();
            uploadStatus.textContent = "Resuming file processing status...";
            uploadProgress.style.display = "block";
            progressFill.style.width = "70%";
        }
    } catch {
        // Ignore storage parse errors.
    }
}

function startPendingUploadsPolling() {
    if (pendingUploadsPoller) clearInterval(pendingUploadsPoller);
    pendingUploadsPoller = setInterval(async () => {
        const active = attachments.filter((item) => ["queued", "uploading", "chunking"].includes(item.status));
        if (!active.length) return;

        try {
            const response = await fetch(`${API_BASE_URL}/agents`);
            if (!response.ok) return;
            const data = await response.json();
            const loadedFiles = new Set((data.agents || []).map((agent) => (agent.filename || "").toLowerCase()));
            let changed = false;

            attachments = attachments.map((item) => {
                if (!["queued", "uploading", "chunking"].includes(item.status)) return item;
                if (loadedFiles.has((item.name || "").toLowerCase())) {
                    changed = true;
                    return { ...item, status: "ready", message: "Ready", progress: 100 };
                }
                return item;
            });

            if (changed) {
                renderAttachmentChips();
                persistPendingUploads();
                await loadDocuments();
            }

            const stillPending = attachments.some((item) => ["queued", "uploading", "chunking"].includes(item.status));
            if (!stillPending) {
                setUploadBusy(false);
                uploadProgress.style.display = "none";
                progressFill.style.width = "0%";
                hideProcessingPanelIfIdle();
            }
        } catch {
            // Ignore polling errors; keep trying.
        }
    }, 2000);
}

function closeModal() {
    document.getElementById("content-modal").style.display = "none";
}
