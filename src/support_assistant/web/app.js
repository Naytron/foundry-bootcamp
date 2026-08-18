"use strict";

const state = {
  sessionId: null,
  maxMessageCharacters: 4000,
};

const elements = {
  form: document.querySelector("#chat-form"),
  message: document.querySelector("#message"),
  messages: document.querySelector("#messages"),
  send: document.querySelector("#send"),
  status: document.querySelector("#chat-status"),
  count: document.querySelector("#character-count"),
  token: document.querySelector("#token"),
  saveToken: document.querySelector("#save-token"),
  tokenStatus: document.querySelector("#token-status"),
  newChat: document.querySelector("#new-chat"),
  modeBadge: document.querySelector("#mode-badge"),
};

function appendMessage(role, text, extraClass = "") {
  const item = document.createElement("li");
  item.className = `message ${role} ${extraClass}`.trim();

  const label = document.createElement("span");
  label.className = "message-role";
  label.textContent = role === "user" ? "You" : "Assistant";

  const content = document.createElement("p");
  content.textContent = text;
  item.append(label, content);
  elements.messages.append(item);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  return content;
}

function parseEvent(block) {
  let name = "message";
  const data = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      name = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      data.push(line.slice(5).trim());
    }
  }
  return { name, data: JSON.parse(data.join("\n")) };
}

async function streamEvents(response, onEvent) {
  if (!response.body) {
    throw new Error("The response stream is unavailable.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      if (block.trim()) {
        onEvent(parseEvent(block));
      }
    }
    if (done) {
      if (buffer.trim()) {
        onEvent(parseEvent(buffer));
      }
      return;
    }
  }
}

async function sendMessage(message) {
  const token = sessionStorage.getItem("bootcampAccessToken");
  if (!token) {
    throw new Error("Add the bootcamp access token first.");
  }

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      session_id: state.sessionId,
    }),
  });

  if (!response.ok) {
    const problem = await response.json().catch(() => ({ detail: "Request failed." }));
    throw new Error(problem.detail || `Request failed with status ${response.status}.`);
  }

  const output = appendMessage("assistant", "");
  await streamEvents(response, ({ name, data }) => {
    if (name === "metadata") {
      state.sessionId = data.session_id;
    } else if (name === "delta") {
      output.textContent += data.text;
      elements.messages.scrollTop = elements.messages.scrollHeight;
    } else if (name === "error") {
      output.parentElement.classList.add("error");
      output.textContent = data.message;
    }
  });
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = elements.message.value.trim();
  if (!message) {
    return;
  }
  appendMessage("user", message);
  elements.message.value = "";
  elements.count.textContent = "0 characters";
  elements.send.disabled = true;
  elements.status.textContent = "Assistant is responding.";
  try {
    await sendMessage(message);
    elements.status.textContent = "Response complete.";
  } catch (error) {
    appendMessage("assistant", error.message, "error");
    elements.status.textContent = "Request failed.";
  } finally {
    elements.send.disabled = false;
    elements.message.focus();
  }
});

elements.message.addEventListener("input", () => {
  const length = elements.message.value.length;
  elements.count.textContent = `${length} of ${state.maxMessageCharacters} characters`;
});

elements.saveToken.addEventListener("click", () => {
  const token = elements.token.value.trim();
  if (!token) {
    elements.tokenStatus.textContent = "Enter a token.";
    return;
  }
  sessionStorage.setItem("bootcampAccessToken", token);
  elements.token.value = "";
  elements.tokenStatus.textContent = "Token stored for this browser tab.";
  elements.message.focus();
});

elements.newChat.addEventListener("click", () => {
  state.sessionId = null;
  elements.messages.replaceChildren();
  appendMessage("assistant", "New conversation started.");
  elements.status.textContent = "";
  elements.message.focus();
});

async function initialize() {
  if (sessionStorage.getItem("bootcampAccessToken")) {
    elements.tokenStatus.textContent = "A token is stored for this browser tab.";
  }
  try {
    const response = await fetch("/api/config");
    const config = await response.json();
    state.maxMessageCharacters = config.max_message_characters;
    elements.message.maxLength = state.maxMessageCharacters;
    elements.modeBadge.textContent = config.mode === "mock" ? "Local mock mode" : "Microsoft Foundry";
  } catch {
    elements.modeBadge.textContent = "Configuration unavailable";
  }
}

initialize();
