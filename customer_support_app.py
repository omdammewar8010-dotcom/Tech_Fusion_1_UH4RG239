import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime
import json

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Institutional AI Support",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. OFFICE & FAQ DATABASE ---
# EDIT THESE DETAILS TO MATCH YOUR OFFICE
OFFICE_INFO = {
    "Name": "Om Dammewar's AI Lab & Office",
    "Address": "Pune, Maharashtra, India",
    "Contact": "+91-XXXXXXXXXX",
    "Email": "om.dammewar@example.com",
    "Hours": "Mon-Fri: 9 AM - 6 PM | Sat: 10 AM - 2 PM",
    "Department": "IoT, Web Development, and AI Research"
}

FAQ_DATABASE = {
    "English": {
        "Where is the office?": f"We are located at {OFFICE_INFO['Address']}.",
        "How can I reach you?": f"You can call us at {OFFICE_INFO['Contact']} or email {OFFICE_INFO['Email']}.",
        "What are your hours?": f"Our working hours are {OFFICE_INFO['Hours']}.",
        "What do you do?": f"Our office specializes in {OFFICE_INFO['Department']}."
    },
    "Spanish": {
        "¿Dónde está la oficina?": f"Estamos ubicados en {OFFICE_INFO['Address']}."
    }
}

# --- 3. CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: bold; text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .chat-msg { padding: 1rem; border-radius: 12px; margin: 0.5rem 0; }
    .user-msg { background: #667eea; color: white; margin-left: 15%; }
    .bot-msg { background: #f0f2f6; color: #1f1f1f; margin-right: 15%; border: 1px solid #ddd; }
    .level-badge { display: inline-block; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; margin: 5px; }
    .level-1 { background: #10b981; color: white; }
    .level-2 { background: #3b82f6; color: white; }
    .level-3 { background: #8b5cf6; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 4. SESSION STATE & AI CLIENT ---
MODEL_ID = "gemini-3-flash-preview"

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0
if 'language' not in st.session_state:
    st.session_state.language = 'English'
if 'current_level' not in st.session_state:
    st.session_state.current_level = 1

def get_chat_session():
    if 'client' not in st.session_state:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("Missing API Key in secrets.toml")
            st.stop()
        st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        st.session_state.chat = st.session_state.client.chats.create(model=MODEL_ID)
    return st.session_state.chat

# --- 5. CORE AI FUNCTION ---
def get_ai_response(user_input):
    lang = st.session_state.language
    faqs = FAQ_DATABASE.get(lang, FAQ_DATABASE["English"])
    faq_context = "\n".join([f"Q: {q} A: {a}" for q, a in faqs.items()])
    
    chat = get_chat_session()
    
    system_instruction = f"""
    You are the Official Assistant for {OFFICE_INFO['Name']}.
    Office Details: {OFFICE_INFO['Address']}, Contact: {OFFICE_INFO['Contact']}, Hours: {OFFICE_INFO['Hours']}.
    Language: {lang}.
    
    Official Knowledge Base:
    {faq_context}
    
    Instructions:
    1. Always identify as the assistant for {OFFICE_INFO['Name']}.
    2. Greet users warmly. Use the office details for any location/contact queries.
    3. If the answer is not in the knowledge base, provide a professional response.
    """
    
    try:
        response = chat.send_message(f"{system_instruction}\n\nUser: {user_input}")
        return response.text
    except Exception as e:
        if "closed" in str(e).lower():
            st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            st.session_state.chat = st.session_state.client.chats.create(model=MODEL_ID)
            return st.session_state.chat.send_message(user_input).text
        return f"Error: {str(e)}"

# --- 6. MAIN UI ---
def main():
    st.markdown('<h1 class="main-header">🤖 Institutional AI Support Assistant</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Settings")
        lvl = st.selectbox("Feature Level", 
                           ["Level 1: FAQ", "Level 2: Enhanced", "Level 3: Voice"], 
                           index=st.session_state.current_level - 1)
        st.session_state.current_level = int(lvl.split(":")[0].split()[1])
        
        st.session_state.language = st.selectbox("Language", ["English", "Spanish", "French"])
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.chat = st.session_state.client.chats.create(model=MODEL_ID)
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📚 Knowledge Base", "📈 Analytics", "🎤 Voice"])
    
    with tab1:
        # Display Conversation
        for msg in st.session_state.conversation_history:
            role_css = "user-msg" if msg['role'] == 'user' else "bot-msg"
            st.markdown(f'<div class="chat-msg {role_css}">{msg["content"]}</div>', unsafe_allow_html=True)

        # Chat Input
        if prompt := st.chat_input("How can I help you today?"):
            st.session_state.conversation_history.append({"role": "user", "content": prompt})
            with st.spinner("Processing..."):
                reply = get_ai_response(prompt)
                st.session_state.conversation_history.append({"role": "assistant", "content": reply})
                st.session_state.total_queries += 1
                st.rerun()

    with tab2:
        st.markdown(f"### 🏢 {OFFICE_INFO['Name']} - Knowledge Base")
        curr_lang_faqs = FAQ_DATABASE.get(st.session_state.language, FAQ_DATABASE["English"])
        for q, a in curr_lang_faqs.items():
            with st.expander(f"❓ {q}"):
                st.write(a)

    with tab3:
        st.markdown("### 📊 Performance Analytics")
        col1, col2 = st.columns(2)
        col1.metric("Total Queries", st.session_state.total_queries)
        col2.metric("Active Level", f"L{st.session_state.current_level}")

    with tab4:
        if st.session_state.current_level < 3:
            st.warning("Please enable Level 3 to access Voice Features.")
        else:
            st.markdown("### 🎤 Voice Interaction Mode")
            st.write("Ready to receive voice input...")

if __name__ == "__main__":
    main()