// Configuration
const API_BASE_URL = 'http://localhost:8000/api/agents';

// State
let documents = {};
let conversationHistory = [];
let activeTrace = { traceId: null, events: [] };
let isBusyUploading = false;
let isQueryInProgress = false;

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const uploadArea = document.getElementById('upload-area');
const documentsList = document.getElementById('documents-list');
const clearAllBtn = document.getElementById('clear-all-btn');
const routeBadge = document.getElementById('route-badge');
const timelineList = document.getElementById('timeline-list');
const historyList = document.getElementById('history-list');
const inputLockMessage = document.getElementById('input-lock-message');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadDocuments();
    loadHistory();
});

function setupEventListeners() {
    // Chat input
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // File upload
    fileInput.addEventListener('change', handleFileSelect);
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-color)';
        uploadArea.style.background = 'rgba(37, 99, 235, 0.05)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--border-color)';
        uploadArea.style.background = 'transparent';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-color)';
        uploadArea.style.background = 'transparent';
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
    });

    // Clear all
    clearAllBtn.addEventListener('click', clearAllDocuments);

    // Auto-grow textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
}

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/agents`);
        if (!response.ok) {
            throw new Error(`Failed to load documents: ${response.statusText}`);
        }
        
        const data = await response.json();

        documents = {};
        if (data.agents && Array.isArray(data.agents)) {
            data.agents.forEach(agent => {
                documents[agent.collection_name] = {
                    name: agent.filename,
                    type: agent.file_type,
                    chunks: agent.chunks_count,
                    collectionName: agent.collection_name
                };
            });
        }

        renderDocuments();
        console.log('Documents loaded:', Object.keys(documents).length);
    } catch (error) {
        console.error('Error loading documents:', error);
        addMessage('assistant', `⚠️ Error loading documents: ${error.message}`);
    }
}

function renderDocuments() {
    const isEmpty = Object.keys(documents).length === 0;
    clearAllBtn.style.display = isEmpty ? 'none' : 'block';

    if (isEmpty) {
        documentsList.innerHTML = '<p class="empty-state">No documents uploaded yet</p>';
        return;
    }

    documentsList.innerHTML = Object.entries(documents).map(([key, doc]) => `
        <div class="document-item">
            <div>
                <div class="document-item-name">📄 ${doc.name}</div>
                <small>${doc.type.toUpperCase()} • ${doc.chunks} chunks</small>
            </div>
            <button class="document-item-delete" onclick="deleteDocument('${key}')">Delete</button>
        </div>
    `).join('');
}

async function handleFileSelect() {
    const files = fileInput.files;
    if (!files.length) return;

    setUploadBusy(true);

    try {
        for (let file of files) {
            await uploadFile(file);
        }
    } finally {
        setUploadBusy(false);
        fileInput.value = '';
    }
}

async function uploadFile(file) {
    const uploadProgress = document.getElementById('upload-progress');
    const uploadStatus = document.getElementById('upload-status');
    const progressFill = document.getElementById('progress-fill');
    const processingAnimation = document.getElementById('processing-animation');
    const processingText = document.getElementById('processing-text');

    uploadProgress.style.display = 'block';
    uploadStatus.textContent = `📤 Uploading ${file.name}...`;
    progressFill.style.width = '0%';

    try {
        const formData = new FormData();
        formData.append('file', file);

        // Simulate progress
        progressFill.style.width = '30%';

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        progressFill.style.width = '70%';

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
        }

        const data = await response.json();
        progressFill.style.width = '100%';
        uploadStatus.textContent = `✅ Processing...`;

        // Show processing animations with document info
        processingAnimation.style.display = 'block';
        processingText.textContent = `📄 Processing ${file.name}...`;
        
        const agentProcessing = document.getElementById('agent-processing-indicator');
        const documentProcessingList = document.getElementById('document-processing-list');
        const processingDocs = document.getElementById('processing-docs');
        
        agentProcessing.style.display = 'block';
        document.getElementById('indicator-agent').textContent = 'Agent: File Processor';
        document.getElementById('indicator-action').textContent = `Indexing ${file.name}...`;
        
        documentProcessingList.style.display = 'block';
        processingDocs.innerHTML = `
            <div class="processing-doc-item">
                <div class="processing-doc-spinner"></div>
                <span class="processing-doc-name">${file.name}</span>
            </div>
        `;

        // Add success message
        addMessage('assistant', `✅ Successfully uploaded **${file.name}**\n- Type: ${data.file_type.toUpperCase()}\n- Chunks: ${data.chunks_count}`);

        // Reload documents - WAIT for this to complete
        console.log('Reloading documents after upload...');
        await loadDocuments();
        console.log('Documents after reload:', Object.keys(documents).length);

        // Hide processing indicators
        processingAnimation.style.display = 'none';
        agentProcessing.style.display = 'none';
        documentProcessingList.style.display = 'none';
        uploadStatus.textContent = `✅ Document ready!`;

        // Keep progress visible for a bit then hide
        setTimeout(() => {
            uploadProgress.style.display = 'none';
            progressFill.style.width = '0%';
            uploadStatus.textContent = '';
        }, 1500);
    } catch (error) {
        uploadStatus.textContent = `❌ Failed: ${error.message}`;
        progressFill.style.width = '0%';
        processingAnimation.style.display = 'none';
        
        const agentProcessing = document.getElementById('agent-processing-indicator');
        const documentProcessingList = document.getElementById('document-processing-list');
        agentProcessing.style.display = 'none';
        documentProcessingList.style.display = 'none';
        
        console.error('Upload error:', error);
        addMessage('assistant', `❌ Upload failed: ${error.message}`);
        
        setTimeout(() => {
            uploadProgress.style.display = 'none';
        }, 3000);
    }
}

async function deleteDocument(collectionName) {
    try {
        const response = await fetch(`${API_BASE_URL}/agent/${collectionName}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Delete failed');

        delete documents[collectionName];
        renderDocuments();
        addMessage('assistant', '🗑️ Document deleted successfully');
    } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete document');
    }
}

