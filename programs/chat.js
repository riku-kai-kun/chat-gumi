const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const nameEl = document.getElementById("name");
const textEl = document.getElementById("text");

let latestRenderedId = 0;

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderMessages(messages) {
  const currentLastId = messages.length > 0 ? messages[messages.length - 1].id : 0;
  if (currentLastId === latestRenderedId) return;

  messagesEl.innerHTML = messages
    .map((item) => {
      const time = new Date(item.timestamp * 1000).toLocaleTimeString("ja-JP");
      return `
        <article class="message">
          <div><strong>${escapeHtml(item.name)}</strong>: ${escapeHtml(item.text)}</div>
          <div class="meta">${time}</div>
        </article>
      `;
    })
    .join("");

  messagesEl.scrollTop = messagesEl.scrollHeight;
  latestRenderedId = currentLastId;
}

async function fetchMessages() {
  try {
    const response = await fetch("/api/messages");
    if (!response.ok) return;
    const data = await response.json();
    renderMessages(data.messages ?? []);
  } catch (error) {
    // Polling based chat; ignore intermittent network failures.
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = nameEl.value.trim();
  const text = textEl.value.trim();
  if (!name || !text) return;

  try {
    const response = await fetch("/api/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, text }),
    });
    if (response.ok) {
      textEl.value = "";
      await fetchMessages();
    }
  } catch (error) {
    // Keep UX minimal and silent for now.
  }
});

fetchMessages();
setInterval(fetchMessages, 1000);
