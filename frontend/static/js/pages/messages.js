document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendMessageBtn');
    const chatMessages = document.getElementById('chatMessages');

    if (sendBtn && messageInput) {
        sendBtn.addEventListener('click', () => sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble sent animate-fade-in';
        bubble.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        `;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        messageInput.value = '';
    }

    const conversationItems = document.querySelectorAll('.conversation-item');
    conversationItems.forEach(item => {
        item.addEventListener('click', () => {
            conversationItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
});
