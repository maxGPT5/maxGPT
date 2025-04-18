import streamlit as st
import requests
import re
from docx import Document
import fitz  # PyMuPDF

# --- App Config ---
st.set_page_config(page_title="maxGPT | AI Chat", layout="centered")

# --- Constants ---
API_KEY = "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"  # 🔑 Add your OpenRouter API key here
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
GOOGLE_API_KEY = "AIzaSyABhQ0GlDJXEx3StLHpdi3KjMG7cB7zxzI"  # 🔑 Add your Google Custom Search API key here
GOOGLE_CX = "60640d6cf20594547"  # 🔑 Add your Google Custom Search Engine ID here

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Styles ---
st.markdown("""
    <style>
        .chat-bubble {
            padding: 0.8rem 1rem;
            border-radius: 1rem;
            margin: 0.5rem 0;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-bubble {
            background-color: #DCF8C6;
            margin-left: auto;
            text-align: right;
        }
        .ai-bubble {
            background-color: #F1F0F0;
            margin-right: auto;
            text-align: left;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
        }
        code {
            background-color: #f5f5f5 !important;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🧠 maxGPT - Chat with AI")

# --- Utility: Check for "search:" command ---
def is_search_command(input_text):
    return input_text.strip().lower().startswith("search:")

# --- Google Search Function ---
def google_search(query):
    search_url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])

        if not items:
            return "❌ No results found."

        formatted_results = ""
        for item in items[:5]:
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            formatted_results += f"**[{title}]({link})**\n\n{snippet}\n\n---\n"

        return formatted_results.strip()

    except requests.exceptions.RequestException as e:
        return f"❌ Google Search Error: {e}"

# --- File Text Extraction ---
def extract_file_text(file):
    file_type = file.name.split(".")[-1].lower()

    if file_type in ["txt", "md"]:
        return file.read().decode("utf-8")
    elif file_type == "pdf":
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    elif file_type == "docx":
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    else:
        return "❌ Unsupported file type."

# --- Ask AI Function ---
def ask_ai(user_input):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",
        "X-Title": "Streamlit Chat"
    }

    st.session_state.history.append({"role": "user", "content": user_input})

    payload = {
        "model": MODEL,
        "messages": st.session_state.history
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_reply = response.json()["choices"][0]["message"]["content"]
        humanized_reply = humanize_ai_response(ai_reply)
        st.session_state.history.append({"role": "assistant", "content": humanized_reply})
        return humanized_reply
    except requests.exceptions.RequestException as e:
        return f"❌ Error: {e}"

# --- Make AI Sound More Human ---
def humanize_ai_response(response_text):
    response_text = response_text.strip()
    response_text = response_text[0].capitalize() + response_text[1:]
    response_text = response_text.replace("I think", "Hmm, I think")
    response_text = response_text.replace("I don't know", "I'm not totally sure, but I can help you look it up!")
    response_text += " 🤔 Let me know if you need more info!"
    if len(response_text) > 150:
        response_text = f"\n{response_text}"
    return response_text

# --- Render AI Markdown / Code ---
def render_ai_response(text):
    parts = re.split(r"```(?:\w+)?\n", text)
    for i, part in enumerate(parts):
        if i % 2 == 0:
            st.markdown(f"<p style='font-size: 16px;'>{part}</p>", unsafe_allow_html=True)
        else:
            code = part.rstrip("`").rstrip()
            st.code(code, language="python")

# --- Top UI: File Upload / Clear Chat ---
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("📎 Upload a file (.txt, .md, .pdf, .docx)", type=["txt", "md", "pdf", "docx"])
with col2:
    if st.button("🧼 Clear Chat"):
        st.session_state.history = []

# --- Process File Upload ---
if uploaded_file is not None:
    file_text = extract_file_text(uploaded_file)
    st.markdown("✅ **File uploaded. Extracted content:**")
    st.text_area("📖 File Content", file_text, height=200)
    if st.button("📤 Send file content to AI"):
        with st.spinner("Sending file to AI..."):
            ask_ai(file_text)

# --- Chat History Rendering ---
if st.session_state.history:
    st.markdown("### 💬 Conversation")
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-container"><div class="chat-bubble user-bubble"><strong>You:</strong><br>{msg["content"]}</div></div>',
                unsafe_allow_html=True
            )
        elif msg["role"] == "assistant":
            st.markdown(
                f'<div class="chat-container"><div class="chat-bubble ai-bubble"><strong>AI:</strong></div></div>',
                unsafe_allow_html=True
            )
            render_ai_response(msg["content"])

# --- Chat Input ---
st.markdown("### Ask something:")
user_input = st.text_area("You:", placeholder="Ask me anything... or try: search: python tutorial", key="input", height=100)
send_button = st.button("Send")

# --- Handle Input or Search ---
if send_button or user_input:
    if user_input:
        if is_search_command(user_input):
            search_query = user_input.replace("search:", "", 1).strip()
            with st.spinner(f"Searching Google for: {search_query}"):
                results = google_search(search_query)
                st.markdown("### 🔍 Google Search Results")
                st.markdown(results, unsafe_allow_html=True)
        else:
            with st.spinner("Thinking..."):
                ai_response = ask_ai(user_input)
                if ai_response and "I don't know" in ai_response:
                    with st.spinner(f"Searching Google for: {user_input.strip()}"):
                        results = google_search(user_input.strip())
                        st.markdown("### 🔍 Google Search Results")
                        st.markdown(results, unsafe_allow_html=True)
                else:
                    st.write(f"maxGPT: {ai_response}")
