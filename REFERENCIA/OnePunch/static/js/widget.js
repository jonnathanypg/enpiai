/**
 * OnePunch AI Chat Widget
 * Embed this on your website to enable AI chat support.
 */
(function () {
    // 1. Get Config from Script Tag
    let myScript = document.currentScript;
    if (!myScript) {
        // Fallback for async/deferred loading
        const scripts = document.getElementsByTagName('script');
        for (let i = 0; i < scripts.length; i++) {
            if (scripts[i].src && (scripts[i].src.includes('widget.js') || scripts[i].src.includes('id='))) {
                myScript = scripts[i];
                if (myScript.src.includes('id=')) break; // found the specific one
            }
        }
    }

    console.log("OnePunch Widget: Script found", myScript);

    let WIDGET_ID = null;
    let API_URL = null;

    if (myScript) {
        try {
            const urlObj = new URL(myScript.src);
            WIDGET_ID = urlObj.searchParams.get('id');
            API_URL = urlObj.origin;
            console.log("OnePunch Widget: Configured", { WIDGET_ID, API_URL });
        } catch (e) {
            console.error("OnePunch Widget Error: Could not parse script URL", e);
        }
    }

    if (!WIDGET_ID) {
        console.warn('OnePunch Widget: ID missing. Add ?id=YOUR_ID to script src. Chat disabled.');
        return;
    }

    // Styles
    const STYLES = `
        #onepunch-widget-container {
            bottom: 20px; right: 20px; z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            position: fixed;
            pointer-events: none; /* Layout container passes clicks */
        }
        #onepunch-widget-btn, #onepunch-window {
            pointer-events: auto; /* Enable clicks on elements */
        }
        #onepunch-widget-btn {
            width: 60px; height: 60px; border-radius: 30px;
            background: #000; border: none; cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex; align-items: center; justify-content: center;
            transition: transform 0.2s;
            pointer-events: auto; /* Button catches clicks */
        }
        #onepunch-widget-btn:hover { transform: scale(1.05); }
        #onepunch-window {
            position: absolute; bottom: 80px; right: 0;
            width: 350px; height: 500px;
            background: white; border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            display: none; flex-direction: column; overflow: hidden;
            border: 1px solid #eee; opacity: 0; transition: opacity 0.2s;
            pointer-events: auto; /* Window catches clicks */
        }
        #onepunch-window.open { display: flex; opacity: 1; }
        .op-msg {
            max-width: 80%; padding: 8px 12px; border-radius: 12px;
            font-size: 14px; line-height: 1.4; margin-bottom: 8px; word-wrap: break-word;
        }
        .op-msg-user {
            align-self: flex-end; background: #000; color: #fff;
            border-bottom-right-radius: 4px;
        }
        .op-msg-bot {
            align-self: flex-start; background: #f1f3f5; color: #000;
            border-bottom-left-radius: 4px;
        }
    `;

    const styleEl = document.createElement('style');
    styleEl.innerHTML = STYLES;
    document.head.appendChild(styleEl);

    // Container
    const container = document.createElement('div');
    container.id = 'onepunch-widget-container';
    document.body.appendChild(container);

    // Button
    const btn = document.createElement('button');
    btn.id = 'onepunch-widget-btn';
    btn.innerHTML = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;
    container.appendChild(btn);

    // Chat Window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'onepunch-window';
    container.appendChild(chatWindow);

    // Header
    const header = document.createElement('div');
    header.style.cssText = "padding: 16px; background: #000; color: white; display:flex; justify-content:space-between; align-items:center;";
    header.innerHTML = `
        <div style="font-weight:600">Chat Support</div>
        <div style="font-size:12px; opacity:0.8">● Online</div>
    `;
    chatWindow.appendChild(header);

    // Messages
    const messages = document.createElement('div');
    messages.style.cssText = "flex: 1; padding: 16px; overflow-y: auto; background: #fff; display: flex; flex-direction: column;";
    messages.innerHTML = `<div style="text-align: center; color: #888; font-size: 13px; margin-top: auto; margin-bottom: auto;">How can we help you today?</div>`;
    chatWindow.appendChild(messages);

    // Input
    const inputArea = document.createElement('div');
    inputArea.style.cssText = "padding: 12px; border-top: 1px solid #eee; display:flex; gap:8px;";

    const input = document.createElement('input');
    input.placeholder = "Type a message...";
    input.style.cssText = "flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 14px;";

    const sendBtn = document.createElement('button');
    sendBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`;
    sendBtn.style.cssText = "border: none; background: #000; color: white; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; display:flex; align-items:center; justify-content:center;";

    inputArea.appendChild(input);
    inputArea.appendChild(sendBtn);
    chatWindow.appendChild(inputArea);

    // Logic
    let isOpen = false;
    btn.onclick = () => {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.classList.add('open');
            btn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
            setTimeout(() => input.focus(), 100);
        } else {
            chatWindow.classList.remove('open');
            btn.innerHTML = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;
        }
    };

    // Generate a fresh session ID on each page load (no persistence)
    // This ensures web chat users always start with a clean conversation
    const SESSION_ID = 'guest_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    const getUserId = () => {
        // For web chat, always use the fresh session ID (no localStorage)
        // Future: If user logs in with Gmail, we can switch to persistent ID
        return SESSION_ID;
    };

    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        input.value = '';

        const loadingId = appendMessage("...", 'bot', true);

        try {
            const resp = await fetch(`${API_URL}/webhooks/webchat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    widget_id: WIDGET_ID,
                    message: text,
                    user_id: getUserId()
                })
            });
            const data = await resp.json();

            removeMessage(loadingId);

            if (data.error) {
                appendMessage("Error: " + data.error, 'bot');
            } else if (data.response) {
                appendMessage(data.response, 'bot');
            }
        } catch (e) {
            removeMessage(loadingId);
            console.error(e);
            appendMessage("Connection error. Please try again.", 'bot');
        }
    };

    input.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
    sendBtn.onclick = sendMessage;

    function parseMarkdown(text) {
        // Convert [text](url) to <a href="url" target="_blank">text</a>
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        let result = text.replace(linkRegex, '<a href="$2" target="_blank" style="color:#007bff;text-decoration:underline;">$1</a>');

        // Also convert plain URLs (https://...) to clickable links
        // But avoid double-processing URLs already in href="..."
        const urlRegex = /(?<!href="|">)(https?:\/\/[^\s<]+)/g;
        result = result.replace(urlRegex, '<a href="$1" target="_blank" style="color:#007bff;text-decoration:underline;">$1</a>');

        // Convert newlines to <br>
        return result.replace(/\n/g, '<br>');
    }

    function appendMessage(text, role, isLoading = false) {
        const msg = document.createElement('div');
        msg.className = `op-msg op-msg-${role}`;

        // Use innerHTML for Bot messages to allow links, innerText for User for security
        if (role === 'bot') {
            msg.innerHTML = parseMarkdown(text);
        } else {
            msg.innerText = text;
        }

        if (isLoading) msg.id = 'op-loading-' + Date.now();

        if (messages.firstChild && messages.firstChild.innerText.includes('How can we help')) {
            messages.innerHTML = '';
        }

        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
        return msg.id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
})();
