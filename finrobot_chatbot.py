import os
import streamlit as st
import autogen
# Ensure finrobot is installed: pip install finrobot
try:
    from finrobot.agents.workflow import SingleAssistant
    from finrobot.utils import get_current_date
except ImportError:
    st.error("Error: finrobot library not found. Please install it using 'pip install finrobot'")
    st.stop() # Stop the script if finrobot is not installed

from typing import Any, Dict, List, Optional, Union
import sys
import io

# Create a custom assistant class that doesn't print to terminal
class StreamlitAssistant(SingleAssistant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_response(self, message: str):
        """Get direct response from the assistant without terminal output"""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        final_response_content = "Error: Could not retrieve response from agent." # Default error message

        try:
            # Initiate the chat - this returns a ChatResult object
            # Setting message_box=False can sometimes prevent the entire conversation history
            # from being returned in the summary, focusing on the final answer.
            chat_result = self.user_proxy.initiate_chat(
                self.assistant,
                message=message,
                message_box=False # Added this for potentially cleaner output
            )

            # Reset the agents for next chat (good practice)
            self.reset()

            # Extract the final response content from the ChatResult object.
            # The 'summary' attribute often contains the final response text.
            if hasattr(chat_result, 'summary') and chat_result.summary is not None:
                final_response_content = chat_result.summary
            else:
                 # Fallback: If summary is not available, try to find the last message
                 # from the assistant in the chat history.
                 # Assuming the assistant's name is available
                 assistant_name = self.assistant.name if hasattr(self.assistant, 'name') else 'assistant'

                 if hasattr(chat_result, 'chat_history') and isinstance(chat_result.chat_history, list):
                      # Iterate backwards through the history to find the last assistant message
                      for msg in reversed(chat_result.chat_history):
                          # Check for 'role' or 'name' to identify the assistant's message
                          # Also check for 'content' key before accessing it
                          if (msg.get('role') == 'assistant' or msg.get('name') == assistant_name) and msg.get('content') is not None:
                              final_response_content = msg.get('content', 'No content found in message.')
                              # Consider breaking here if only the absolute last message is needed
                              # If you need all assistant messages in the final response, you'd concatenate
                              break # Assuming we want the very last assistant message


                 # Added a check for chat_history being a dictionary with a messages list key
                 elif hasattr(chat_result, 'chat_history') and isinstance(chat_result.chat_history, dict) and isinstance(chat_result.chat_history.get('messages'), list):
                     messages_list = chat_result.chat_history['messages']
                     for msg in reversed(messages_list):
                          if (msg.get('role') == 'assistant' or msg.get('name') == assistant_name) and msg.get('content') is not None:
                              final_response_content = msg.get('content', 'No content found in message.')
                              break


            # If after all attempts, content is still the default error message, refine it
            if final_response_content == "Error: Could not retrieve response from agent.":
                 final_response_content += " The agent did not provide a readable response."

            return final_response_content

        except Exception as e:
            st.error(f"Error during chat initiation: {e}")
            # Return a specific error message related to the exception
            return f"An error occurred while processing your request: {e}"
        finally:
            # Restore stdout
            sys.stdout = old_stdout

# --- Streamlit App Structure ---

# Page config
st.set_page_config(page_title="FinRobot Chatbot", page_icon="💰", layout="wide")

# Title
st.title("💬 FinRobot Chatbot")
st.markdown("Ask me anything about finance!")

# Sidebar for Settings
with st.sidebar:
    st.header("Settings")

    # Input for OpenAI API Key
    # Using st.text_input for direct input, secrets management is also an option
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        # Optionally verify the API key here if needed

    agent_options = [
        "Expert_Investor",
        "Market_Analyst",
        "Financial_Analyst",
        "Data_Analyst",
        "Artificial_Intelligence_Engineer"
    ]
    selected_agent = st.selectbox("Choose Agent", agent_options, key="agent_select") # Added unique key

    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.7, 0.1, key="temperature_slider") # Added unique key

    # Initialize Button
    # Adding a key to the button can help if there are multiple forms/buttons
    initialize = st.button("Initialize Agent", key="initialize_button")

