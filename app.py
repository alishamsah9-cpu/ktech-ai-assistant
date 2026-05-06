from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
with open("course_material.txt", "r", encoding="utf-8") as f:
    course_material = f.read()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>IS215-5 AI Learning Assistant | Ali Shamsah</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 40px;
        }

        .container {
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 38px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        }

        .top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }

        .badge {
            background: #111827;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
        }

        .creator {
            color: #2563eb;
            font-weight: bold;
            font-size: 14px;
        }

        h1 {
            margin: 0;
            color: #111827;
            font-size: 36px;
        }

        .subtitle {
            margin-top: 12px;
            margin-bottom: 25px;
            color: #4b5563;
            font-size: 17px;
        }

        textarea {
            width: 100%;
            height: 120px;
            padding: 15px;
            font-size: 16px;
            border-radius: 12px;
            border: 1px solid #cbd5e1;
            resize: vertical;
            box-sizing: border-box;
        }

        button {
            padding: 13px 22px;
            font-size: 15px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 14px;
        }

        .ask-btn {
            background: #2563eb;
            color: white;
        }

        .clear-btn {
            background: #6b7280;
            color: white;
            margin-left: 10px;
        }

        #answer {
            margin-top: 25px;
            background: #f8fafc;
            border-left: 5px solid #2563eb;
            padding: 18px;
            border-radius: 10px;
            white-space: pre-wrap;
            line-height: 1.6;
            color: #111827;
            min-height: 85px;
        }

        .footer {
            margin-top: 30px;
            text-align: center;
            color: #6b7280;
            font-size: 13px;
        }

        .footer strong {
            color: #111827;
        }
    </style>
</head>

<body>
    <div class="container">

        <div class="top-row">
            <div class="badge">K-Tech Course Assistant</div>
            <div class="creator">Developed by Ali Shamsah</div>
        </div>

        <h1>Business Information Systems — IS215-5</h1>

        <p class="subtitle">
            AI Learning Assistant created to support students with simple explanations, course examples, and study guidance.
        </p>

        <textarea
            id="question"
            placeholder="Example: Explain information systems in simple words"
        ></textarea>

        <br>

        <button class="ask-btn" onclick="askAI()">Ask AI Assistant</button>
        <button class="clear-btn" onclick="clearChat()">Clear</button>

        <div id="answer">
            Welcome. Ask a question to begin.
        </div>

        <div class="footer">
            AI Learning Assistant prototype for <strong>Business Information Systems — IS215-5</strong><br>
            Designed and developed by <strong>Ali Shamsah</strong>
        </div>

    </div>

    <script>
        const questionInput = document.getElementById("question");

        questionInput.addEventListener("keydown", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                askAI();
            }
        });

        async function askAI() {
            const question = document.getElementById("question").value;
            const answerBox = document.getElementById("answer");

            if (!question.trim()) {
                answerBox.innerText = "Please type a question first.";
                return;
            }

            answerBox.innerHTML = "🤖 AI Assistant is thinking...";

            try {
                const response = await fetch("/ask", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: question
                    })
                });

                const data = await response.json();
                answerBox.innerText = data.answer;

            } catch (error) {
                answerBox.innerText = "Error connecting to AI assistant.";
            }
        }

        function clearChat() {
            document.getElementById("question").value = "";
            document.getElementById("answer").innerText =
                "Welcome. Ask a question to begin.";
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")

   
    response = client.responses.create(
    model="gpt-5.5",
    input=f"""
You are an AI Learning Assistant for the university course:
Business Information Systems — IS215-5.

This assistant was designed and developed by Ali Shamsah.

Your job is to teach and explain ONLY topics related to the provided course materials.

IMPORTANT RULES:
- Stay within the scope of the course material.
- You MAY simplify, explain, expand, and teach concepts found in the material.
- You MAY provide easy university-related examples.
- You MAY explain concepts in simpler words for beginners.
- Do NOT answer unrelated general questions outside the course.
- If a question is completely unrelated to the course, reply:
"This assistant is designed only for Business Information Systems IS215-5 course support."

Use examples related to:
- students
- professors
- classrooms
- assignments
- university systems
- business organizations

COURSE MATERIAL:
{course_material}

STUDENT QUESTION:
{question}
"""
)



    return jsonify({
        "answer": response.output_text
    })

if __name__ == "__main__":
    app.run(debug=True)