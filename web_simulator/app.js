/**
 * Aetheris Omni-Agent Client Application
 * Amazon Developer Hackathon 2026: Alexa+, Ring, Bee, Fire TV, AWS Bedrock
 */

// Global State
let currentFilter = 'ALL';
let isRecording = false;
let recognition = null;
let protocolLogs = [];

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initSpeechRecognition();
    initEventStream();
    refreshSystemState();
    fetchProtocolLogs();
    setInterval(fetchProtocolLogs, 2500);
});

// =====================================================================
// SPEECH RECOGNITION & SYNTHESIS (ALEXA+ VOICE INTERACTION)
// =====================================================================

function initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
        recognition = new SpeechRec();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isRecording = true;
            document.getElementById('btn-mic').classList.add('recording');
            document.getElementById('agent-status-tag').textContent = 'LISTENING TO SPEECH...';
            document.getElementById('waveform').classList.add('active');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('user-input').value = transcript;
            handleUserQuery(transcript);
        };

        recognition.onerror = (event) => {
            console.warn('Speech recognition error:', event.error);
            stopVoiceRecording();
        };

        recognition.onend = () => {
            stopVoiceRecording();
        };
    } else {
        console.warn('Web Speech API not supported in this browser. Falling back to text-only mode.');
    }
}

function toggleVoiceRecording() {
    if (!recognition) {
        alert('Voice recognition is supported in Chromium browsers (Chrome, Edge, Brave). You can type your request directly!');
        return;
    }
    if (isRecording) {
        recognition.stop();
        stopVoiceRecording();
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.error(e);
        }
    }
}

function stopVoiceRecording() {
    isRecording = false;
    document.getElementById('btn-mic').classList.remove('recording');
    document.getElementById('agent-status-tag').textContent = 'READY & LISTENING';
    document.getElementById('waveform').classList.remove('active');
}

function speakAlexaResponse(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop prior audio
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;
        
        // Find natural English voice
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.lang.includes('en') && (v.name.includes('Samantha') || v.name.includes('Natural') || v.name.includes('Zira') || v.name.includes('Google')));
        if (preferred) utterance.voice = preferred;

        utterance.onstart = () => {
            document.getElementById('waveform').classList.add('active');
            document.getElementById('agent-status-tag').textContent = 'ALEXA+ SPEAKING';
        };
        utterance.onend = () => {
            document.getElementById('waveform').classList.remove('active');
            document.getElementById('agent-status-tag').textContent = 'READY & LISTENING';
        };

        window.speechSynthesis.speak(utterance);
    }
}

// =====================================================================
// SERVER-SENT EVENTS (SSE) REAL-TIME TELEMETRY STREAM
// =====================================================================

function initEventStream() {
    const evtSource = new EventSource('/api/events');

    evtSource.onmessage = (e) => {
        try {
            const eventData = JSON.parse(e.data);
            handleIncomingLiveEvent(eventData);
        } catch (err) {
            console.error('SSE parse error:', err);
        }
    };

    evtSource.onerror = () => {
        // Automatically reconnects
    };
}

function handleIncomingLiveEvent(event) {
    console.log('Live Event received:', event);
    if (event.event === 'scenario_update' || event.event === 'agent_response') {
        refreshSystemState();
        fetchProtocolLogs();
    }
}

// =====================================================================
// CHAT & AGENT ORCHESTRATION
// =====================================================================

async function handleUserSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    await handleUserQuery(text);
}

async function handleUserQuery(text) {
    appendUserMessage(text);
    
    // Set UI to reasoning mode
    document.getElementById('agent-status-tag').textContent = 'ORCHESTRATING MCP TOOLS...';
    document.getElementById('waveform').classList.add('active');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await response.json();
        
        appendAgentResponse(data);
        speakAlexaResponse(data.spoken_text);
        refreshSystemState();
        fetchProtocolLogs();
    } catch (err) {
        console.error('Chat error:', err);
        appendAgentResponse({
            spoken_text: 'Encountered a communication issue with the local MCP server. Please ensure python -m mcp_server.server is running.',
            tool_calls: [],
            cards: []
        });
    } finally {
        document.getElementById('agent-status-tag').textContent = 'READY & LISTENING';
    }
}

