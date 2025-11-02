import streamlit as st
import sqlite3
import os
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default system prompt for general assistance
DEFAULT_SYSTEM_PROMPT = """You are a helpful, friendly, and knowledgeable AI assistant. You provide accurate,
thoughtful, and well-structured responses to user questions across various topics. You are patient, professional,
and always aim to give clear explanations. When you don't know something, you honestly admit it rather than
making up information."""

# Database setup
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    # Create chats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def create_new_chat():
    """Create a new chat session"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    chat_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    cursor.execute('INSERT INTO chats (name) VALUES (?)', (chat_name,))
    chat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return chat_id

def get_all_chats():
    """Retrieve all chat sessions"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, created_at FROM chats ORDER BY created_at DESC')
    chats = cursor.fetchall()

    conn.close()
    return chats

def delete_chat(chat_id):
    """Delete a chat session and its messages"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM chats WHERE id = ?', (chat_id,))

    conn.commit()
    conn.close()

def save_message(chat_id, role, content):
    """Save a message to the database"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)',
        (chat_id, role, content)
    )

    conn.commit()
    conn.close()

def load_messages(chat_id):
    """Load all messages for a specific chat"""
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp',
        (chat_id,)
    )
    messages = cursor.fetchall()

    conn.close()
    return [{"role": role, "content": content} for role, content in messages]

def get_azure_openai_client():
    """Initialize Azure OpenAI client with error handling"""
    try:
        # Get environment variables
        endpoint = os.getenv("AZURE_OPENAI_CHAT_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_CHAT_API_VERSION")

        # Validate all required variables are present
        if not endpoint:
            st.error("❌ AZURE_OPENAI_CHAT_ENDPOINT not found in environment variables")
            st.info("Please add it to your .env file")
            st.stop()

        if not api_key:
            st.error("❌ AZURE_OPENAI_CHAT_API_KEY not found in environment variables")
            st.info("Please add it to your .env file")
            st.stop()

        if not api_version:
            st.error("❌ AZURE_OPENAI_CHAT_API_VERSION not found in environment variables")
            st.info("Please add it to your .env file")
            st.stop()

        # Initialize and return client
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )

    except Exception as e:
        st.error(f"❌ Error initializing Azure OpenAI client: {str(e)}")
        st.stop()

def stream_chat_response(client, messages, deployment_name, system_prompt):
    """Stream response from Azure OpenAI with error handling"""
    try:
        # Prepend system message to the conversation
        messages_with_system = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages_with_system,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    yield delta.content

    except Exception as e:
        st.error(f"❌ Error generating response: {str(e)}")
        yield ""