async function clearAllDocuments() {
    if (!confirm('Are you sure you want to delete all documents?')) return;

    try {
        const promises = Object.keys(documents).map(key =>
            fetch(`${API_BASE_URL}/agent/${key}`, { method: 'DELETE' })
        );

        await Promise.all(promises);
        documents = {};
        conversationHistory = [];
        resetTracePanels();
        renderDocuments();
        chatMessages.innerHTML = '';
        addMessage('assistant', '🗑️ All documents cleared. Ready for new uploads!');
        await loadHistory();
    } catch (error) {
        console.error('Clear error:', error);
        alert('Failed to clear documents');
    }
}

async function sendMessage() {
    if (isBusyUploading || isQueryInProgress) return;

    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage('user', message);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    isQueryInProgress = true;
    updateInputAvailability();

    // Show processing indicators
    const processingAnimation = document.getElementById('processing-animation');
    const processingText = document.getElementById('processing-text');
    const agentProcessing = document.getElementById('agent-processing-indicator');
    
    // Show analyzing state
    processingAnimation.style.display = 'block';
    processingText.textContent = '🔍 Analyzing query...';
    agentProcessing.style.display = 'block';
    document.getElementById('indicator-agent').textContent = 'Agent: Analyzing';
    document.getElementById('indicator-action').textContent = 'Determining best approach...';
    resetTracePanels();

    // Add loading indicator in chat
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message assistant';
    loadingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await processQuery(message);
        loadingDiv.remove();

        if (response.success) {
            addMessage('assistant', response.message, response.metadata);
            await loadHistory();
        } else {
            addMessage('assistant', `⚠️ ${response.message}`);
        }
    } catch (error) {
        loadingDiv.remove();
        console.error('Error:', error);
        addMessage('assistant', `❌ Error: ${error.message}`);
    }

    // Hide processing indicators
    processingAnimation.style.display = 'none';
    agentProcessing.style.display = 'none';
    isQueryInProgress = false;
    updateInputAvailability();
    chatInput.focus();
}

async function processQuery(query) {
    try {
        const data = await streamQuery(query);
        if ('success' in data && !data.success) {
            return { success: false, message: data.answer || 'Query processing failed' };
        }
        return formatFinalResponse(data);
    } catch (error) {
        console.error('Error:', error);
        return {
            success: false,
            message: `❌ Error: ${error.message}`
        };
    }
}