function appendUserMessage(text) {
    const feed = document.getElementById('conversation-feed');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const msgHtml = `
        <div class="chat-message user-msg">
            <div class="message-meta">
                <span class="sender-name">You (Voice / Touch)</span>
                <span class="avatar user-avatar">U</span>
                <span class="msg-time">${time}</span>
            </div>
            <div class="message-bubble">
                <p>${escapeHtml(text)}</p>
            </div>
        </div>
    `;
    feed.insertAdjacentHTML('beforeend', msgHtml);
    feed.scrollTop = feed.scrollHeight;
}

function appendAgentResponse(data) {
    const feed = document.getElementById('conversation-feed');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Render tool pills
    let toolsHtml = '';
    if (data.tool_calls && data.tool_calls.length > 0) {
        toolsHtml = '<div class="tool-pill-group">';
        data.tool_calls.forEach(tc => {
            toolsHtml += `<span class="tool-badge">${tc.tool}</span>`;
        });
        toolsHtml += '</div>';
    }

    // Render dynamic MCP Cards
    let cardsHtml = '';
    if (data.cards && data.cards.length > 0) {
        data.cards.forEach(card => {
            if (card.type === 'procurement_receipt') {
                cardsHtml += `
                    <div class="mcp-card">
                        <div class="mcp-card-header">
                            <span class="mcp-card-title">📦 ${card.title}</span>
                            <span class="mcp-card-status">PRIME CONFIRMED</span>
                        </div>
                        <div class="mcp-card-body">
                            <div class="mcp-item-row"><span>Item:</span><strong>${card.item}</strong></div>
                            <div class="mcp-item-row"><span>Quantity:</span><strong>${card.quantity || 2}</strong></div>
                            <div class="mcp-item-row"><span>Total Charged:</span><strong>${card.total || '$57.00'}</strong></div>
                            <div class="mcp-item-row"><span>Estimated Arrival:</span><strong>${card.delivery || 'Same-Day Prime'}</strong></div>
                        </div>
                    </div>
                `;
            } else if (card.type === 'schedule_card') {
                cardsHtml += `
                    <div class="mcp-card">
                        <div class="mcp-card-header">
                            <span class="mcp-card-title">📅 ${card.title}</span>
                            <span class="mcp-card-status">${card.status}</span>
                        </div>
                        <div class="mcp-card-body">
                            ${card.details.map(d => `<div class="mcp-item-row"><span>• ${d}</span></div>`).join('')}
                        </div>
                    </div>
                `;
            } else if (card.type === 'ring_card') {
                cardsHtml += `
                    <div class="mcp-card">
                        <div class="mcp-card-header">
                            <span class="mcp-card-title">🔔 ${card.title}</span>
                            <span class="mcp-card-status">${card.deadbolt_status}</span>
                        </div>
                        <div class="mcp-card-body">
                            <div class="mcp-item-row"><span>Porch Event:</span><strong>${card.event}</strong></div>
                            <div class="mcp-item-row"><span>Live Stream:</span><strong>${card.live_stream}</strong></div>
                        </div>
                    </div>
                `;
            } else if (card.type === 'bee_telemetry_card') {
                cardsHtml += `
                    <div class="mcp-card">
                        <div class="mcp-card-header">
                            <span class="mcp-card-title">🐝 ${card.title}</span>
                            <span class="mcp-card-status">COGNITIVE LOAD ${card.stress_index}</span>
                        </div>
                        <div class="mcp-card-body">
                            <div class="mcp-item-row"><span>Resting Heart Rate:</span><strong>${card.heart_rate}</strong></div>
                            <div class="mcp-item-row"><span>Haptic Recommendation:</span><strong>${card.wrist_coaching}</strong></div>
                        </div>
                    </div>
                `;
            }
        });
    }

    const msgHtml = `
        <div class="chat-message agent-msg">
            <div class="message-meta">
                <span class="avatar alexa-avatar">A+</span>
                <span class="sender-name">Alexa+ Omni-Agent</span>
                <span class="msg-time">${time}</span>
            </div>
            <div class="message-bubble">
                <p>${escapeHtml(data.spoken_text)}</p>
                ${toolsHtml}
                ${cardsHtml}
            </div>
        </div>
    `;
    feed.insertAdjacentHTML('beforeend', msgHtml);
    feed.scrollTop = feed.scrollHeight;
}

