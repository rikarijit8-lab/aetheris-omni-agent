/**
 * Aetheris Omni-Agent: Clean Executive Client Controller
 * Amazon Developer Hackathon 2026: Alexa+, Ring, Bee, Fire TV, AWS Bedrock
 */

// Global State
let activeTab = 'calendar';
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
// CLEAN TAB CONTROLLER (RING, BEE, FIRE TV, SUPPLIES, GRID)
// =====================================================================

function switchDeviceTab(tabKey) {
    activeTab = tabKey;

    // Update Tab Navigation Active State
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    const targetTabBtn = document.getElementById(`tab-${tabKey}`);
    if (targetTabBtn) targetTabBtn.classList.add('active');

    // Update Panel Visibility
    document.querySelectorAll('.device-panel').forEach(p => p.classList.remove('active'));
    const targetPanel = document.getElementById(`panel-${tabKey}`);
    if (targetPanel) targetPanel.classList.add('active');
}

// =====================================================================
// SPEECH RECOGNITION & ALEXA+ VOICE SYNTHESIS
// =====================================================================

function createSpeechRecognizer() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return null;

    const rec = new SpeechRec();
    rec.continuous = false;
    rec.interimResults = true; // Show live interim words as user speaks
    rec.lang = 'en-US';

    rec.onstart = () => {
        isRecording = true;
        document.getElementById('btn-mic').classList.add('recording');
        document.getElementById('alexa-orb').classList.add('recording');
        document.getElementById('agent-status-badge').textContent = 'Listening... Speak now!';
        document.getElementById('user-input').placeholder = 'Listening to your voice... Speak now!';
        document.getElementById('waveform').classList.add('active');
    };

    rec.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        const currentText = finalTranscript || interimTranscript;
        if (currentText) {
            document.getElementById('user-input').value = currentText;
        }

        if (finalTranscript) {
            handleUserQuery(finalTranscript);
        }
    };

    rec.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        const badge = document.getElementById('agent-status-badge');
        if (event.error === 'not-allowed') {
            alert('Microphone access was blocked! Please click the camera/mic icon or lock icon in your browser address bar and select "Allow" for microphone.');
            if (badge) badge.textContent = 'Mic Blocked (Allow in Address Bar)';
        } else if (event.error === 'no-speech') {
            if (badge) badge.textContent = 'No voice detected. Click mic to try again.';
        } else {
            if (badge) badge.textContent = `Mic Error: ${event.error}`;
        }
        stopVoiceRecording();
    };

    rec.onend = () => {
        stopVoiceRecording();
    };

    return rec;
}

function initSpeechRecognition() {
    recognition = createSpeechRecognizer();
    if (!recognition) {
        console.warn('Web Speech Recognition API not natively supported in this browser. Text input remains active.');
    }
}

function toggleVoiceRecording() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        alert('Voice speech recognition requires a Chromium browser (Chrome, Edge, Brave). You can type directly in the text composer below!');
        return;
    }

    if (isRecording) {
        if (recognition) {
            try { recognition.stop(); } catch (e) {}
        }
        stopVoiceRecording();
    } else {
        // Create fresh recognizer on click to guarantee clean state
        try {
            recognition = createSpeechRecognizer();
            if (recognition) {
                recognition.start();
            }
        } catch (e) {
            console.error('Error starting speech recognition:', e);
            stopVoiceRecording();
        }
    }
}

function stopVoiceRecording() {
    isRecording = false;
    const btn = document.getElementById('btn-mic');
    if (btn) btn.classList.remove('recording');
    const orb = document.getElementById('alexa-orb');
    if (orb) orb.classList.remove('recording');
    const input = document.getElementById('user-input');
    if (input) input.placeholder = "Ask Alexa+, e.g. 'Coffee is low and the courier is at the Ring door...'";
    const badge = document.getElementById('agent-status-badge');
    if (badge && !badge.textContent.includes('Speaking') && !badge.textContent.includes('Reasoning')) {
        badge.textContent = 'Ready • Listening';
    }
    const wave = document.getElementById('waveform');
    if (wave && (!badge || !badge.textContent.includes('Speaking'))) {
        wave.classList.remove('active');
    }
}

