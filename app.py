from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "course_material.txt"), "r", encoding="utf-8") as f:
    course_material = f.read()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_sections(text):
    """Split course material into labelled sections using the ====\nTITLE\n==== pattern.
    The text before the first header is treated as Chapter 3 (hardware), which is how
    the source file is laid out."""
    pattern = re.compile(r"={10,}\s*\n([^\n]+)\n={10,}\s*\n")
    matches = list(pattern.finditer(text))
    sections = []

    if matches:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append({
                "key": "ch3",
                "label": "Chapter 3 — Hardware",
                "content": preamble,
            })

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        ch_match = re.match(r"CHAPTER\s+(\d+)\s*[—-]\s*(.+)", title, re.IGNORECASE)
        if ch_match:
            num, name = ch_match.group(1), ch_match.group(2).strip().title()
            key = f"ch{num}"
            label = f"Chapter {num} — {name}"
        else:
            key = "info_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
            label = title.title()

        sections.append({"key": key, "label": label, "content": body})

    return sections


SECTIONS = parse_sections(course_material)
SECTION_MAP = {s["key"]: s for s in SECTIONS}


SYSTEM_INSTRUCTIONS = """You are an AI Learning Assistant for the university course:
Business Information Systems — IS215-5.

This assistant was designed and developed by Ali Shamsah.

Your job is to teach and explain ONLY topics related to the provided course materials.

IMPORTANT RULES:
- ONLY answer using the provided course material.
- If the question is outside the course material, reply:
"This topic is outside the current course materials."
- Do not answer sports, politics, celebrities, or unrelated topics.
- If asked for quizzes, generate MCQs, true/false, or short-answer questions from the course material.
- If asked in Arabic, answer in Arabic.
- Always explain step-by-step in simple language.
- Stay within the scope of the course material.
- You MAY simplify, explain, expand, and teach concepts found in the material.
- You MAY provide easy university-related examples.
- You MAY explain concepts in simpler words for beginners.
- Do NOT answer unrelated general questions outside the course.
- If a student refers to a previous message ("explain that simpler", "give me an example", "what about the second point"), use the conversation history to understand what they mean.
- If a question is completely unrelated to the course, reply:
"This assistant is designed only for Business Information Systems IS215-5 course support."

Use examples related to:
- students
- professors
- classrooms
- assignments
- university systems
- business organizations

Format answers with short paragraphs, bullet points where helpful, and bold key terms using **markdown**."""


