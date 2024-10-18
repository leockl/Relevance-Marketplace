import streamlit as st
import requests
import json
import time
from streamlit_chat import message

def initialize_session_state():
    if 'users' not in st.session_state:
        st.session_state.users = {
            "Leo": {"password": "password1", "agents": []},
            "user2": {"password": "password2", "agents": []}
        }
    if 'marketplace_agents' not in st.session_state:
        st.session_state.marketplace_agents = [
            {
                "name": "Video Podcast Coordinator",
                "description": "You run a team of agents who convert audio podcasts into video podcasts",
                "agent_id": "e70c7d5d-9d66-454e-b98b-2f3a7d4ff05d",
                "api_key": "728755c94f7d-4a2f-b067-938b10aee7ec:sk-MDk5NTUxNWEtYjlhZC00NWNlLWEzYzMtYmQ3YWY5MWQ5MDhl",
                "owner": "Samantha"
            },
            {
                "name": "Audio Podcast Coordinator",
                "description": "You run a team of agents who convert text into audio podcasts",
                "agent_id": "e0111c18-199f-4e72-98a8-77c7838fe6ba",
                "api_key": "728755c94f7d-4a2f-b067-938b10aee7ec:sk-NDlkOGI5MjAtOWVlZC00Mjc0LWFmMmItZjAyMDhjMmMwNmIw",
                "owner": "Adam"
            }
        ]
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    if 'chat_agent' not in st.session_state:
        st.session_state.chat_agent = None
    if 'conversations' not in st.session_state:
        st.session_state.conversations = {}

def authenticate(username, password):
    return username in st.session_state.users and st.session_state.users[username]["password"] == password

def register_user(username, password):
    if username in st.session_state.users:
        return False
    st.session_state.users[username] = {"password": password, "agents": []}
    return True

def add_agent(username, agent_name, description, agent_id, api_key):
    new_agent = {
        "name": agent_name,
        "description": description,
        "agent_id": agent_id,
        "api_key": api_key,
        "owner": username
    }
    st.session_state.users[username]["agents"].append(new_agent)
    st.session_state.marketplace_agents.append(new_agent)

