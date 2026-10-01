document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');
    const chatHistory = document.getElementById('chat-history');
    const timeline = document.getElementById('timeline');
    const statusEl = document.getElementById('system-status');
    const tokenEl = document.getElementById('token-count');
    const costEl = document.getElementById('cost-value');
    
    const API_KEY = "secret-enterprise-key";

    function appendMessage(role, text) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function appendTimelineEvent(text, isDone=false) {
        const li = document.createElement('li');
        li.className = `timeline-item ${isDone ? 'done' : ''}`;
        li.textContent = text;
        timeline.appendChild(li);
    }

    async function executeQuery() {
        const query = queryInput.value.trim();
        if (!query) return;

        appendMessage('user', query);
        queryInput.value = '';
        timeline.innerHTML = '';
        statusEl.textContent = 'Executing...';
        statusEl.style.color = 'var(--accent)';

        try {
            const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-KEY': API_KEY
                },
                body: JSON.stringify({
                    question: query,
                    user_id: "tenant-1"
                })
            });

            if (!response.ok) {
                appendMessage('ai', 'Error: Unauthorized or server error.');
                statusEl.textContent = 'Error';
                statusEl.style.color = '#ef4444';
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.status) {
                                appendTimelineEvent(data.status, data.node === 'END');
                            }

                            if (data.node === 'END') {
                                statusEl.textContent = 'Complete';
                                statusEl.style.color = 'var(--success)';
                                
                                appendMessage('ai', 'Execution completed. (Check backend logs for final output).');
                                
                                let currentTokens = parseInt(tokenEl.textContent) || 0;
                                currentTokens += 1542; // Mocking token addition for UI demo
                                tokenEl.textContent = currentTokens;
                                costEl.textContent = `$${(currentTokens / 1000000 * 1.25).toFixed(4)}`;
                            }
                        } catch (e) {
                            console.error('Parse error:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error(error);
            statusEl.textContent = 'Failed';
            statusEl.style.color = '#ef4444';
        }
    }

    sendBtn.addEventListener('click', executeQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') executeQuery();
    });
});