# Streamlit app configuration
st.set_page_config(
    page_title="Perfect AI Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stButton button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database
init_database()

# Initialize session state
if 'current_chat_id' not in st.session_state:
    chats = get_all_chats()
    if chats:
        st.session_state.current_chat_id = chats[0][0]
    else:
        st.session_state.current_chat_id = create_new_chat()

if 'messages' not in st.session_state:
    st.session_state.messages = load_messages(st.session_state.current_chat_id)

if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT

# Sidebar - Chat Management
with st.sidebar:
    st.title("💬 Chat Sessions")

    # New Chat button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_chat_id = create_new_chat()
        st.session_state.current_chat_id = new_chat_id
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Display all chats
    chats = get_all_chats()

    if chats:
        st.subheader("Your Conversations")

        for chat_id, chat_name, created_at in chats:
            col1, col2 = st.columns([4, 1])

            with col1:
                # Chat button - highlight current chat
                button_type = "primary" if chat_id == st.session_state.current_chat_id else "secondary"
                if st.button(
                    chat_name,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.messages = load_messages(chat_id)
                    st.rerun()

            with col2:
                # Delete button
                if st.button("🗑️", key=f"delete_{chat_id}", help="Delete this chat"):
                    delete_chat(chat_id)

                    # Switch to another chat or create new one
                    remaining_chats = get_all_chats()
                    if remaining_chats:
                        st.session_state.current_chat_id = remaining_chats[0][0]
                        st.session_state.messages = load_messages(remaining_chats[0][0])
                    else:
                        st.session_state.current_chat_id = create_new_chat()
                        st.session_state.messages = []

                    st.rerun()
    else:
        st.info("No chats yet. Start a new conversation!")

    st.divider()

    # System Prompt Configuration
    with st.expander("⚙️ System Prompt Settings"):
        st.markdown("**Customize AI Behavior**")
        st.caption("Define how the AI assistant should respond")

        # Predefined templates
        prompt_template = st.selectbox(
            "Select Template",
            [
                "General Assistant",
                "Healthcare Professional",
                "Physiotherapy Expert",
                "Software Developer",
                "Business Consultant",
                "Education Tutor",
            ]
        )

        # # System prompt templates
        # templates = {
        #     "General Assistant": DEFAULT_SYSTEM_PROMPT,
        #     "Healthcare Professional": """You are a knowledgeable healthcare professional AI assistant. You provide
        #     accurate medical information, health advice, and wellness guidance. You always remind users to consult
        #     with qualified healthcare providers for serious medical concerns. You are empathetic, clear, and focus
        #     on evidence-based information.""",
        #     "Physiotherapy Expert": """You are an expert physiotherapy AI assistant. You provide guidance on
        #     physical therapy exercises, injury prevention, rehabilitation techniques, and musculoskeletal health.
        #     You explain exercises clearly with safety precautions and always recommend consulting a licensed
        #     physiotherapist for personalized treatment plans.""",
        #     "Software Developer": """You are an experienced software developer AI assistant. You help with coding
        #     problems, debug issues, explain programming concepts, and provide best practices for software development.
        #     You write clean, well-commented code and explain technical concepts in an accessible way.""",
        #     "Business Consultant": """You are a professional business consultant AI assistant. You provide strategic
        #     advice on business planning, management, marketing, finance, and organizational development. You offer
        #     practical solutions and insights based on business best practices.""",
        #     "Education Tutor": """You are a patient and knowledgeable education tutor AI assistant. You help students
        #     understand complex topics, break down difficult concepts, and provide learning strategies. You adapt your
        #     explanations to different learning styles and encourage critical thinking.""",
        # }

        # # Update system prompt based on selection
        # if prompt_template == "Custom":
        #     custom_prompt = st.text_area(
        #         "Enter Custom System Prompt",
        #         value=st.session_state.system_prompt,
        #         height=150,
        #         help="Define how you want the AI to behave"
        #     )
        #     if st.button("Apply Custom Prompt"):
        # #         st.session_state.system_prompt = custom_prompt
        # #         st.success("✅ System prompt updated!")
        # else:
        #     st.session_state.system_prompt = templates[prompt_template]
        #     st.info(f"Using: {prompt_template}")

    st.divider()
    st.caption("Powered by Azure OpenAI")

# Main chat interface
st.title("🤖 Perfect AI Assistant")
st.markdown("##### 💡 Customize the system prompt to make the AI specialize in any field.")
st.caption("Ask me anything - I'm here to help!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Validate deployment name
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    if not deployment_name:
        st.error("❌ AZURE_OPENAI_CHAT_DEPLOYMENT not found in environment variables")
        st.info("Please add it to your .env file")
        st.stop()

    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.current_chat_id, "user", prompt)

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get Azure OpenAI client
    client = get_azure_openai_client()

    # Generate and stream assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # Stream the response with system prompt
            for chunk in stream_chat_response(
                client,
                st.session_state.messages,
                deployment_name,
                st.session_state.system_prompt
            ):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")

            # Remove cursor and display final response
            response_placeholder.markdown(full_response)

            # Save assistant message if response was generated
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_message(st.session_state.current_chat_id, "assistant", full_response)
            else:
                st.warning("No response generated. Please try again.")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("Please check your Azure OpenAI configuration and try again.")