def build_prompt(question, chapter_key, history):
    if chapter_key and chapter_key != "all" and chapter_key in SECTION_MAP:
        section = SECTION_MAP[chapter_key]
        material_header = f"SELECTED TOPIC: {section['label']}"
        material_body = section["content"]
    else:
        material_header = "FULL COURSE MATERIAL (all chapters)"
        material_body = course_material

    history_text = ""
    if history:
        lines = []
        for turn in history[-6:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if not content:
                continue
            if role == "user":
                lines.append(f"Student: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
        if lines:
            history_text = "\n\nCONVERSATION HISTORY (for context on follow-up questions):\n" + "\n".join(lines)

    return f"""{SYSTEM_INSTRUCTIONS}

{material_header}:
{material_body}
{history_text}

CURRENT STUDENT QUESTION:
{question}
"""


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>IS215-5 AI Learning Assistant | Ali Shamsah</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        html, body { height: 100%; }
        body {
            margin: 0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 100%);
            color: #111827;
            -webkit-font-smoothing: antialiased;
        }

        .shell {
            max-width: 920px;
            margin: 0 auto;
            padding: 24px 20px 40px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .card {
            background: #ffffff;
            border-radius: 22px;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
            padding: 28px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }

        .header { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
        .badge {
            background: #111827; color: white; padding: 6px 14px;
            border-radius: 999px; font-size: 13px; font-weight: 500;
        }
        .creator { color: #2563eb; font-weight: 600; font-size: 13px; }

        h1 {
            margin: 14px 0 6px; color: #0f172a; font-size: 28px; line-height: 1.2;
        }
        .subtitle { margin: 0 0 18px; color: #475569; font-size: 15px; }

        .controls {
            display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
            background: #f8fafc; padding: 12px; border-radius: 14px;
            margin-bottom: 16px;
        }
        .controls label { font-size: 13px; color: #475569; font-weight: 500; }
        select {
            flex: 1; min-width: 200px;
            padding: 10px 12px; font-size: 14px; font-family: inherit;
            border-radius: 10px; border: 1px solid #cbd5e1; background: white;
            color: #0f172a; cursor: pointer;
        }
        select:focus { outline: 2px solid #2563eb; outline-offset: 1px; }

        .chat {
            flex: 1; min-height: 280px;
            border: 1px solid #e2e8f0; border-radius: 14px;
            background: #f8fafc; padding: 16px; overflow-y: auto;
            display: flex; flex-direction: column; gap: 12px;
            margin-bottom: 14px;
            max-height: 55vh;
        }
        .msg { display: flex; gap: 10px; align-items: flex-start; animation: fadeIn 0.25s ease; }
        .msg .avatar {
            flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 13px; font-weight: 700; color: white;
        }
        .msg.user .avatar { background: #2563eb; }
        .msg.assistant .avatar { background: #0f172a; }
        .bubble {
            background: white; padding: 12px 14px; border-radius: 12px;
            line-height: 1.55; font-size: 15px; max-width: 88%;
            border: 1px solid #e2e8f0;
            white-space: normal;
        }
        .msg.user .bubble { background: #2563eb; color: white; border-color: #2563eb; }
        .bubble p { margin: 0 0 8px; }
        .bubble p:last-child { margin-bottom: 0; }
        .bubble ul, .bubble ol { margin: 6px 0 8px; padding-left: 22px; }
        .bubble li { margin: 3px 0; }
        .bubble strong { color: inherit; }
        .bubble code { background: rgba(15, 23, 42, 0.08); padding: 2px 6px; border-radius: 5px; font-size: 13px; }
        .msg.user .bubble code { background: rgba(255,255,255,0.2); }

        .empty {
            text-align: center; color: #94a3b8; font-size: 14px;
            padding: 32px 16px;
        }

        .input-row {
            display: flex; gap: 10px; align-items: flex-end;
        }
        textarea {
            flex: 1; min-height: 60px; max-height: 160px;
            padding: 12px 14px; font-size: 15px; font-family: inherit;
            border-radius: 12px; border: 1px solid #cbd5e1;
            resize: none; line-height: 1.45;
        }
        textarea:focus { outline: 2px solid #2563eb; outline-offset: 1px; }

        .btn-stack { display: flex; flex-direction: column; gap: 8px; }
        button {
            padding: 12px 18px; font-size: 14px; font-weight: 600;
            border: none; border-radius: 10px; cursor: pointer;
            font-family: inherit;
            transition: transform 0.05s ease, opacity 0.2s ease;
        }
        button:active { transform: scale(0.97); }
        button:disabled { opacity: 0.55; cursor: not-allowed; }
        .ask-btn { background: #2563eb; color: white; }
        .ask-btn:hover:not(:disabled) { background: #1d4ed8; }
        .clear-btn { background: #e2e8f0; color: #334155; }
        .clear-btn:hover:not(:disabled) { background: #cbd5e1; }

        .typing {
            display: inline-flex; gap: 4px; align-items: center;
            padding: 4px 0;
        }
        .typing span {
            width: 7px; height: 7px; border-radius: 50%; background: #94a3b8;
            animation: bounce 1.2s infinite ease-in-out;
        }
        .typing span:nth-child(2) { animation-delay: 0.15s; }
        .typing span:nth-child(3) { animation-delay: 0.3s; }

        .footer {
            margin-top: 18px; text-align: center; color: #64748b; font-size: 12px;
        }
        .footer strong { color: #0f172a; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        @media (max-width: 600px) {
            .shell { padding: 14px 12px 24px; }
            .card { padding: 18px; border-radius: 18px; }
            h1 { font-size: 22px; }
            .bubble { font-size: 14px; }
            .input-row { flex-direction: column; align-items: stretch; }
            .btn-stack { flex-direction: row; }
            .btn-stack button { flex: 1; }
        }
    </style>
</head>
<body>
    <div class="shell">
        <div class="card">
            <div class="header">
                <div class="badge">K-Tech Course Assistant</div>
                <div class="creator">Developed by Ali Shamsah</div>
            </div>

            <h1>Business Information Systems — IS215-5</h1>
            <p class="subtitle">Pick a chapter, ask anything, and follow up with more questions just like a real conversation.</p>

            <div class="controls">
                <label for="chapter">Topic:</label>
                <select id="chapter">
                    <option value="all">All chapters (slower)</option>
                    {{ chapter_options | safe }}
                </select>
            </div>

            <div id="chat" class="chat">
                <div class="empty" id="emptyState">
                    Welcome! Pick a topic above and ask your first question.<br>
                    Example: <em>"Explain information systems in simple words"</em>
                </div>
            </div>

            <div class="input-row">
                <textarea id="question" placeholder="Type your question..." rows="2"></textarea>
                <div class="btn-stack">
                    <button class="ask-btn" id="askBtn" onclick="askAI()">Ask</button>
                    <button class="clear-btn" onclick="clearChat()">Clear</button>
                </div>
            </div>

            <div class="footer">
                AI Learning Assistant for <strong>Business Information Systems — IS215-5</strong><br>
                Designed and developed by <strong>Ali Shamsah</strong>
            </div>
        </div>
    </div>

    <script>
        const chat = document.getElementById("chat");
        const emptyState = document.getElementById("emptyState");
        const questionInput = document.getElementById("question");
        const askBtn = document.getElementById("askBtn");
        const chapterSelect = document.getElementById("chapter");

        let history = [];

        questionInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                askAI();
            }
        });

        function escapeHtml(str) {
            const div = document.createElement("div");
            div.textContent = str;
            return div.innerHTML;
        }

        function addMessage(role, content, asMarkdown) {
            if (emptyState && emptyState.parentNode) emptyState.remove();
            const msg = document.createElement("div");
            msg.className = "msg " + role;
            const avatar = document.createElement("div");
            avatar.className = "avatar";
            avatar.textContent = role === "user" ? "You" : "AI";
            const bubble = document.createElement("div");
            bubble.className = "bubble";
            if (asMarkdown && window.marked) {
                bubble.innerHTML = marked.parse(content);
            } else {
                bubble.innerHTML = escapeHtml(content).replace(/\\n/g, "<br>");
            }
            msg.appendChild(avatar);
            msg.appendChild(bubble);
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
            return bubble;
        }

        function addTyping() {
            const msg = document.createElement("div");
            msg.className = "msg assistant";
            msg.id = "typingMsg";
            msg.innerHTML = '<div class="avatar">AI</div><div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }

        function removeTyping() {
            const t = document.getElementById("typingMsg");
            if (t) t.remove();
        }

        async function askAI() {
            const question = questionInput.value.trim();
            if (!question) return;

            askBtn.disabled = true;
            addMessage("user", question, false);
            questionInput.value = "";
            addTyping();

            try {
                const response = await fetch("/ask", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        question: question,
                        chapter: chapterSelect.value,
                        history: history,
                    }),
                });
                const data = await response.json();
                removeTyping();
                const answer = data.answer || "Sorry, no answer was returned.";
                addMessage("assistant", answer, true);
                history.push({ role: "user", content: question });
                history.push({ role: "assistant", content: answer });
                if (history.length > 12) history = history.slice(-12);
            } catch (err) {
                removeTyping();
                addMessage("assistant", "Error connecting to the AI assistant. Please try again.", false);
            } finally {
                askBtn.disabled = false;
                questionInput.focus();
            }
        }

        function clearChat() {
            history = [];
            chat.innerHTML = '<div class="empty" id="emptyState">Chat cleared. Ask a new question to begin.</div>';
        }
    </script>
</body>
</html>
"""


def render_chapter_options():
    return "\n".join(
        f'<option value="{s["key"]}">{s["label"]}</option>' for s in SECTIONS
    )


@app.route("/")
def home():
    return render_template_string(HTML_PAGE, chapter_options=render_chapter_options())


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    question = (data.get("question") or "").strip()
    chapter = data.get("chapter") or "all"
    history = data.get("history") or []

    if not question:
        return jsonify({"answer": "Please type a question first."})

    prompt = build_prompt(question, chapter, history)

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt,
    )

    return jsonify({"answer": response.output_text})


if __name__ == "__main__":
    app.run(debug=True)
