import os
import json
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import weaviate, os, time
from weaviate.classes.init import Auth
import imghdr
import base64
from langchain_openai import ChatOpenAI
from typing import List
from langchain_core.prompts.prompt import PromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

### Load the keys
os.environ["OPENAI_API_KEY"]=os.getenv('openai_key')
weaviate_api_key=os.getenv('weaviate_api_key')
URL=os.getenv('weaviate_URL')

### text processing
def parse_docs_weaviate(docs):
    """Split base64-encoded images and texts"""
    b64 = []
    text = []
    for doc in docs:
        if doc.get('page_number'):
            new_text=f"page:{doc['page']}\n page_content:{doc['page_content']}\n page_number:{doc['page_number']}"
            text.append(new_text)
        else:
            new_text=f"page:{doc['page']}\n page_content:{doc['page_content']}"
            text.append(new_text)
    return {"images": b64, "texts": text}
    # - Give relevent output which is most possible answer.
    # - Give All possiblle solution which is relatable.
    # * Generate solution in simple language.
def build_prompt_weaviate(kwargs):

    docs_by_type = kwargs["context"]
    user_question = kwargs["question"]
    
    context_text = ""
    if len(docs_by_type["texts"]) > 0:
        for text_element in docs_by_type["texts"]:
            # print("text_element: ",text_element.page_content)
            # print("---"*50)
            context_text += text_element
            # print("---"*50)

    # construct prompt with context (including images)
    prompt_template = f"""Role: mindagate solution pvt ltd .
    ----
    Steps to generate answer:
    * Analyse the Context text.
    * Find the right text from Context text and seggregate the text which related with Question.
    * generate relevent solution for user query by analysing seggregated text.
    ---
    note:
    * generate relevent anwer.
    * Strictly Avoid generate irrelevant answer.  
    ---
    note for context text:
    * Context text also have text which is not relevent to user question.
    * Strictly Avoid give these irrelevent solution from context text.
    * Strictly generate answer base on context_text provide.
    ---
    Avoid generation:
    * if query is not relevent with context text then avoid generate text with wrong answer.
    
    ---
    Context: {context_text}
    Question: {user_question}
    """

    prompt_content = [{"type": "text", "text": prompt_template}]
    

    if len(docs_by_type["images"]) > 0:
        for image in docs_by_type["images"]:
            # Use imghdr to detect the image type
            img_type=imghdr.what(None, base64.b64decode(image['image']))
            prompt_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{img_type};base64,{image['image']}"},
                }
            )

    return ChatPromptTemplate.from_messages(
        [
            HumanMessage(content=prompt_content),
        ]
    )

# Weaviate connection using OAuth2 Bearer token
client_1 = weaviate.connect_to_wcs(
    cluster_url=URL,
    auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
    headers={
        'X-OpenAI-Api-Key':os.getenv('openai_key')  # Optional, if you're using Google's embedding models
    }
)

collection_1 = client_1.collections.get("mind")

def retriever_weaviate(query):
    response_1 = collection_1.query.hybrid(
    query=query,
    alpha=0.25,
    #fusion_type=HybridFusion.RELATIVE_SCORE,
    limit=10)

    doc=[]
    for o in response_1.objects:
        doc.append(o.properties)
    return doc

# print(retriever_weaviate("hello"))