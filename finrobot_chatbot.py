import os
import json
import streamlit as st
import autogen
from finrobot.agents.workflow import SingleAssistant
from finrobot.utils import get_current_date
from datetime import datetime

# Set up the page configuration
st.set_page_config(
    page_title="FinRobot Chatbot",
    page_icon="💰",
    layout="wide",
)

# Set up styles
st.markdown("""
<style>
.main-title {
    font-size: 3rem;
    color: #1E88E5;
    text-align: center;
    margin-bottom: 1rem;
}
.subtitle {
    font-size: 1.2rem;
    color: #555;
    text-align: center;
    margin-bottom: 2rem;
}
.chat-container {
    background-color: #f9f9f9;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.user-message {
    background-color: #E3F2FD;
    padding: 10px 15px;
    border-radius: 10px;
    margin: 10px 0;
    text-align: right;
    color: #1565C0;
}
.bot-message {
    background-color: #F5F5F5;
    padding: 10px 15px;
    border-radius: 10px;
    margin: 10px 0;
    color: #333;
}
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<div class="main-title">FinRobot Chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your AI Finance Assistant</div>', unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
    
if 'finrobot_agent' not in st.session_state:
    st.session_state.finrobot_agent = None

# Sidebar for agent selection
with st.sidebar:
    st.title("Settings")
    
    # Agent selection
    agent_options = [
        "Expert_Investor", 
        "Market_Analyst", 
        "Financial_Analyst",
        "Data_Analyst",
        "Artificial_Intelligence_Engineer"
    ]
    
    selected_agent = st.selectbox(
        "Select your financial agent:",
        agent_options,
        index=0
    )
    
    # Temperature slider
    temperature = st.slider(
        "Response Creativity:", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.1,
        help="Lower values make responses more focused and deterministic. Higher values make responses more creative and varied."
    )
    
    # Initialize agent button
    init_agent = st.button("Initialize Agent")
    
    if init_agent:
        try:
            st.session_state.messages = []
            
            # Set up your OpenAI config using Streamlit secrets
            api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else ""
            os.environ["OPENAI_API_KEY"] = api_key
            
            # Create a config list programmatically instead of from file
            config_list = [
                {
                    "model": "gpt-4-0125-preview",
                    "api_key": api_key
                }
            ]
            
            llm_config = {
                "config_list": config_list,
                "temperature": temperature
            }
            
            st.session_state.finrobot_agent = SingleAssistant(
                agent_config=selected_agent,
                llm_config=llm_config,
                human_input_mode="NEVER",
                code_execution_config={
                    "work_dir": "coding",
                    "use_docker": False,
                }
            )
            
            st.session_state.agent_initialized = True
            st.success(f"{selected_agent} initialized successfully!")
            
        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")

# Function to collect chat history
class ChatHistory:
    def __init__(self):
        self.history = []
        
    def append(self, role, message):
        self.history.append({"role": role, "content": message})
        
    def get_all(self):
        return self.history

# Custom user proxy agent to capture responses
class CustomUserProxy(autogen.UserProxyAgent):
    def __init__(self, chat_history, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_history = chat_history
        
    def receive(self, message, sender, config=None):
        self.chat_history.append("assistant", message["content"])
        return super().receive(message, sender, config)

# Display chat messages
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat input
with st.container():
    user_input = st.text_area("Ask your financial question:", height=100)
    send_button = st.button("Send")
    
    if send_button and user_input:
        if not st.session_state.agent_initialized:
            st.warning("Please initialize an agent first!")
        else:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Create a chat history collector
            chat_history = ChatHistory()
            chat_history.append("user", user_input)
            
            try:
                # Use a placeholder to show typing indicator
                with st.spinner("FinRobot is thinking..."):
                    # Custom callback to capture response
                    def add_message_callback(message):
                        st.session_state.messages.append({"role": "assistant", "content": message})
                    
                    # Create a custom user proxy that will record the chat history
                    custom_user_proxy = CustomUserProxy(
                        chat_history=chat_history,
                        name="User_Proxy",
                        human_input_mode="NEVER"
                    )
                    
                    # Replace the user proxy in the agent
                    original_user_proxy = st.session_state.finrobot_agent.user_proxy
                    st.session_state.finrobot_agent.user_proxy = custom_user_proxy
                    st.session_state.finrobot_agent.assistant.register_proxy(custom_user_proxy)
                    
                    # Initiate chat with the agent
                    response = custom_user_proxy.initiate_chat(
                        st.session_state.finrobot_agent.assistant,
                        message=user_input
                    )
                    
                    # Add assistant's response to chat
                    full_response = ""
                    for msg in chat_history.get_all():
                        if msg["role"] == "assistant":
                            full_response = msg["content"]
                            break
                    
                    if full_response:
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    # Reset the agent for next conversation
                    st.session_state.finrobot_agent.reset()
                    
                    # Restore original user proxy
                    st.session_state.finrobot_agent.user_proxy = original_user_proxy
                    st.session_state.finrobot_agent.assistant.register_proxy(original_user_proxy)
                
                # Rerun to update the chat display
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {str(e)}"})

# Add footer
st.markdown("""
---
<div style="text-align: center; color: #888; padding: 20px;">
    Built with FinRobot | Current Date: {current_date}
</div>
""".format(current_date=get_current_date()), unsafe_allow_html=True)