async function streamQuery(query) {
    const response = await fetch(`${API_BASE_URL}/query/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: query,
            use_llm: true
        })
    });

    if (!response.ok) {
        throw new Error(`Stream request failed: ${response.statusText}`);
    }
    if (!response.body) {
        throw new Error('Streaming not supported by this browser.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalResponse = null;

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || '';

        for (const message of messages) {
            const parsed = parseSSEMessage(message);
            if (!parsed) continue;
            const { eventName, data } = parsed;
            handleStreamEvent(eventName, data);
            if (eventName === 'final_response' && data.payload?.response) {
                finalResponse = data.payload.response;
            }
        }
    }

    if (!finalResponse) {
        throw new Error('No final response received from stream.');
    }
    return finalResponse;
}

function parseSSEMessage(raw) {
    const lines = raw.split('\n');
    let eventName = 'message';
    let dataLine = '';
    for (const line of lines) {
        if (line.startsWith('event:')) {
            eventName = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
            dataLine += line.slice(5).trim();
        }
    }
    if (!dataLine) return null;
    try {
        return { eventName, data: JSON.parse(dataLine) };
    } catch (error) {
        console.error('Failed to parse SSE data:', error);
        return null;
    }
}

function handleStreamEvent(eventName, eventEnvelope) {
    const payload = eventEnvelope.payload || {};
    if (payload.trace_id) {
        activeTrace.traceId = payload.trace_id;
    }
    activeTrace.events.push({ eventName, payload, timestamp: eventEnvelope.timestamp });
    appendTimelineEvent(eventName, payload);

    if (eventName === 'routing_decision') {
        updateRouteBadge(payload.route_type || payload.agent, payload.reason || 'Routed');
        document.getElementById('indicator-agent').textContent = `Agent: ${friendlyRouteName(payload.route_type || payload.agent)}`;
        document.getElementById('indicator-action').textContent = payload.reason || 'Processing request...';
    }
    if (eventName === 'agent_started') {
        document.getElementById('processing-text').textContent = `⚙️ ${friendlyRouteName(payload.agent || 'agent')} running...`;
    }
}

function appendTimelineEvent(eventName, payload) {
    if (timelineList.querySelector('.empty-state')) {
        timelineList.innerHTML = '';
    }
    const item = document.createElement('div');
    item.className = 'timeline-item';

    const title = document.createElement('div');
    title.className = 'timeline-item-title';
    title.textContent = eventName.replace(/_/g, ' ');

    const body = document.createElement('div');
    body.className = 'timeline-item-body';
    body.textContent = summarizeEventPayload(eventName, payload);

    item.appendChild(title);
    item.appendChild(body);
    timelineList.appendChild(item);
    timelineList.scrollTop = timelineList.scrollHeight;
}

function summarizeEventPayload(eventName, payload) {
    if (eventName === 'routing_decision') {
        return `${friendlyRouteName(payload.route_type || payload.agent)} | ${payload.reason || 'route selected'}`;
    }
    if (eventName === 'chapter_resolution') {
        return `${payload.document || 'Document'} | ${payload.mode || 'resolved'} | chunks: ${payload.matched_chunks || 0}`;
    }
    if (eventName === 'retrieval_completed') {
        return `${payload.document || 'Document'} | ${payload.result_count || 0} chunks retrieved`;
    }
    if (eventName === 'summary_partial') {
        return `${payload.document || 'Document'} partial summary completed`;
    }
    if (eventName === 'error') {
        return payload.message || 'Unknown error';
    }
    if (payload.document) {
        return `${payload.document}`;
    }
    return payload.message || 'processing';
}

function formatFinalResponse(data) {
    let agentName = friendlyRouteName(data.agent);
    let message = '';
    let actionText = '';

    if (data.agent === 'general_llm') {
        actionText = 'Generated a direct LLM response';
        message = `${data.answer}`;
    } else if (['all_documents_summary', 'single_document_summary', 'chapter_summary'].includes(data.agent)) {
        actionText = data.agent === 'chapter_summary' ? 'Generated chapter-focused summaries' : 'Generated document summaries';
        message = '';
        if (Array.isArray(data.summaries)) {
            data.summaries.forEach(s => {
                const chapterLine = s.chapters ? `\n_Targets: ${s.chapters.join(', ')}_` : '';
                message += `**${s.document}:**\n${s.summary}${chapterLine}\n\n`;
            });
        }
    } else if (data.agent === 'document_retriever') {
        actionText = 'Retrieved relevant chunks and generated answer';
        message = `${data.answer}`;
    } else {
        actionText = 'Completed';
        message = data.answer || 'Completed processing.';
    }

    document.getElementById('indicator-agent').textContent = `Agent: ${agentName}`;
    document.getElementById('indicator-action').textContent = actionText;
    document.getElementById('processing-text').textContent = `✅ ${agentName}`;

    return {
        success: true,
        message,
        metadata: {
            traceId: data.trace_id,
            agent: data.agent,
            routeType: data.routing?.route_type || data.agent,
            routeReason: data.routing?.reason || '',
            routing: data.routing || {},
            events: activeTrace.events,
            results: data.results || [],
            summaries: data.summaries || []
        }
    };
}

function friendlyRouteName(routeType) {
    const map = {
        general_llm: 'General LLM',
        document_retriever: 'Document Retriever',
        all_documents_summary: 'All Documents Summarizer',
        single_document_summary: 'Single Document Summarizer',
        chapter_summary: 'Chapter Summarizer'
    };
    return map[routeType] || 'Agent';
}

function updateRouteBadge(routeType, reason) {
    if (!routeBadge) return;
    routeBadge.querySelector('.route-agent').textContent = friendlyRouteName(routeType || 'general_llm');
    routeBadge.querySelector('.route-reason').textContent = reason || 'route selected';
}

function resetTracePanels() {
    activeTrace = { traceId: null, events: [] };
    if (timelineList) {
        timelineList.innerHTML = '<p class="empty-state">Run a query to see live flow</p>';
    }
    updateRouteBadge('general_llm', 'Waiting for query');
}

async function loadHistory() {
    if (!historyList) return;
    try {
        const response = await fetch(`${API_BASE_URL}/history?limit=30`);
        if (!response.ok) {
            throw new Error(`History load failed: ${response.statusText}`);
        }
        const data = await response.json();
        renderHistory(Array.isArray(data.history) ? data.history : []);
    } catch (error) {
        console.error('History load error:', error);
        historyList.innerHTML = `<p class="empty-state">History unavailable: ${escapeHTML(error.message)}</p>`;
    }
}

function renderHistory(historyItems) {
    if (!historyList) return;
    if (!historyItems.length) {
        historyList.innerHTML = '<p class="empty-state">No history yet</p>';
        return;
    }

    historyList.innerHTML = historyItems.map(item => {
        const routeType = item.routing?.route_type || item.response?.agent || 'unknown';
        const query = escapeHTML(item.query || '');
        const routeLabel = escapeHTML(friendlyRouteName(routeType));
        const eventCount = Array.isArray(item.events) ? item.events.length : 0;
        return `
            <div class="history-item">
                <div class="history-item-route">${routeLabel}</div>
                <div>${query.slice(0, 120)}</div>
                <small>${eventCount} events</small>
            </div>
        `;
    }).join('');
}

function addMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const avatar = role === 'user' ? 'You' : 'AI';
    const formattedContent = role === 'assistant' ? markdownToHTML(content) : escapeHTML(content);

    messageDiv.innerHTML = `<div class="message-avatar">${avatar}</div><div class="message-content">${formattedContent}</div>`;

    if (role === 'assistant') {
        const contentEl = messageDiv.querySelector('.message-content');
        const metadataRow = document.createElement('div');
        metadataRow.className = 'message-meta';

        const routeType = metadata.routeType || metadata.agent;
        if (routeType) {
            metadataRow.innerHTML += `<span class="meta-chip">Agent: ${escapeHTML(friendlyRouteName(routeType))}</span>`;
        }
        if (metadata.routeReason) {
            metadataRow.innerHTML += `<span class="meta-chip">${escapeHTML(metadata.routeReason)}</span>`;
        }
        if (metadata.traceId) {
            metadataRow.innerHTML += `<span class="meta-chip">Trace: ${escapeHTML(metadata.traceId.slice(0, 8))}</span>`;
        }
        if (metadataRow.innerHTML.trim().length > 0) {
            contentEl.appendChild(metadataRow);
        }

        if (Array.isArray(metadata.results) && metadata.results.length > 0) {
            contentEl.appendChild(renderRetrievedChunks(metadata.results));
        }
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Store in history
    conversationHistory.push({ role, content, metadata });
}

function markdownToHTML(text) {
    // Simple markdown conversion
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.+<\/li>)/s, '<ul>$1</ul>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
}

function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderRetrievedChunks(results) {
    const details = document.createElement('details');
    details.className = 'retrieved-chunks';

    const summary = document.createElement('summary');
    summary.textContent = `Retrieved chunks (${results.length})`;
    details.appendChild(summary);

    const list = document.createElement('div');
    list.className = 'chunk-list';

    results.slice(0, 5).forEach((result) => {
        const item = document.createElement('div');
        item.className = 'chunk-item';
        const similarity = Math.round((result.similarity || 0) * 100);
        const preview = (result.content || '').slice(0, 260);
        item.innerHTML = `
            <div class="chunk-head">
                <span>${escapeHTML(result.document || 'Document')}</span>
                <span>${similarity}% match</span>
            </div>
            <div class="chunk-preview">${escapeHTML(preview)}${preview.length >= 260 ? '...' : ''}</div>
        `;
        list.appendChild(item);
    });

    details.appendChild(list);
    return details;
}

function setUploadBusy(isBusy) {
    isBusyUploading = isBusy;
    fileInput.disabled = isBusy;
    uploadArea.style.opacity = isBusy ? '0.6' : '1';
    uploadArea.style.pointerEvents = isBusy ? 'none' : 'auto';
    if (inputLockMessage) {
        inputLockMessage.style.display = isBusy ? 'block' : 'none';
    }
    updateInputAvailability();
}

function updateInputAvailability() {
    const disabled = isBusyUploading || isQueryInProgress;
    chatInput.disabled = disabled;
    sendBtn.disabled = disabled;
}

function closeModal() {
    document.getElementById('content-modal').style.display = 'none';
}
