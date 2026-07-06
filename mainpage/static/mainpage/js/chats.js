/* ==========================================================
   chats.js  —  Lista de Chats + Modal Chat Detail
   Tempo real via WebSocket (mesmo transporte usado em
   item_detail.html e chat_detail.html — sem polling HTTP).
   Salvar em: static/mainpage/js/chats.js
   ========================================================== */

(function () {
  'use strict';

  /* ----------------------------------------------------------
     ELEMENTOS
     ---------------------------------------------------------- */
  const backdrop      = document.getElementById('chatModalBackdrop');
  const modal         = document.getElementById('chatModal');
  const modalAvatar   = document.getElementById('modalAvatar');
  const modalUsername = document.getElementById('modalUsername');
  const modalItem     = document.getElementById('modalItemName');
  const modalDot      = document.getElementById('modalStatusDot');
  const modalBadge    = document.getElementById('modalStatusBadge');
  const modalLoading  = document.getElementById('modalLoading');
  const modalMessages = document.getElementById('modalMessages');
  const modalEmpty    = document.getElementById('modalEmptyState');
  const msgBox        = document.getElementById('modalMessagesBox');
  const closeBtn      = document.getElementById('modalCloseBtn');
  const msgForm       = document.getElementById('modalMsgForm');
  const textarea      = document.getElementById('modalConteudo');
  const sendBtn       = document.getElementById('modalSendBtn');
  const toast         = document.getElementById('chatErrorToast');
  const searchInput   = document.getElementById('chatSearch');

  /* Estado do chat aberto no momento */
  let urlMessages   = null;
  let currentChatId = null;
  let chatSocket    = null;
  let chatIsAtivo   = false;
  let lastSender    = null;

  /* ----------------------------------------------------------
     UTILS
     ---------------------------------------------------------- */
  function escapeHtml(text) {
    const d = document.createElement('div');
    d.innerText = text;
    return d.innerHTML;
  }

  function showError(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2800);
  }

  function setComposerEnabled(enabled) {
    textarea.disabled = !enabled;
    textarea.placeholder = enabled ? 'Digite uma mensagem…' : 'Esta conversa está encerrada.';
    sendBtn.disabled = !enabled || textarea.value.trim() === '';
  }

  /* ----------------------------------------------------------
     MODAL — abrir / fechar
     ---------------------------------------------------------- */
  function openModal(data) {
    /* Preenche header */
    modalAvatar.textContent   = data.avatar;
    modalUsername.textContent = data.username;
    modalItem.textContent     = data.item;

    const isAtivo = data.status === 'ativo';
    chatIsAtivo = isAtivo;

    modalDot.className = 'modal-status-dot ' + (isAtivo ? 'dot-ativo' : 'dot-fechado');
    modalBadge.textContent = data.statusLabel;
    modalBadge.className   = 'modal-status-badge ' + (isAtivo ? 'msb-ativo' : 'msb-fechado');

    /* Estado do chat */
    currentChatId = data.chatId;
    urlMessages   = data.urlMessages;

    /* Reset área de mensagens */
    modalMessages.innerHTML = '';
    modalEmpty.style.display   = 'none';
    modalLoading.style.display = 'flex';
    textarea.value = '';
    textarea.style.height = 'auto';
    lastSender = null;
    setComposerEnabled(false);

    /* Abre o backdrop */
    backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';

    /* Carrega histórico e conecta o WebSocket */
    loadHistory();

    /* Foca no input */
    setTimeout(() => textarea.focus(), 280);
  }

  function closeModal() {
    backdrop.classList.remove('open');
    document.body.style.overflow = '';
    if (chatSocket) {
      chatSocket.close();
      chatSocket = null;
    }
    currentChatId = null;
    urlMessages = null;
  }

  /* ----------------------------------------------------------
     HISTÓRICO — carregado uma única vez ao abrir o modal
     ---------------------------------------------------------- */
  async function loadHistory() {
    if (!urlMessages) return;

    try {
      const r    = await fetch(urlMessages);
      const data = await r.json();

      if (!r.ok) { showError(data.error || 'Erro ao carregar'); return; }

      if (data.status) {
        const isAtivo = data.status === 'ativo';
        chatIsAtivo = isAtivo;
        modalBadge.textContent = isAtivo ? 'Ativo' : 'Fechado';
        modalBadge.className   = 'modal-status-badge ' + (isAtivo ? 'msb-ativo' : 'msb-fechado');
        modalDot.className     = 'modal-status-dot '   + (isAtivo ? 'dot-ativo' : 'dot-fechado');
      }

      renderHistory(data.mensagens || []);
      connectSocket();
    } catch {
      modalLoading.style.display = 'none';
      showError('Sem conexão');
    }
  }

  function renderHistory(mensagens) {
    modalLoading.style.display = 'none';

    if (!mensagens.length) {
      modalEmpty.style.display   = 'flex';
      modalMessages.style.display = 'none';
      return;
    }

    modalEmpty.style.display    = 'none';
    modalMessages.style.display = 'flex';
    modalMessages.innerHTML = '';
    lastSender = null;

    mensagens.forEach(appendMessage);
    msgBox.scrollTop = msgBox.scrollHeight;
  }

  /* ----------------------------------------------------------
     MENSAGENS — anexar uma mensagem (histórico ou tempo real)
     ---------------------------------------------------------- */
  function appendMessage(m) {
    if (modalEmpty.style.display !== 'none') {
      modalEmpty.style.display    = 'none';
      modalMessages.style.display = 'flex';
    }

    const senderKey    = m.is_me ? '__me__' : m.remetente;
    const isGroupStart = senderKey !== lastSender;

    const wrap = document.createElement('div');
    wrap.className =
      'msg ' + (m.is_me ? 'me' : 'other') + (isGroupStart ? ' group-start' : '');

    wrap.innerHTML = `
      <div class="bubble">
        <div class="bubble-name">${isGroupStart && !m.is_me ? escapeHtml(m.remetente) : ''}</div>
        <div class="bubble-text">${escapeHtml(m.conteudo)}</div>
        <div class="bubble-footer">
          <span class="bubble-time">${escapeHtml(m.data_envio)}</span>
          ${m.is_me ? '<i class="bi bi-check2-all" style="font-size:.65rem;color:var(--chat-accent);opacity:.7;"></i>' : ''}
        </div>
      </div>`;

    modalMessages.appendChild(wrap);
    lastSender = senderKey;
    msgBox.scrollTop = msgBox.scrollHeight;
  }

  /* ----------------------------------------------------------
     WEBSOCKET — tempo real (substitui o polling antigo)
     ---------------------------------------------------------- */
  function connectSocket() {
    if (!chatIsAtivo || !currentChatId) {
      setComposerEnabled(false);
      return;
    }

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/chat/${currentChatId}/`);

    chatSocket.onopen = () => setComposerEnabled(true);

    chatSocket.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === 'error') {
        showError(data.detail || 'Não foi possível enviar a mensagem.');
        return;
      }

      appendMessage({
        is_me: data.is_me,
        remetente: data.remetente,
        conteudo: data.message,
        data_envio: data.data_envio,
      });
    };

    chatSocket.onclose = () => setComposerEnabled(false);
    chatSocket.onerror = () => showError('Conexão em tempo real perdida.');
  }

  /* ----------------------------------------------------------
     MENSAGENS — enviar via WebSocket
     ---------------------------------------------------------- */
  msgForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const conteudo = textarea.value.trim();
    if (!conteudo || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;

    chatSocket.send(JSON.stringify({ message: conteudo }));
    textarea.value = '';
    textarea.style.height = 'auto';
    sendBtn.disabled = true;
    textarea.focus();
  });

  /* ----------------------------------------------------------
     TEXTAREA — auto-grow + habilitar botão
     ---------------------------------------------------------- */
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    sendBtn.disabled = textarea.disabled || textarea.value.trim() === '';
  });

  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) msgForm.requestSubmit();
    }
  });

  /* ----------------------------------------------------------
     FECHAR MODAL
     ---------------------------------------------------------- */
  closeBtn.addEventListener('click', closeModal);

  /* Clique fora do modal (no backdrop) */
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closeModal();
  });

  /* Tecla Escape */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && backdrop.classList.contains('open')) closeModal();
  });

  /* ----------------------------------------------------------
     ABRIR MODAL ao clicar numa linha
     ---------------------------------------------------------- */
  document.querySelectorAll('.chat-row').forEach((row) => {
    row.addEventListener('click', () => {
      openModal({
        chatId:      row.dataset.chatId,
        avatar:      row.dataset.avatar,
        username:    row.dataset.username,
        item:        row.dataset.item,
        status:      row.dataset.status,
        statusLabel: row.dataset.statusLabel,
        urlMessages: row.dataset.urlMessages,
      });
    });
  });

  /* ----------------------------------------------------------
     BUSCA AO VIVO
     ---------------------------------------------------------- */
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.chat-row').forEach((row) => {
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
})();
