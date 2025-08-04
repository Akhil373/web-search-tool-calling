from typing import List, Dict
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
import requests
from dotenv import load_dotenv
import os
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import BeautifulSoupTransformer, MarkdownifyTransformer
from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import logging
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

google_api_key = os.getenv("GOOGLE_SEARCH_API")
cse_id = os.getenv("CSE_ID")
gemini_api_key = os.getenv("GEMINI_API_KEY")

llm = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google-genai",
    api_key=gemini_api_key
)

def web_search(search_item: str, search_depth: int = 10, site_filter: str | None = None):
    """
    Perform Google search and optionally filters specified site
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_item,
        "key": google_api_key,
        "cx": cse_id,
        "num": min(search_depth, 10)
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except requests.RequestException as e:
        print(f"An error occurred during web search: {e}")
        return set()

    if site_filter:
        items = [it for it in items if "link" in it and site_filter in it["link"]]

    problematic_urls = ['twitter.com', 'x.com']

    items = [item for item in items if "link" in item and not any(domain in item["link"].lower() for domain in problematic_urls)]

    return {item['link'] for item in items if 'link' in item}


@tool
async def retrieve_webpage_content(search_item: str) -> str:
    """
    Performs a web search for a given query and retrieves the summarized 
    content from the main article of each resulting URL. Use this to find
    recent information about people, events, or companies.
    """
    print(f"TOOL: Searching for '{search_item}'...")
    urls = web_search(search_item)
    
    if not urls:
        return "No URLs found from web search."

    urls_list = list(urls)
    loader = AsyncHtmlLoader(urls_list)
    docs = await loader.aload()

    
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed_bs = bs_transformer.transform_documents(
        docs, tags_to_extract=["main"]
    )

    md_transformer = MarkdownifyTransformer()
    converted_docs = md_transformer.transform_documents(docs_transformed_bs)
    
    output_str = ""
    for doc in converted_docs:
        output_str += f"Source: {doc.metadata.get('source', 'N/A')}\n\n"
        output_str += f"{doc.page_content}\n\n---\n\n"

    with open('web_results.md', 'w', encoding='utf-8') as f:
        f.write(output_str)
    return output_str


# async def summarize_web_content(search_item: str) -> str | None:
#     """
#     Performs web search and returns summary of all the web search results.
#     :param search_item:
#     :return:
#     """
#     print(f"TOOL: Retrieving content for '{search_item}' to summarize...")
#     retrieved_text = await retrieve_webpage_content(search_item)
#
#     if not retrieved_text:
#         return "Could not retrieve any content to summarize."
#
#     prompt_template = ChatPromptTemplate.from_messages([
#         ("system",
#          "You are an expert summarization engine. Your task is to create a concise, factual summary of the provided text. Extract all key points, names, dates, and figures accurately."),
#         ("human", "{text_to_summarize}")
#     ])
#
#     summarization_chain = prompt_template | summary_llm
#
#     try:
#         response = await summarization_chain.ainvoke({"text_to_summarize": retrieved_text})
#
#         with open('summary.md', 'w', encoding='utf-8') as f:
#             f.write(response.content)
#         return response.content
#     except Exception as e:
#         print(f'An error occurred during summarization: {e}')
#         return None

system_prompt="""
You are a helpful, meticulous, and adaptable research assistant. Your primary goal is to answer user questions accurately by synthesizing information from web search results. If the query does NOT require web search, just use your internet knowledge.

CRITICAL RULES:

* You MUST cite every piece of information you use from the provided sources.
* Citations must be in Markdown format, as numbered superscripts like [1], [2], etc.
* At the end of your response, you MUST provide a "Sources" section that lists the corresponding URLs for each number.
* Synthesize information from multiple sources into a coherent narrative. Do not just copy-paste sections.
* **Adjust your verbosity based on the quality and comprehensiveness of the retrieved web search results.**
    * **If the web search results are rich, detailed, and directly answer the user's query, provide a thorough and expansive answer.**
    * **If the web search results are sparse, lack direct answers, or are of low quality, acknowledge the limitations of the available information and provide a concise summary based only on what can be confidently extracted.**

EXAMPLE:

[CONTEXT FROM TOOL]

Source: https://science.nasa.gov/sky_color
The blue color of the sky is a result of a process called Rayleigh scattering. As sunlight, which is made up of many different colors, enters Earth’s atmosphere, it collides with gas molecules. The shorter wavelengths of light, like blue and violet, are scattered more easily and in all directions by these molecules than the longer wavelengths, like red and yellow.

Source: https://phys.edu/why-sunsets-are-red
While blue light is scattered across the sky during the day, at sunset, the sunlight has to pass through much more of the atmosphere to reach our eyes. This increased distance means that most of the blue light is scattered away from our line of sight. This allows the longer wavelengths, primarily red and orange, to pass through directly, which is why sunsets have their characteristic colors.

[FINAL ANSWER]

The sky appears blue due to a phenomenon known as Rayleigh scattering [1]. When sunlight enters the atmosphere, the shorter blue wavelengths are scattered more widely by gas molecules than other colors, filling the sky with a blue hue [1].

This same process explains why sunsets often appear red. At sunset, the sun's light travels a longer path through the atmosphere, which scatters most of the blue light away from our view. This allows the remaining longer wavelengths, like red and orange, to become visible [2].

Sources

[1] https://science.nasa.gov/sky_color
[2] https://phys.edu/why-sunsets-are-red
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

tools = [retrieve_webpage_content]


conversation_history: Dict[str, List[BaseMessage]] = {}

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=3
)


class PromptRequest(BaseModel):
    prompt: str
    conversation_id: str | None = None


app = FastAPI()
router = APIRouter()

origins = [
    "http://localhost:5173",
    "http://localhost",
    "https://web-query.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['*']
)

def get_conversation_history(conversation_id: str) -> List[BaseMessage]:
    """Get existing conversation history or create new one"""
    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = []
    return conversation_history[conversation_id]

async def stream_tokens(user_input: str, conversation_id: str):
    chat_history = get_conversation_history(conversation_id)
    
    agent_input = {
        "input": user_input,
        "chat_history": chat_history
    }
    
    full_response = ""
    
    async for event in agent_executor.astream_events(agent_input, version="v1"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield chunk.content
    
    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=full_response))
    
    if len(chat_history) > 20:
        chat_history.clear()
        conversation_history[conversation_id] = chat_history
        
@router.post("/generate/")
async def generate_final_answer(request_data: PromptRequest):
    """
    POST /generate
    Body: {"prompt": "your question", "conversation_id": "uuid"}
    Returns: StreamingResponse with X-Conversation-ID header
    """
    conversation_id = request_data.conversation_id or str(uuid4())

    return StreamingResponse(
        stream_tokens(request_data.prompt, conversation_id),
        media_type="text/plain",
        headers={"X-Conversation-ID": conversation_id}
    )

@router.delete("/conversations/{conversation_id}")
async def clear_chat(conversation_id: str):
    """Clear a specific conversation history"""
    try:
        if conversation_id in conversation_history:
            del conversation_history[conversation_id]
            return{"message": "Conversation deleted."}
        return {"message": "Unable to find conversation."}
    except Exception as e:
        return {"error": e}


@router.get("/conversations/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get a specific conversation history"""
    history = conversation_history[conversation_id]
    return {
        "conversation_id": conversation_id,
        "messages": [{"type": type(msg).__name__, "content": msg.content} for msg in history]
    }

app.include_router(router)
