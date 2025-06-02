(function() {
    const protocol = location.protocol === "https:" ? "wss://" : "ws://";
    const wsUrl = protocol + location.host + "/ws";
    const ws = new WebSocket(wsUrl);

    const statusEl = document.getElementById('status');
    const messagesEl = document.getElementById('messages');

    ws.onopen = () => {
        statusEl.textContent = "Connected";
        ws.send("Viewer connected");
    };

    ws.onmessage = event => {
        const msgItem = document.createElement('li');
        msgItem.textContent = "Server: " + event.data;
        messagesEl.appendChild(msgItem);
    };

    ws.onclose = () => {
        statusEl.textContent = "Disconnected";
    };

    ws.onerror = error => {
        console.error("WebSocket error:", error);
    };
})();