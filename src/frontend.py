import streamlit as st
from chatbot_graph import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

#util functions
def generate_thread_id():
    thrread_id=uuid.uuid4()
    return thrread_id

def reset_chat():
    thread_id=generate_thread_id()
    st.session_state['thread_id']=thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history']=[]

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state=chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

def first_question(thread_id):
    state=chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    messages = state.values.get('messages', [])
    # Handle empty threads gracefully
    if not messages:
        return "New Chat"  # or return "No messages yet"
    # Find the first human (user) message
    for msg in messages:
        if isinstance(msg, HumanMessage):
            return msg.content

    return "New Chat"  # Fallback if no human message is found

#Session Setup
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state: # creating unique thread id for each session 
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

#Sidebar UI
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('Conversations')
for thread_id in st.session_state['chat_threads'][::-1]:
    first_msg = first_question(thread_id)
    label = first_msg[:30] + "..." if len(first_msg) > 40 else first_msg
    if st.sidebar.button(str(label),key=str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages=load_conversation(thread_id)

        temp_message=[]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_message.append({'role':role,'content':msg.content})
        
        st.session_state['message_history']=temp_message
#Main UI
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input("Type your message here...")
if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message("user"):
        st.text(user_input)
    
    #CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    #LangSmith Config
    CONFIG={
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata":{"thread_id": st.session_state["thread_id"]}, # added to langsmith metadata
        "run_name": "Chatbot Run"
    }
    # streaming response
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}
        
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,  
                stream_mode='messages', 
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk, AIMessage): # only yield AIMessage content
                    yield message_chunk.content
        
        ai_message = st.write_stream(ai_only_stream())
        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
        

    st.session_state['message_history'].append({'role':'assistant','content':ai_message})
    


