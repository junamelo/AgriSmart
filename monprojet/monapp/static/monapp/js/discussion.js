(function () {
    function escapeHtml(text) {
        return text
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

    function addMessage(container, emptyState, currentUserId, message) {
        if (emptyState) {
            emptyState.remove();
        }

        const isMine = String(message.auteur_id) === String(currentUserId);
        const wrapper = document.createElement('div');
        wrapper.className = `flex ${isMine ? 'justify-end' : 'justify-start'}`;

        wrapper.innerHTML = `
            <div class="max-w-[80%] rounded-2xl px-4 py-3 ${isMine ? 'bg-green-600 text-white' : 'bg-white border border-gray-200 text-gray-800'}">
                <div class="text-xs opacity-80 mb-1">${escapeHtml(message.auteur_nom)} · ${formatDate(message.date_envoi)}</div>
                <p class="whitespace-pre-wrap">${escapeHtml(message.contenu)}</p>
            </div>
        `;

        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }

    document.addEventListener('DOMContentLoaded', function () {
        const config = window.DISCUSSION_CONFIG;
        const messagesContainer = document.getElementById('discussion-messages');
        const form = document.getElementById('discussion-form');
        const input = document.getElementById('discussion-input');
        const statusBadge = document.getElementById('discussion-status');

        if (!config || !messagesContainer || !form || !input) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketUrl = `${protocol}//${window.location.host}${config.websocketPath}`;
        const socket = new WebSocket(socketUrl);

        socket.addEventListener('open', function () {
            if (statusBadge) {
                statusBadge.textContent = 'En ligne';
                statusBadge.className = 'text-sm px-3 py-1 rounded-full bg-green-100 text-green-700';
            }
        });

        socket.addEventListener('close', function () {
            if (statusBadge) {
                statusBadge.textContent = 'Déconnecté';
                statusBadge.className = 'text-sm px-3 py-1 rounded-full bg-red-100 text-red-700';
            }
        });

        socket.addEventListener('error', function () {
            if (statusBadge) {
                statusBadge.textContent = 'Erreur de connexion';
                statusBadge.className = 'text-sm px-3 py-1 rounded-full bg-red-100 text-red-700';
            }
        });

        socket.addEventListener('message', function (event) {
            const payload = JSON.parse(event.data);

            if (payload.type === 'history') {
                payload.messages.forEach((message) => addMessage(messagesContainer, document.getElementById('discussion-empty'), window.DISCUSSION_CONFIG.currentUserId, message));
                return;
            }

            if (payload.type === 'message') {
                addMessage(messagesContainer, document.getElementById('discussion-empty'), window.DISCUSSION_CONFIG.currentUserId, payload.message);
            }
        });

        form.addEventListener('submit', function (event) {
            event.preventDefault();

            const contenu = input.value.trim();
            if (!contenu || socket.readyState !== WebSocket.OPEN) {
                return;
            }

            socket.send(JSON.stringify({
                type: 'message',
                contenu: contenu,
            }));

            input.value = '';
            input.focus();
        });
    });
})();