// =====================================================================
// QUICK DEMO SCENARIOS FOR JUDGES
// =====================================================================

async function triggerScenario(scenarioName) {
    const titles = {
        'resolve_calendar_conflict': 'Alexa, check my schedule and resolve any double-bookings.',
        'courier_delivery_restock': 'Amazon Courier detected at front door. Reorder depleted supplies.',
        'bee_stress_focus_ambience': 'Bee Wearable reports elevated cognitive stress. Engage focus ambience.'
    };
    const query = titles[scenarioName] || scenarioName;
    await handleUserQuery(query);
}

async function triggerSymphony() {
    await handleUserQuery('Alexa, run the full Aetheris Cross-Device Autonomous Symphony.');
}

// =====================================================================
// DEVICE INTERACTION & CONTROLS
// =====================================================================

async function toggleSmartDeadbolt() {
    const btn = document.getElementById('btn-toggle-deadbolt');
    btn.textContent = 'Unlocking 60s...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/device/ring_doorbell/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'toggle_lock' })
        });
        const data = await res.json();
        
        document.getElementById('ring-lock-status').textContent = 'UNLOCKED (PASS)';
        document.getElementById('ring-lock-status').className = 'device-status-badge warning';
        document.getElementById('ring-cam-image').src = '/static/door_unlocked.jpg';
        
        setTimeout(() => {
            document.getElementById('ring-lock-status').textContent = 'LOCKED';
            document.getElementById('ring-lock-status').className = 'device-status-badge active';
            document.getElementById('ring-cam-image').src = '/static/clear_porch.jpg';
            btn.textContent = 'Disengage 60s';
            btn.disabled = false;
        }, 5000); // 5-second accelerated simulation for demo
    } catch (e) {
        console.error(e);
        btn.textContent = 'Disengage 60s';
        btn.disabled = false;
    }
}

async function setAmbience(preset) {
    document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    await handleUserQuery(`Set workspace ambience to ${preset.replace('_', ' ')}.`);
}

async function reorderItem(itemName) {
    await handleUserQuery(`Alexa, auto procure ${itemName.replace('_', ' ')} via Amazon 1-Click.`);
}

// =====================================================================
// SYSTEM STATE REFRESH & TELEMETRY SYNC
// =====================================================================