function speakAlexaResponse(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.lang.includes('en') && (v.name.includes('Samantha') || v.name.includes('Natural') || v.name.includes('Zira') || v.name.includes('Google')));
        if (preferred) utterance.voice = preferred;

        utterance.onstart = () => {
            document.getElementById('waveform').classList.add('active');
            document.getElementById('agent-status-badge').textContent = 'Alexa+ Speaking';
        };
        utterance.onend = () => {
            document.getElementById('waveform').classList.remove('active');
            document.getElementById('agent-status-badge').textContent = 'Ready • Listening';
        };

        window.speechSynthesis.speak(utterance);
    }
}

// =====================================================================
// SERVER-SENT EVENTS (SSE) STREAM
// =====================================================================

function initEventStream() {
    const evtSource = new EventSource('/api/events');
    evtSource.onmessage = (e) => {
        try {
            const eventData = JSON.parse(e.data);
            if (eventData.event === 'scenario_update' || eventData.event === 'agent_response') {
                refreshSystemState();
                fetchProtocolLogs();
            }
        } catch (err) {
            console.error(err);
        }
    };
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

    document.getElementById('agent-status-badge').textContent = 'Reasoning over MCP Tools...';
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

        // Auto-switch tab based on content
        const lower = text.toLowerCase();
        if (lower.includes('calendar') || lower.includes('schedule') || lower.includes('meeting') || lower.includes('conflict')) {
            switchDeviceTab('calendar');
        } else if (lower.includes('ring') || lower.includes('door') || lower.includes('courier')) {
            switchDeviceTab('ring');
        } else if (lower.includes('bee') || lower.includes('stress') || lower.includes('biometric')) {
            switchDeviceTab('bee');
        } else if (lower.includes('firetv') || lower.includes('tv') || lower.includes('ambience')) {
            switchDeviceTab('firetv');
        } else if (lower.includes('coffee') || lower.includes('paper') || lower.includes('order') || lower.includes('buy') || lower.includes('procure')) {
            switchDeviceTab('procure');
        }

        refreshSystemState();
        fetchProtocolLogs();
    } catch (err) {
        console.error('Chat error:', err);
        appendAgentResponse({
            spoken_text: 'Communication established with local MCP server.',
            tool_calls: [],
            cards: []
        });
    } finally {
        document.getElementById('agent-status-badge').textContent = 'Ready • Listening';
    }
}

function appendUserMessage(text) {
    const feed = document.getElementById('conversation-feed');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const html = `
        <div class="message-card user">
            <div class="card-meta">
                <span class="time-stamp">${time}</span>
                <div class="author-pill">
                    <span>You</span>
                    <span class="author-icon" style="background: #475569;">U</span>
                </div>
            </div>
            <div class="card-content">
                <p>${escapeHtml(text)}</p>
            </div>
        </div>
    `;
    feed.insertAdjacentHTML('beforeend', html);
    feed.scrollTop = feed.scrollHeight;
}

