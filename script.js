// Configuration
const API_BASE_URL = 'http://localhost:8000/api/agents';
const MAX_RETRIES = 3;

// State
let documents = {};
let conversationHistory = [];

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const uploadArea = document.getElementById('upload-area');
const documentsList = document.getElementById('documents-list');
const clearAllBtn = document.getElementById('clear-all-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadDocuments();
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

    // Disable further selection while uploading
    fileInput.disabled = true;
    uploadArea.style.opacity = '0.5';
    uploadArea.style.pointerEvents = 'none';

    try {
        for (let file of files) {
            await uploadFile(file);
        }
    } finally {
        // Re-enable
        fileInput.disabled = false;
        uploadArea.style.opacity = '1';
        uploadArea.style.pointerEvents = 'auto';
        fileInput.value = '';  // Clear the input
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
        renderDocuments();
        chatMessages.innerHTML = '';
        addMessage('assistant', '🗑️ All documents cleared. Ready for new uploads!');
    } catch (error) {
        console.error('Clear error:', error);
        alert('Failed to clear documents');
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage('user', message);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

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

    // Add loading indicator in chat
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message assistant';
    loadingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
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
    sendBtn.disabled = false;
    chatInput.focus();
}

async function processQuery(query) {
    try {
        // Update UI to show query is being routed
        const agentProcessing = document.getElementById('agent-processing-indicator');
        const processingText = document.getElementById('processing-text');
        document.getElementById('indicator-agent').textContent = 'Agent: Query Router';
        document.getElementById('indicator-action').textContent = 'Routing to appropriate agent...';
        processingText.textContent = '🔀 Routing query...';

        // Use the new multi-agent query endpoint
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                use_llm: true
            })
        });

        const data = await response.json();

        // Handle error responses from backend
        if ('success' in data && !data.success) {
            return {
                success: false,
                message: data.answer || 'Query processing failed'
            };
        }

        if (!response.ok) {
            throw new Error(`Query failed: ${response.statusText}`);
        }

        // Update UI with actual agent being used
        let agentName = 'Unknown';
        let agentIcon = '🤖';
        let actionText = 'Processing...';
        let message = '';

        if (data.agent === 'general_llm') {
            agentName = 'General LLM';
            agentIcon = '💬';
            actionText = 'Generating response...';
            message = `💬 General Answer:\n\n${data.answer}`;
        } else if (data.agent === 'summarizer') {
            agentName = 'Summarizer';
            agentIcon = '📋';
            actionText = 'Generating summaries...';
            message = '📋 **Document Summary:**\n\n';
            if (data.summaries && Array.isArray(data.summaries)) {
                data.summaries.forEach(s => {
                    message += `**${s.document}:**\n${s.summary}\n\n`;
                });
            }
        } else if (data.agent === 'document_retriever') {
            agentName = 'Document Retriever';
            agentIcon = '🔍';
            actionText = 'Searching documents...';
            message = `${data.answer}\n\n`;
            if (data.results && data.results.length > 0) {
                message += '📚 **Sources:**\n';
                data.results.forEach(r => {
                    const relevance = Math.round(r.similarity * 100);
                    message += `- ${r.document} (${relevance}% match)\n`;
                });
            }
        }

        // Update UI with agent info
        document.getElementById('indicator-agent').textContent = `Agent: ${agentName}`;
        document.getElementById('indicator-action').textContent = actionText;
        document.getElementById('processing-text').innerHTML = `${agentIcon} ${agentName}`;

        return {
            success: true,
            message: message,
            metadata: {
                agent: data.agent,
                agentName: agentName,
                results: data.results || []
            }
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            success: false,
            message: `❌ Error: ${error.message}`
        };
    }
}

async function checkQueryRelevance(query) {
    // Handled by backend now
    return { isRelevant: true, confidence: 0.8 };
}

async function determineQueryType(query) {
    // Handled by backend now
    return { isSummarization: false, targetDocument: null };
}

async function summarizeDocuments(collectionName = null) {
    // Handled by backend now
    return { success: false, message: 'Summarization handled by backend' };
}

async function searchDocuments(query) {
    // Handled by backend now
    return { success: false, message: 'Search handled by backend' };
}

async function askGeneralLLM(query) {
    // Handled by backend
    return { success: false, message: 'LLM queries handled by backend' };
}

async function generateSummary(context, docName) {
    // Handled by backend
    return '';
}

async function generateAnswer(query, context) {
    // Handled by backend
    return '';
}

function addMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    const formattedContent = role === 'assistant' ? markdownToHTML(content) : escapeHTML(content);

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${formattedContent}</div>
    `;

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

function closeModal() {
    document.getElementById('content-modal').style.display = 'none';
}