async function refreshSystemState() {
    try {
        const res = await fetch('/api/state');
        const state = await res.json();

        // 1. Ring
        if (state.ring_events && state.ring_events.length > 0) {
            const latest = state.ring_events[0];
            document.getElementById('ring-event-text').textContent = `Latest: ${latest.detected_object || 'Porch Monitored'}`;
        }

        // 2. Bee Wearable
        if (state.bee_telemetry && state.bee_telemetry.length > 0) {
            const latestBee = state.bee_telemetry[0];
            document.getElementById('bee-hr').innerHTML = `${latestBee.heart_rate} <small>BPM</small>`;
            document.getElementById('bee-stress').innerHTML = `${latestBee.stress_level}<small>%</small>`;
            document.getElementById('stress-bar-fill').style.width = `${latestBee.stress_level}%`;
            document.getElementById('bee-memo-text').textContent = `"${latestBee.ambient_memo}"`;
            document.getElementById('bee-coach-pill').innerHTML = `💡 <strong>Wrist Coach:</strong> ${latestBee.coaching_tip}`;
        }

        // 3. Fire TV Canvas
        if (state.firetv_canvas && state.firetv_canvas.length > 0) {
            const latestCanvas = state.firetv_canvas[0];
            document.getElementById('canvas-headline').textContent = latestCanvas.headline;
            document.getElementById('canvas-body').textContent = latestCanvas.body;
        }

        // 4. Inventory
        if (state.inventory && state.inventory.length > 0) {
            const tbody = document.getElementById('inventory-tbody');
            tbody.innerHTML = '';
            let shortages = 0;

            state.inventory.forEach(item => {
                const isShort = item.stock <= item.reorder_threshold;
                if (isShort) shortages++;
                const pillClass = item.stock === 0 ? 'out' : (isShort ? 'low' : 'ok');
                
                const tr = `
                    <tr>
                        <td>${item.display_name}</td>
                        <td><span class="stock-pill ${pillClass}">${item.stock} in stock</span></td>
                        <td>$${item.unit_price.toFixed(2)}</td>
                        <td><button class="btn-table-order" onclick="reorderItem('${item.item_name}')">1-Click Buy</button></td>
                    </tr>
                `;
                tbody.insertAdjacentHTML('beforeend', tr);
            });

            document.getElementById('inv-badge').textContent = `${shortages} SHORTAGE${shortages === 1 ? '' : 'S'}`;
            document.getElementById('inv-badge').className = shortages > 0 ? 'device-status-badge warning' : 'device-status-badge active';
        }

        // Recent Orders
        if (state.recent_orders && state.recent_orders.length > 0) {
            const orderFeed = document.getElementById('recent-orders-feed');
            orderFeed.innerHTML = '';
            state.recent_orders.slice(0, 2).forEach(ord => {
                orderFeed.insertAdjacentHTML('beforeend', `
                    <div class="order-mini-chip">
                        <span>📦 <strong>${ord.order_id}:</strong> ${ord.item_name} (Qty ${ord.quantity}) • ${ord.delivery_estimate}</span>
                    </div>
                `);
            });
        }
    } catch (e) {
        console.error('Error refreshing state:', e);
    }
}

// =====================================================================
// REAL-TIME MCP PROTOCOL INSPECTOR
// =====================================================================

function toggleInspector() {
    const drawer = document.getElementById('inspector-drawer');
    drawer.classList.toggle('open');
}

async function fetchProtocolLogs() {
    try {
        const res = await fetch('/api/mcp-logs');
        protocolLogs = await res.json();
        document.getElementById('protocol-counter').textContent = `${protocolLogs.length} packets`;
        renderLogs();
    } catch (e) {
        // quiet
    }
}

function filterLogs(tab) {
    currentFilter = tab;
    document.querySelectorAll('.filter-tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderLogs();
}

function clearProtocolLogs() {
    protocolLogs = [];
    document.getElementById('inspector-logs').innerHTML = '';
    document.getElementById('protocol-counter').textContent = '0 packets';
}

function renderLogs() {
    const container = document.getElementById('inspector-logs');
    container.innerHTML = '';

    const filtered = protocolLogs.filter(entry => {
        if (currentFilter === 'ALL') return true;
        return entry.direction === currentFilter;
    });

    filtered.forEach(log => {
        const dirClass = log.direction.toLowerCase();
        const payloadStr = typeof log.payload === 'string' ? log.payload : JSON.stringify(log.payload);

        const html = `
            <div class="log-entry">
                <span class="log-time">[${log.timestamp}]</span>
                <span class="log-dir ${dirClass}">${log.direction}</span>
                <span class="log-method">${log.method}</span>
                <span class="log-preview" title="${escapeHtml(payloadStr)}">${escapeHtml(payloadStr)}</span>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });

    container.scrollTop = container.scrollHeight;
}

function escapeHtml(string) {
    const div = document.createElement('div');
    div.innerText = string;
    return div.innerHTML;
}