def trigger_agent(agent_id, api_key, message_content, conversation_id=None):
    base_url = "https://api-f1db6c.stack.tryrelevance.com/latest/"
    headers = {"Content-Type": "application/json", "Authorization": api_key}
    
    data = {
        "message": {"role": "user", "content": message_content},
        "agent_id": agent_id
    }
    
    if conversation_id:
        data["conversation_id"] = conversation_id
    
    try:
        response = requests.post(f"{base_url}agents/trigger", headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error triggering agent: {str(e)}")
        if response:
            st.error(f"Response content: {response.text}")
        return None

def poll_job(job, api_key):
    if not job:
        return None

    base_url = "https://api-f1db6c.stack.tryrelevance.com/latest/"
    headers = {"Authorization": api_key}
    studio_id = job.get("job_info", {}).get("studio_id")
    job_id = job.get("job_info", {}).get("job_id")
    
    if not studio_id or not job_id:
        st.error("Invalid job information")
        st.json(job)
        return None

    max_retries = 10
    for _ in range(max_retries):
        try:
            response = requests.get(f"{base_url}studios/{studio_id}/async_poll/{job_id}", headers=headers)
            response.raise_for_status()
            status = response.json()
            
            if status.get('type') == 'complete' and status.get('updates'):
                return status
            
            time.sleep(3)
        except requests.RequestException as e:
            st.error(f"Error polling job: {str(e)}")
            if response:
                st.error(f"Response content: {response.text}")
            return None

    st.warning("Max retries reached. The agent may still be processing.")
    return None

def extract_ai_response(status):
    if status and 'updates' in status:
        for update in status['updates']:
            if update.get('type') == 'chain-success':
                output = update.get('output', {}).get('output', {})
                if 'history_items' in output and output['history_items']:
                    return output['history_items'][-1].get('message', "")
    return "Sorry, I couldn't generate a response."

def main_page():
    # Custom CSS for the blue title, centered login form, and green buttons
    st.markdown("""
    <style>
    .blue-title {
        color: #4664F0;
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        color: #666666;
        font-size: 16px;
        text-align: center;
        margin-bottom: 30px;
    }
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    .stButton>button {
        width: 200px;
    }
    .green-button {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    div[data-testid="stSidebarNav"] ul {
        max-height: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display the blue title and subtitle
    st.markdown('<p class="blue-title">Relevance Marketplace</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Buy and sell AI agents</p>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        # Center-align the login form
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            username = st.text_input("Username", key="username_input")
            password = st.text_input("Password", type="password", key="password_input")
            
            if st.button("Login", key="login_button"):
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
            
            if st.button("Register", key="register_button"):
                if register_user(username, password):
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error("Username already exists. Please choose a different username.")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        if st.sidebar.button("Logout", key="logout_button", on_click=lambda: setattr(st.session_state, 'logged_in', False)):
            st.experimental_rerun()
        
        menu = ["Available Agents", "Add New Agent", "My Agents"]
        choice = st.sidebar.selectbox("Menu", menu)
        
        if choice == "Available Agents":
            st.subheader("Available Agents")
            
            # CSS for the agent boxes and green hire button
            st.markdown("""
            <style>
            .agent-box {
                background-color: #f0f2f6;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .agent-name {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .agent-owner {
                font-size: 14px;
                color: #666;
                margin-bottom: 10px;
            }
            .agent-description {
                font-size: 14px;
                margin-bottom: 15px;
            }
            .stButton > button {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            .stButton > button:hover {
                background-color: #45a049;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create a 2-column layout
            col1, col2 = st.columns(2)
            
            for i, agent in enumerate(st.session_state.marketplace_agents):
                with col1 if i % 2 == 0 else col2:
                    st.markdown(f"""
                    <div class="agent-box">
                        <div class="agent-name">{agent['name']}</div>
                        <div class="agent-owner">By {agent['owner']}</div>
                        <div class="agent-description">{agent['description']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Hire", key=f"hire_{agent['name']}"):
                        st.session_state.chat_agent = agent
                        st.session_state.page = 'chat'
                        # Clear the conversation for this agent
                        st.session_state.conversations[agent['agent_id']] = []
                        st.experimental_rerun()
        
        elif choice == "Add New Agent":
            st.subheader("Add New Agent")
            agent_name = st.text_input("Agent Name")
            description = st.text_area("Description")
            agent_id = st.text_input("Agent ID")
            api_key = st.text_input("API Key", type="password")
            
            if st.button("Add Agent", key="add_agent_button", help="Click to add the new agent"):
                if agent_name and description and agent_id and api_key:
                    add_agent(st.session_state.username, agent_name, description, agent_id, api_key)
                    st.success("Agent added successfully!")
                else:
                    st.error("Please fill in all fields.")

        elif choice == "My Agents":
            st.subheader("My Agents")
            user_agents = st.session_state.users[st.session_state.username]["agents"]
            for agent in user_agents:
                st.write(f"**{agent['name']}**")
                st.write(agent['description'])

    # Apply green color to specific buttons
    st.markdown("""
    <style>
    .stButton>button[data-testid="logout_button"],
    .stButton>button[data-testid="add_agent_button"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

def chat_page():
    agent = st.session_state.chat_agent
    
    # Create a container for the title and back button
    header_container = st.container()
    with header_container:
        st.title(f"Chat with {agent['name']}")
        st.button("Back to Main Page", on_click=lambda: setattr(st.session_state, 'page', 'main'))
    
    # Add some space between the header and the chat
    st.markdown("---")
    
    if agent['agent_id'] not in st.session_state.conversations:
        st.session_state.conversations[agent['agent_id']] = []
    
    conversation = st.session_state.conversations[agent['agent_id']]
    
    # Create a container for the chat messages
    chat_container = st.container()
    
    # Create a container for the user input
    input_container = st.container()
    
    with chat_container:
        for message in conversation:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    with input_container:
        user_input = st.chat_input("Your message:")
        
        if user_input:
            conversation.append({"role": "user", "content": user_input})
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_input)
            
                with st.chat_message("assistant"):
                    with st.spinner("Agent is thinking..."):
                        job = trigger_agent(agent['agent_id'], agent['api_key'], user_input)
                        if job:
                            status = poll_job(job, agent['api_key'])
                            if status:
                                agent_response = extract_ai_response(status)
                                conversation.append({"role": "assistant", "content": agent_response})
                                st.write(agent_response)
                            else:
                                st.error("Failed to get a response from the agent.")
                        else:
                            st.error("Failed to trigger the agent.")

def main():
    st.set_page_config(page_title="Relevance Marketplace", layout="wide")
    initialize_session_state()

    if st.session_state.page == 'main':
        main_page()
    elif st.session_state.page == 'chat':
        chat_page()

if __name__ == "__main__":
    main()