function appendAgentResponse(data) {
    const feed = document.getElementById('conversation-feed');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Render tool badges
    let toolsHtml = '';
    if (data.tool_calls && data.tool_calls.length > 0) {
        toolsHtml = '<div class="tools-badge-list">';
        data.tool_calls.forEach(tc => {
            toolsHtml += `<span class="tool-tag">${tc.tool}</span>`;
        });
        toolsHtml += '</div>';
    }

    // Render dynamic MCP Cards
    let cardsHtml = '';
    if (data.cards && data.cards.length > 0) {
        data.cards.forEach(card => {
            if (card.type === 'procurement_receipt') {
                cardsHtml += `
                    <div class="mcp-ui-card">
                        <div class="mcp-ui-header">
                            <span class="mcp-ui-title">📦 ${card.title}</span>
                            <span class="mcp-ui-tag">PRIME CONFIRMED</span>
                        </div>
                        <div class="mcp-ui-row"><span>Item:</span><strong>${card.item}</strong></div>
                        <div class="mcp-ui-row"><span>Quantity:</span><strong>${card.quantity || 2}</strong></div>
                        <div class="mcp-ui-row"><span>Total:</span><strong>${card.total || '$57.00'}</strong></div>
                        <div class="mcp-ui-row"><span>Delivery:</span><strong>${card.delivery || 'Same-Day Prime'}</strong></div>
                    </div>
                `;
            } else if (card.type === 'schedule_card') {
                cardsHtml += `
                    <div class="mcp-ui-card">
                        <div class="mcp-ui-header">
                            <span class="mcp-ui-title">📅 ${card.title}</span>
                            <span class="mcp-ui-tag">${card.status}</span>
                        </div>
                        ${card.details.map(d => `<div class="mcp-ui-row"><span>• ${d}</span></div>`).join('')}
                    </div>
                `;
            } else if (card.type === 'ring_card') {
                cardsHtml += `
                    <div class="mcp-ui-card">
                        <div class="mcp-ui-header">
                            <span class="mcp-ui-title">🔔 ${card.title}</span>
                            <span class="mcp-ui-tag">${card.deadbolt_status}</span>
                        </div>
                        <div class="mcp-ui-row"><span>Event:</span><strong>${card.event}</strong></div>
                        <div class="mcp-ui-row"><span>Stream:</span><strong>${card.live_stream}</strong></div>
                    </div>
                `;
            } else if (card.type === 'bee_telemetry_card') {
                cardsHtml += `
                    <div class="mcp-ui-card">
                        <div class="mcp-ui-header">
                            <span class="mcp-ui-title">🐝 ${card.title}</span>
                            <span class="mcp-ui-tag">STRESS ${card.stress_index}</span>
                        </div>
                        <div class="mcp-ui-row"><span>Heart Rate:</span><strong>${card.heart_rate}</strong></div>
                        <div class="mcp-ui-row"><span>Coaching:</span><strong>${card.wrist_coaching}</strong></div>
                    </div>
                `;
            }
        });
    }

    const html = `
        <div class="message-card agent">
            <div class="card-meta">
                <div class="author-pill">
                    <span class="author-icon">A+</span>
                    <span>Alexa+ Agent</span>
                </div>
                <span class="time-stamp">${time}</span>
            </div>
            <div class="card-content">
                <p>${escapeHtml(data.spoken_text)}</p>
                ${toolsHtml}
                ${cardsHtml}
            </div>
        </div>
    `;
    feed.insertAdjacentHTML('beforeend', html);
    feed.scrollTop = feed.scrollHeight;
}

// =====================================================================
// QUICK DEMO SCENARIOS
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
// DEVICE ACTIONS & CONTROLS
// =====================================================================

async function toggleSmartDeadbolt() {
    const btn = document.getElementById('btn-toggle-deadbolt');
    btn.textContent = 'Unlocking 60s...';
    btn.disabled = true;

    try {
        await fetch('/api/device/ring_doorbell/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'toggle_lock' })
        });

        document.getElementById('ring-lock-status').textContent = 'UNLOCKED • 60S PASS';
        document.getElementById('ring-lock-status').className = 'lock-indicator unlocked';
        document.getElementById('ring-cam-image').src = '/static/door_unlocked.jpg';

        setTimeout(() => {
            document.getElementById('ring-lock-status').textContent = 'LOCKED • SECURE';
            document.getElementById('ring-lock-status').className = 'lock-indicator locked';
            document.getElementById('ring-cam-image').src = '/static/clear_porch.jpg';
            btn.textContent = 'Disengage Lock 60s';
            btn.disabled = false;
        }, 5000);
    } catch (e) {
        console.error(e);
        btn.textContent = 'Disengage Lock 60s';
        btn.disabled = false;
    }
}

async function setAmbience(preset) {
    document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    await handleUserQuery(`Set workspace ambience to ${preset.replace('_', ' ')}.`);
}

async function reorderItem(itemName) {
    await handleUserQuery(`Alexa, auto procure ${itemName.replace('_', ' ')} via Amazon 1-Click.`);
}

// =====================================================================
// SYSTEM STATE REFRESH
// =====================================================================

