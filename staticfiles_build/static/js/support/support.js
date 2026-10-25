(() => {
  const root = document.getElementById("kim-support-widget");

  if (!root) return;

  const launcher = document.getElementById("kim-chat-launcher");
  const panel = document.getElementById("kim-chat-panel");
  const closeBtn = document.getElementById("kim-chat-close");
  const messages = document.getElementById("kim-chat-messages");

  const chatForm = document.getElementById("kim-chat-form");
  const input = document.getElementById("kim-chat-input");
  const sendBtn = document.getElementById("kim-chat-send");

  const ticketButton = document.getElementById("kim-create-ticket");
  const ticketWrap = document.getElementById("kim-ticket-form-wrap");
  const ticketForm = document.getElementById("kim-ticket-form");
  const ticketCancel = document.getElementById("kim-ticket-cancel");
  const ticketSubmit = document.getElementById("kim-ticket-submit");

  let sessionId = null;
  let busy = false;

  function csrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);

    if (match) {
      return decodeURIComponent(match[1]);
    }

    const element = root.querySelector("[name=csrfmiddlewaretoken]");

    return element ? element.value : "";
  }

  async function post(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.error || "Request failed. Please try again.");
    }

    return data;
  }

  async function ensureSession() {
    if (sessionId) return sessionId;

    const data = await post(root.dataset.startUrl, {});
    sessionId = data.session_id;

    return sessionId;
  }

  function addMessage(text, who = "assistant") {
    const element = document.createElement("div");

    element.className =
      "kim-chat-bubble " +
      (who === "user" ? "kim-user-bubble" : "kim-assistant-bubble");

    // Use textContent so responses are not interpreted as HTML.
    element.textContent = text;

    messages.appendChild(element);
    messages.scrollTop = messages.scrollHeight;

    return element;
  }

  function setBusy(value) {
    busy = value;
    sendBtn.disabled = value;
    input.disabled = value;
    sendBtn.textContent = value ? "…" : "➤";
  }

  function openChat() {
    panel.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    input.focus();
  }

  function closeChat() {
    panel.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
  }

  launcher.addEventListener("click", () => {
    if (panel.hidden) {
      openChat();
    } else {
      closeChat();
    }
  });

  closeBtn.addEventListener("click", closeChat);

  ticketButton.addEventListener("click", () => {
    ticketWrap.hidden = false;
    ticketWrap.scrollIntoView({
      block: "nearest",
    });
  });

  ticketCancel.addEventListener("click", () => {
    ticketWrap.hidden = true;
  });

  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.prompt;
      chatForm.requestSubmit();
    });
  });

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = input.value.trim();

    if (!message || busy) return;

    openChat();
    addMessage(message, "user");
    input.value = "";

    setBusy(true);

    const pending = addMessage("Thinking…");

    try {
      await ensureSession();

      const data = await post(root.dataset.messageUrl, {
        session_id: sessionId,
        message: message,
      });

      pending.textContent = data.answer;

      if (data.escalate) {
        addMessage(
          "Would you like our team to follow up? " +
            "Select “Create a support ticket” below.",
        );

        ticketWrap.hidden = false;
      }
    } catch (error) {
      pending.textContent =
        error.message ||
        "Chat is temporarily unavailable. Please create a support ticket.";

      ticketWrap.hidden = false;
    } finally {
      setBusy(false);
      messages.scrollTop = messages.scrollHeight;
      input.focus();
    }
  });

  ticketForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (ticketSubmit.disabled) return;

    ticketSubmit.disabled = true;
    ticketSubmit.textContent = "Creating…";

    const payload = Object.fromEntries(new FormData(ticketForm).entries());

    payload.session_id = sessionId || "";

    try {
      const data = await post(root.dataset.ticketUrl, payload);

      addMessage(data.message);

      ticketForm.reset();
      ticketWrap.hidden = true;
    } catch (error) {
      window.alert(
        error.message || "Ticket could not be created. Please try again.",
      );
    } finally {
      ticketSubmit.disabled = false;
      ticketSubmit.textContent = "Create ticket";
    }
  });
})();
