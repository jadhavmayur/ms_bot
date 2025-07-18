import streamlit as st
import os
from dotenv import load_dotenv
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import weaviate, os, time
# Custom functions (replace with actual logic)
from helper import retriever_weaviate, parse_docs_weaviate, build_prompt_weaviate

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv('openai_key')
weaviate_api_key = os.getenv('weaviate_api_key')
URL = os.getenv('weaviate_URL')


# UI Setup - Logo and Header
col1, col2 = st.columns([1, 3])

with col2:
    st.markdown(
        """
        <div style='display: flex; align-items: center; height: 20%; padding-top: 0px; padding-bottom: 20px;justify-content: flex-start;'>
            <h2 style='margin-right:20px; color:#27a9e1; font-size: 50px;'>Mindgate AI Bot</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


# Build RAG Chain
chain_with_sources = {
    "context": retriever_weaviate | RunnableLambda(parse_docs_weaviate),
    "question": RunnablePassthrough(),
} | RunnablePassthrough().assign(
    response=(
        RunnableLambda(build_prompt_weaviate)
        | ChatOpenAI(model="gpt-4o-mini")
        | StrOutputParser()
    )
)




# Session State Setup
# if 'messages' not in st.session_state:
#     st.session_state.messages = []

# Session State Setup
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": """I'm here to assist you! If you have any specific questions or need information related to our services or information about digital payments, feel free to ask!"""}]

# # ✅ Debug: Show messages in sidebar for clarity
# with st.sidebar:
#     st.write("🛠 Debug Session Messages:")
#     st.write(st.session_state.messages)


# Display existing conversation history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])


# User Input
prompt = st.chat_input("Type your message...")

if prompt:
    # Append user's message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Render user's message immediately
    with st.chat_message("user"):
        st.write(prompt)

    # Generate assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = chain_with_sources.invoke(prompt.lower())  # Your RAG pipeline
                print(resp)
                response = resp['response']
            except Exception as e:
                response = "The Chat API is currently unavailable; please try again later."
                st.error(str(e))

            # Display assistant's message
            st.write(response)
    # Append assistant's response
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
