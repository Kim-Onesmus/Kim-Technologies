(() => {
  "use strict";

  const root = document.getElementById("kim-support-widget");
  if (!root || root.dataset.initialized === "true") return;

  const $ = (id) => root.querySelector(`#${id}`);

  // If the HTML and JS files are out of sync, say so instead of failing silently.
  const REQUIRED = [
    "kim-chat-launcher",
    "kim-chat-panel",
    "kim-chat-messages",
    "kim-chat-form",
    "kim-chat-input",
    "kim-chat-send",
    "kim-chat-file",
    "kim-chat-attach",
    "kim-chat-file-preview",
    "kim-chat-emoji",
    "kim-emoji-picker",
    "kim-chat-code",
    "kim-menu",
    "kim-menu-btn",
    "kim-resume-wrap",
    "kim-resume-form",
    "kim-resume-input",
    "kim-resume-error",
    "kim-ticket-form-wrap",
    "kim-ticket-form",
    "kim-ticket-submit",
    "kim-ticket-email",
  ];
  const missing = REQUIRED.filter((id) => !$(id));
  if (missing.length) {
    console.error(
      "Kim chat widget: HTML and JS are out of sync. Missing:",
      missing.join(", "),
    );
    return;
  }
  root.dataset.initialized = "true";

  const launcher = $("kim-chat-launcher");
  const panel = $("kim-chat-panel");
  const messages = $("kim-chat-messages");
  const chatForm = $("kim-chat-form");
  const input = $("kim-chat-input");
  const sendBtn = $("kim-chat-send");
  const fileInput = $("kim-chat-file");
  const attachBtn = $("kim-chat-attach");
  const filePreview = $("kim-chat-file-preview");
  const emojiButton = $("kim-chat-emoji");
  const emojiPicker = $("kim-emoji-picker");
  const codeLabel = $("kim-chat-code");
  const menu = $("kim-menu");
  const menuBtn = $("kim-menu-btn");
  const resumeWrap = $("kim-resume-wrap");
  const resumeForm = $("kim-resume-form");
  const resumeInput = $("kim-resume-input");
  const resumeError = $("kim-resume-error");
  const ticketWrap = $("kim-ticket-form-wrap");
  const ticketForm = $("kim-ticket-form");
  const ticketSubmit = $("kim-ticket-submit");
  const ticketEmail = $("kim-ticket-email");

  const MAX_FILE_SIZE = 5 * 1024 * 1024;
  const STORE_KEY = "kimSupportChat";
  const WELCOME = "Hi 👋 How can I help?";
  const QUICK_PROMPTS = [
    ["Our services", "What services does Kim Technologies Group offer?"],
    ["Get a quote", "I'd like a quote for a project."],
    ["Technical support", "I need technical support."],
  ];

  let sessionId = null;
  let chatCode = null;
  let busy = false;
  let closed = false;
  let isOpen = false;
  let started = false;
  let selectedFile = null;
  let quickRow = null;

  // ---------- storage (keeps the chat across page reloads) ----------

  const store = {
    read() {
      try {
        return JSON.parse(localStorage.getItem(STORE_KEY)) || {};
      } catch {
        return {};
      }
    },
    write(value) {
      try {
        localStorage.setItem(STORE_KEY, JSON.stringify(value));
      } catch {
        /* storage unavailable */
      }
    },
    clear() {
      try {
        localStorage.removeItem(STORE_KEY);
      } catch {
        /* storage unavailable */
      }
    },
  };

  function showCode() {
    codeLabel.textContent = chatCode || "…";
  }

  function setSession(id, code) {
    sessionId = id;
    if (code) chatCode = code;
    showCode();
    store.write({ sessionId, chatCode });
  }

  function resetSession() {
    sessionId = null;
    chatCode = null;
    showCode();
    store.clear();
  }

  const saved = store.read();
  sessionId = saved.sessionId || null;
  chatCode = saved.chatCode || null;
  showCode();

  // ---------- networking ----------

  function csrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (match) return decodeURIComponent(match[1]);
    const tokenInput = root.querySelector("[name=csrfmiddlewaretoken]");
    return tokenInput ? tokenInput.value : "";
  }

  async function post(url, payload, multipart = false) {
    const headers = { "X-CSRFToken": csrfToken() };
    if (!multipart) headers["Content-Type"] = "application/json";

    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: multipart ? payload : JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Something went wrong. Please try again.");
    }
    return data;
  }

  async function ensureSession() {
    if (sessionId) return sessionId;

    const data = await post(root.dataset.startUrl, {});
    if (!data.session_id) throw new Error("Could not start a chat.");

    setSession(data.session_id, data.chat_code);
    return sessionId;
  }

  // ---------- open / close ----------

  const isDesktop = () => window.matchMedia("(min-width: 640px)").matches;

  async function openChat() {
    if (isOpen) return;
    isOpen = true;

    panel.classList.add("kim-open");
    panel.setAttribute("aria-hidden", "false");
    launcher.setAttribute("aria-expanded", "true");

    if (!started) {
      started = true;
      await startChat();
    }

    scrollDown();
    if (isDesktop()) input.focus();
  }

  function closeChat() {
    isOpen = false;
    panel.classList.remove("kim-open");
    panel.setAttribute("aria-hidden", "true");
    launcher.setAttribute("aria-expanded", "false");
    hideMenu();
    emojiPicker.hidden = true;
  }

  function hideMenu() {
    menu.hidden = true;
    menuBtn.setAttribute("aria-expanded", "false");
  }

  function hideSheets() {
    emojiPicker.hidden = true;
    resumeWrap.hidden = true;
    ticketWrap.hidden = true;
  }

  // ---------- rendering ----------

  function scrollDown() {
    messages.scrollTop = messages.scrollHeight;
  }

  function formatTime(iso) {
    const date = iso ? new Date(iso) : new Date();
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function addNotice(text) {
    const wrap = document.createElement("div");
    wrap.className = "kim-notice-wrap";

    const pill = document.createElement("span");
    pill.className = "kim-notice";
    pill.textContent = text;

    wrap.appendChild(pill);
    messages.appendChild(wrap);
    scrollDown();
  }

  function addMessage(text, who = "assistant", file = null, iso = null) {
    const isUser = who === "user";

    const row = document.createElement("div");
    row.className = isUser ? "kim-row kim-user" : "kim-row";

    const bubble = document.createElement("div");
    bubble.className = "kim-bubble";

    const body = document.createElement("div");
    body.className = "kim-text";
    body.textContent = text || "";
    bubble.appendChild(body);

    if (file) {
      const attachment = document.createElement("div");
      attachment.className = "kim-file";
      attachment.textContent = `${file.type && file.type.startsWith("image/") ? "🖼️" : "📎"} ${file.name}`;
      bubble.appendChild(attachment);
    }

    const meta = document.createElement("div");
    meta.className = "kim-meta";

    const time = document.createElement("span");
    time.textContent = formatTime(iso);
    meta.appendChild(time);

    if (isUser) {
      const tick = document.createElement("span");
      tick.className = "kim-tick";
      tick.textContent = "✓✓";
      meta.appendChild(tick);
    }

    bubble.appendChild(meta);
    row.appendChild(bubble);
    messages.appendChild(row);
    scrollDown();

    return { row, textElement: body, timeElement: time };
  }

  function addTyping() {
    const pending = addMessage("", "assistant");
    pending.textElement.innerHTML =
      '<span class="kim-typing" aria-label="Typing"><i></i><i></i><i></i></span>';
    return pending;
  }

  function addActions(buttons) {
    const row = document.createElement("div");
    row.className = "kim-actions";

    buttons.forEach(({ label, primary, onClick }) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.className = primary ? "kim-btn-primary" : "kim-btn-ghost";
      button.addEventListener("click", () => {
        row.remove();
        onClick();
      });
      row.appendChild(button);
    });

    messages.appendChild(row);
    scrollDown();
    return row;
  }

  // The email form only appears after the visitor taps "Yes".
  function showConsent() {
    addActions([
      {
        label: "Yes, contact support",
        primary: true,
        onClick: () => showTicketForm(),
      },
      {
        label: "No, continue here",
        primary: false,
        onClick: () => send("No thanks, let's continue here."),
      },
    ]);
  }

  function showWelcome() {
    messages.innerHTML = "";

    if (chatCode) {
      addNotice(`Chat ID: ${chatCode} · keep it to resume this chat later`);
    }
    addMessage(WELCOME, "assistant");

    quickRow = document.createElement("div");
    quickRow.className = "kim-chips";

    QUICK_PROMPTS.forEach(([label, prompt]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "kim-chip";
      button.textContent = label;
      button.addEventListener("click", () => send(prompt));
      quickRow.appendChild(button);
    });

    messages.appendChild(quickRow);
  }

  function removeQuickRow() {
    if (quickRow) {
      quickRow.remove();
      quickRow = null;
    }
  }

  function renderHistory(list, isClosed) {
    messages.innerHTML = "";
    quickRow = null;

    if (!list || !list.length) {
      showWelcome();
    } else {
      list.forEach((item) =>
        addMessage(
          item.content,
          item.role === "user" ? "user" : "assistant",
          null,
          item.created_at,
        ),
      );
      addNotice(`Chat ${chatCode} resumed`);
    }

    setClosed(Boolean(isClosed));
  }

  function applyDisabled() {
    const off = busy || closed;
    input.disabled = off;
    sendBtn.disabled = off;
    attachBtn.disabled = off;
    input.placeholder = closed ? "This chat is closed" : "Type a message";
  }

  function setClosed(value) {
    closed = value;
    applyDisabled();
    if (value)
      addNotice("This chat is closed. Start a new chat from the menu.");
  }

  function setBusy(value) {
    busy = value;
    applyDisabled();
  }

  // ---------- start / restore / resume ----------

  async function startChat() {
    if (sessionId) {
      try {
        const data = await post(root.dataset.resumeUrl, {
          session_id: sessionId,
        });
        setSession(data.session_id, data.chat_code);
        renderHistory(data.messages, data.closed);
        return;
      } catch {
        resetSession(); // the stored chat no longer exists
      }
    }

    try {
      await ensureSession();
    } catch {
      /* a session is created again on the first message */
    }

    showWelcome();
  }

  async function resumeByCode(code) {
    resumeError.hidden = true;

    try {
      const data = await post(root.dataset.resumeUrl, { chat_code: code });
      setSession(data.session_id, data.chat_code);
      renderHistory(data.messages, data.closed);
      resumeWrap.hidden = true;
      resumeInput.value = "";
      scrollDown();
    } catch (error) {
      resumeError.textContent = error.message;
      resumeError.hidden = false;
    }
  }

  async function newChat() {
    resetSession();
    closed = false;
    applyDisabled();
    hideSheets();

    try {
      await ensureSession();
    } catch {
      /* created on the first message */
    }

    showWelcome();
  }

  // ---------- sending ----------

  async function send(message, file = null) {
    message = (message || "").trim();
    if ((!message && !file) || busy || closed) return;

    await openChat();
    setBusy(true);
    removeQuickRow();
    hideSheets();

    addMessage(message || "Please review this attachment.", "user", file);

    input.value = "";
    input.style.height = "auto";
    selectedFile = null;
    fileInput.value = "";
    filePreview.hidden = true;
    filePreview.textContent = "";

    const pending = addTyping();

    try {
      await ensureSession();

      let data;

      if (file) {
        const formData = new FormData();
        formData.append("session_id", sessionId);
        formData.append("message", message);
        formData.append("file", file);
        data = await post(root.dataset.messageUrl, formData, true);
      } else {
        data = await post(root.dataset.messageUrl, {
          session_id: sessionId,
          message,
        });
      }

      // Always keep the header's chat ID in sync with the server.
      if (data.session_id) setSession(data.session_id, data.chat_code);

      pending.textElement.textContent =
        data.answer || "I couldn't answer that. Please try again.";
      pending.timeElement.textContent = formatTime();

      if (data.escalate) showConsent();
    } catch (error) {
      pending.textElement.textContent =
        error.message || "Chat is unavailable right now. Please try again.";
      pending.timeElement.textContent = formatTime();
      showConsent();
    } finally {
      setBusy(false);
      scrollDown();
      if (isDesktop()) input.focus();
    }
  }

  chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    send(input.value, selectedFile);
  });

  // Enter sends; Shift+Enter adds a new line.
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });

  // The typing box grows with the text, up to a limit.
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 112)}px`;
  });

  // ---------- emoji and attachments ----------

  emojiButton.addEventListener("click", () => {
    const show = emojiPicker.hidden;
    hideSheets();
    emojiPicker.hidden = !show;
  });

  emojiPicker.querySelectorAll("[data-emoji]").forEach((button) => {
    button.addEventListener("click", () => {
      const emoji = button.dataset.emoji;
      const start = input.selectionStart ?? input.value.length;
      const end = input.selectionEnd ?? input.value.length;

      input.value =
        input.value.slice(0, start) + emoji + input.value.slice(end);

      const cursor = start + emoji.length;
      input.focus();
      input.setSelectionRange(cursor, cursor);
      emojiPicker.hidden = true;
    });
  });

  attachBtn.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    const file = fileInput.files && fileInput.files[0];
    selectedFile = null;

    if (!file) {
      filePreview.hidden = true;
      filePreview.textContent = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      window.alert("Please choose a file smaller than 5 MB.");
      fileInput.value = "";
      filePreview.hidden = true;
      return;
    }

    selectedFile = file;
    filePreview.textContent = `📎 ${file.name} · ${(file.size / 1024).toFixed(0)} KB`;
    filePreview.hidden = false;
  });

  // ---------- support ticket (email only, after the visitor agrees) ----------

  async function showTicketForm() {
    hideSheets();

    try {
      await ensureSession();
    } catch (error) {
      addMessage(error.message, "assistant");
      return;
    }

    ticketWrap.hidden = false;
    ticketEmail.focus();
  }

  ticketForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (ticketSubmit.disabled) return;

    const email = ticketEmail.value.trim();
    if (!email) {
      ticketEmail.focus();
      return;
    }

    ticketSubmit.disabled = true;
    ticketSubmit.textContent = "Sending…";

    try {
      await ensureSession();

      const data = await post(root.dataset.ticketUrl, {
        email,
        session_id: sessionId,
        source: "website_ai_support",
      });

      addMessage(
        data.message || "Done. Our team will reply to your email.",
        "assistant",
      );
      addNotice(`Your chat ID: ${data.chat_code || chatCode}`);

      ticketForm.reset();
      ticketWrap.hidden = true;
    } catch (error) {
      addMessage(
        error.message || "We couldn't send your request. Please try again.",
        "assistant",
      );
    } finally {
      ticketSubmit.disabled = false;
      ticketSubmit.textContent = "Send";
      scrollDown();
    }
  });

  resumeForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const code = resumeInput.value.trim();
    if (code) resumeByCode(code);
  });

  // ---------- buttons: one delegated handler for every [data-action] ----------

  root.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-action]");
    if (!target || !root.contains(target)) return;

    switch (target.dataset.action) {
      case "close":
        closeChat();
        break;

      case "toggle-menu": {
        const show = menu.hidden;
        menu.hidden = !show;
        menuBtn.setAttribute("aria-expanded", String(show));
        break;
      }

      case "menu-resume":
        hideMenu();
        hideSheets();
        resumeError.hidden = true;
        resumeWrap.hidden = false;
        resumeInput.focus();
        break;

      case "menu-new":
        hideMenu();
        newChat();
        break;

      case "menu-contact":
        hideMenu();
        showTicketForm();
        break;

      case "resume-cancel":
        resumeWrap.hidden = true;
        resumeError.hidden = true;
        break;

      case "ticket-cancel":
        ticketWrap.hidden = true;
        break;

      case "copy-id":
        if (!chatCode) break;
        try {
          await navigator.clipboard.writeText(chatCode);
          codeLabel.textContent = "Copied ✓";
          setTimeout(showCode, 1500);
        } catch {
          /* clipboard unavailable */
        }
        break;

      default:
        break;
    }
  });

  launcher.addEventListener("click", () => (isOpen ? closeChat() : openChat()));

  // Close the menu when tapping elsewhere; Esc closes the menu, then the chat.
  document.addEventListener("click", (event) => {
    if (
      !menu.hidden &&
      !menu.contains(event.target) &&
      !menuBtn.contains(event.target)
    ) {
      hideMenu();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !isOpen) return;
    if (!menu.hidden) hideMenu();
    else closeChat();
  });
})();