# Initialize FinRobot agent
# Agent initialization should only happen once or when settings change
if initialize or ("agent" in st.session_state and st.session_state.agent_config != selected_agent) or ("agent" in st.session_state and st.session_state.temperature != temperature):
    if not api_key and "OPENAI_API_KEY" not in os.environ:
        st.warning("Please enter your OpenAI API Key to initialize the agent.")
    else:
        try:
            # Get API key from input or environment
            current_api_key = api_key if api_key else os.environ.get("OPENAI_API_KEY")

            if not current_api_key:
                 st.error("OpenAI API Key is not provided.")
                 if "agent" in st.session_state:
                      del st.session_state.agent # Clear agent if key is missing
                 st.session_state.agent_initialized = False
            else:
                config_list = [
                    {
                        "model": "gpt-3.5-turbo", # Or "gpt-4" etc.
                        "api_key": current_api_key
                    }
                ]

                llm_config = {
                    "config_list": config_list,
                    "temperature": temperature,
                    # Add other LLM config parameters if needed
                }

                # Initialize the StreamlitAssistant
                agent = StreamlitAssistant(
                    agent_config=selected_agent,
                    llm_config=llm_config,
                    human_input_mode="NEVER", # Set to NEVER for a non-interactive chatbot
                    code_execution_config={
                        "work_dir": "coding", # Directory for code execution
                        "use_docker": False, # Set to True if Docker is preferred/available
                    }
                )

                st.session_state.agent = agent
                st.session_state.agent_config = selected_agent # Store config to detect changes
                st.session_state.temperature = temperature # Store temperature to detect changes
                st.session_state.agent_initialized = True # Flag for successful initialization
                st.success(f"{selected_agent} initialized successfully! Ready to chat.")

        except Exception as e:
            st.error(f"Initialization failed: {str(e)}")
            st.session_state.agent_initialized = False
            # Clear agent from state on failure
            if "agent" in st.session_state:
                del st.session_state.agent

# Initialize messages history in session state if not already present or if agent changes
if "messages" not in st.session_state or (st.session_state.get("agent_config_changed", False)):
     st.session_state.messages = []
     if st.session_state.get("agent_config_changed", False):
          st.session_state.agent_config_changed = False # Reset the flag


# Display chat history in the UI
st.subheader("Conversation")
chat_container = st.container()
with chat_container:
    # Use st.empty() to create a placeholder for messages and update it
    # This can sometimes be more efficient for displaying dynamic content than rerunning the whole loop
    # However, the current loop based on session_state.messages is more standard and often sufficient.
    # Let's stick to the standard loop as it was mostly working.

    for message in st.session_state.messages:
        # Ensure message has 'role' and 'content' keys and 'content' is a string
        if isinstance(message, dict) and "role" in message and "content" in message and isinstance(message["content"], str):
             if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])
             else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(message["content"])
        else:
            # Display a warning or just skip messages with unexpected format
            st.warning(f"Skipping message with unexpected format or content type: {message}")


# Input area for user prompt
# Only show the chat input if the agent is initialized
if st.session_state.get("agent_initialized", False):
    user_prompt = st.chat_input("Ask FinRobot something...")

    if user_prompt:
        # Add user message to history immediately
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        # *** No st.rerun() here - rely on the next block to process and rerun ***

# Process messages after rerun if there's a pending user message
# This block runs after the script reruns due to a new user message being added to session_state
# Check if the last message is from the user AND the agent is initialized AND we are not already generating a response
if st.session_state.get("agent_initialized", False) and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # Use a state variable to prevent triggering response generation multiple times
    if "generating_response" not in st.session_state or not st.session_state.generating_response:
        st.session_state.generating_response = True # Set flag to indicate response generation is in progress
        try:
            # Show a spinner while processing
            with st.spinner("FinRobot is thinking..."):
                # Get the last user message
                last_user_message = st.session_state.messages[-1]["content"]

                # Use our custom method to get the direct response from the agent
                reply = st.session_state.agent.get_response(message=last_user_message)

                # Add assistant's reply to the messages
                # Ensure the reply is treated as a string before appending
                st.session_state.messages.append({"role": "assistant", "content": str(reply)})

            st.session_state.generating_response = False # Reset flag

            # Force a rerun to display the response in the chat UI
            st.rerun()
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            # Append the error to the chat history so the user sees it in context
            st.session_state.messages.append({"role": "assistant", "content": f"Error: Could not generate response. {str(e)}"})
            st.session_state.generating_response = False # Reset flag on error
            st.rerun() # Rerun to display the error message in chat

else:
    # Display a message if the agent is not initialized and there are no messages
    if not st.session_state.get("agent_initialized", False) and not st.session_state.messages:
        st.info("Please initialize the agent in the sidebar to start chatting.")

    # Reset generating_response flag if the last message is not from the user (e.g., assistant just replied)
    if "generating_response" in st.session_state and st.session_state.generating_response and st.session_state.messages and st.session_state.messages[-1]["role"] != "user":
         st.session_state.generating_response = False


# Footer (removed as requested)
# st.markdown("---")
# st.caption(f"Built with ❤️ | Current Date: {get_current_date()}")