async function refreshSystemState() {
    try {
        const res = await fetch('/api/state');
        const state = await res.json();

        // 0. Calendar & Schedule Timeline
        if (state.schedule && state.schedule.length > 0) {
            const timeline = document.getElementById('calendar-timeline');
            if (timeline) {
                timeline.innerHTML = '';
                state.schedule.forEach(event => {
                    const isCollision = event.id === 2 && event.start_time.startsWith('13:30');
                    const isRescheduled = event.id === 2 && event.start_time.startsWith('14:00');
                    const cardClass = isCollision ? 'conflict' : (isRescheduled ? 'rescheduled' : '');
                    const tagStatus = isCollision ? '<span class="event-tag-status conflict">Time Collision</span>' : 
                                     (isRescheduled ? '<span class="event-tag-status rescheduled">Auto-Rescheduled</span>' : 
                                     '<span class="event-tag-status confirmed">Confirmed</span>');

                    const itemHtml = `
                        <div class="timeline-event-card ${cardClass}">
                            <div class="event-left">
                                <div class="event-time-badge">
                                    <span class="time-text">${event.start_time} - ${event.end_time}</span>
                                </div>
                                <div class="event-details">
                                    <h4 class="event-title">${event.title}</h4>
                                    <div class="event-sub">
                                        <span>📍 ${event.location || 'Executive Studio'}</span>
                                        <span>👥 ${event.participants || 'Team'}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="event-right">
                                ${tagStatus}
                            </div>
                        </div>
                    `;
                    timeline.insertAdjacentHTML('beforeend', itemHtml);
                });

                const hasCollision = state.schedule.some(e => e.id === 2 && e.start_time.startsWith('13:30'));
                const summaryEl = document.getElementById('schedule-conflict-summary');
                const pillEl = document.getElementById('schedule-status-pill');
                if (summaryEl) {
                    summaryEl.textContent = hasCollision ? 
                        "Collision: Operations Sync overlaps Keynote at 1:30 PM." : 
                        "All schedules optimized. Operations Sync shifted to 2:00 PM.";
                }
                if (pillEl) {
                    pillEl.textContent = hasCollision ? "Conflict Flagged" : "3 Sessions • Conflict Solved";
                    pillEl.className = hasCollision ? "schedule-status-pill warning" : "schedule-status-pill";
                }
                const gridCal = document.getElementById('grid-calendar-text');
                if (gridCal) {
                    gridCal.textContent = hasCollision ? "1 Collision Flagged" : "3 Sessions • Collisions Solved";
                }
            }
        }

        // 1. Ring
        if (state.ring_events && state.ring_events.length > 0) {
            const latest = state.ring_events[0];
            document.getElementById('ring-event-text').textContent = latest.detected_object || 'Front porch secure';
            document.getElementById('grid-ring-text').textContent = latest.detected_object || 'Front porch monitored';
        }

        // 2. Bee
        if (state.bee_telemetry && state.bee_telemetry.length > 0) {
            const latestBee = state.bee_telemetry[0];
            document.getElementById('bee-hr').innerHTML = `${latestBee.heart_rate} <small>BPM</small>`;
            document.getElementById('bee-stress').innerHTML = `${latestBee.stress_level}<small>%</small>`;
            document.getElementById('stress-bar-fill').style.width = `${latestBee.stress_level}%`;
            document.getElementById('bee-memo-text').textContent = `"${latestBee.ambient_memo}"`;
            document.getElementById('bee-coach-pill').innerHTML = `💡 <strong>Wrist Coach:</strong> ${latestBee.coaching_tip}`;
            document.getElementById('grid-bee-text').textContent = `HR: ${latestBee.heart_rate} BPM • Stress: ${latestBee.stress_level}%`;
        }

        // 3. Fire TV
        if (state.firetv_canvas && state.firetv_canvas.length > 0) {
            const latestCanvas = state.firetv_canvas[0];
            document.getElementById('canvas-headline').textContent = latestCanvas.headline;
            document.getElementById('canvas-body').textContent = latestCanvas.body;
            document.getElementById('grid-firetv-text').textContent = latestCanvas.headline;
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
                        <td><strong>${item.display_name}</strong></td>
                        <td><span class="stock-tag ${pillClass}">${item.stock} in stock</span></td>
                        <td>$${item.unit_price.toFixed(2)}</td>
                        <td><button class="btn-buy" onclick="reorderItem('${item.item_name}')">1-Click Buy</button></td>
                    </tr>
                `;
                tbody.insertAdjacentHTML('beforeend', tr);
            });

            document.getElementById('inv-badge').textContent = `${shortages} Shortage${shortages === 1 ? '' : 's'}`;
            document.getElementById('grid-procure-text').textContent = `${shortages} item shortages flagged`;
        }

        // Recent Orders
        if (state.recent_orders && state.recent_orders.length > 0) {
            const orderFeed = document.getElementById('recent-orders-feed');
            orderFeed.innerHTML = '';
            state.recent_orders.slice(0, 1).forEach(ord => {
                orderFeed.insertAdjacentHTML('beforeend', `
                    <div class="order-chip">
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
// PROTOCOL INSPECTOR
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
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
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
            <div class="log-line">
                <span class="time">[${log.timestamp}]</span>
                <span class="direction ${dirClass}">${log.direction}</span>
                <span class="method">${log.method}</span>
                <span class="payload" title="${escapeHtml(payloadStr)}">${escapeHtml(payloadStr)}</span>
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
