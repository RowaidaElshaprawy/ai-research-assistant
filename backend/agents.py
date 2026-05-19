# ── IMPORTS ──────────────────────────────────────────────────────────────────
import os                          # lets us read environment variables
from typing import TypedDict, List, Dict  # for type hints (good practice)

from dotenv import load_dotenv, find_dotenv  # reads our .env file
from langgraph.graph import StateGraph, START, END  # builds the agent pipeline
from langchain_groq import ChatGroq              # connects to Groq LLM
from langchain_core.messages import HumanMessage # wraps our prompts
import arxiv                                     # fetches academic papers
import chromadb                                  # stores/indexes paper content

# ── LOAD SECRET KEYS ─────────────────────────────────────────────────────────
# This reads your .env file and makes GROQ_KEY available to the program
load_dotenv(find_dotenv())
GROQ_API_KEY = os.getenv("GROQ_KEY")

# ── CONNECT TO THE LLM ───────────────────────────────────────────────────────
# This is the brain all 5 agents share
# llama-3.3-70b-versatile is a powerful free model on Groq
# temperature=0.2 means "be precise, not creative" (0=robotic, 1=creative)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY,
    temperature=0.2
)

# ── THE SHARED STATE ─────────────────────────────────────────────────────────
# Think of this as a shared notebook that gets passed between all agents
# Each agent reads from it and writes their results back into it
# TypedDict means we define exactly what keys this dictionary must have
class ResearchState(TypedDict):
    query: str               # the user's research topic
    plan: str                # coordinator's research plan
    search_queries: List[str]  # list of search terms to use
    raw_content: List[Dict[str, str]]  # papers fetched from arXiv
    analyzed_content: str    # analyzer's summary of the papers
    report_draft: str        # synthesis agent's draft report
    final_report: str        # citation agent's final polished report


# ── AGENT 1: COORDINATOR ─────────────────────────────────────────────────────
# This agent reads the user's query and creates a research plan
# It's like a project manager who delegates work to the team
def coordinator_node(state: ResearchState) -> dict:
    print("--- AGENT 1: COORDINATOR ---")  # so you can see progress in terminal

    # We write a prompt telling the LLM what role to play and what to do
    prompt = f"""You are a research coordinator planning a literature review.
    Create a detailed search plan for the topic: '{state['query']}'.
    Identify key sub-topics and specific search queries to find relevant papers."""

    # We send the prompt to the LLM and get a response
    # HumanMessage wraps our text the way the LLM expects to receive it
    response = llm.invoke([HumanMessage(content=prompt)])

    # We return a dict with the keys we want to update in the shared state
    # The agent also creates simple search queries based on the original topic
    return {
        "plan": response.content,
        "search_queries": [
            state['query'],
            state['query'] + " survey",
            state['query'] + " literature review"
        ]
    }


# ── AGENT 2: WEB SEARCH ──────────────────────────────────────────────────────
# This agent uses the arXiv API to fetch real academic papers
# arXiv is a free database of research papers in CS, physics, math, etc.
def search_node(state: ResearchState) -> dict:
    print("--- AGENT 2: SEARCHER ---")

    raw_content = []  # empty list — we'll fill it with papers

    try:
        client = arxiv.Client()  # create a connection to arXiv

        # Search arXiv with the user's query
        # max_results=5 means fetch 5 papers (more = slower but richer)
        # SortCriterion.Relevance = most relevant papers first
        search = arxiv.Search(
            query=state['query'],
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )

        # Loop through each result and save the source URL and abstract
        for result in client.results(search):
            raw_content.append({
                "source": result.entry_id,   # the paper's URL
                "title": result.title,        # the paper's title
                "text": result.summary        # the abstract/summary
            })
            print(f"  Found: {result.title}")  # show progress

    except Exception as e:
        # If arXiv fails (no internet, timeout, etc.) we don't crash
        # We just note the error and continue
        print(f"arXiv error: {e}")
        raw_content.append({
            "source": "error",
            "title": "Search failed",
            "text": f"Could not fetch papers: {e}"
        })

    return {"raw_content": raw_content}


# ── AGENT 3: CONTENT ANALYZER ────────────────────────────────────────────────
# This agent reads all the papers and extracts key information from each one
# It also indexes the content in ChromaDB for efficient retrieval
def analyzer_node(state: ResearchState) -> dict:
    print("--- AGENT 3: ANALYZER ---")

    # ChromaDB is a vector database — it stores text in a way that
    # makes it easy to search by meaning, not just keywords
    chroma_client = chromadb.Client()

    try:
        # Try to create a new collection (like a table in a database)
        collection = chroma_client.create_collection("research_sources")
    except Exception:
        # If it already exists (from a previous run), just get it
        collection = chroma_client.get_or_create_collection("research_sources")

    # Add each paper to ChromaDB
    # documents = the text content
    # metadatas = extra info about each document
    # ids = unique identifier for each document
    if state['raw_content']:
        try:
            collection.add(
                documents=[c['text'] for c in state['raw_content']],
                metadatas=[{"source": c['source'], "title": c.get('title', '')}
                           for c in state['raw_content']],
                ids=[f"doc_{i}" for i in range(len(state['raw_content']))]
            )
        except Exception as e:
            print(f"ChromaDB error: {e}")

    # Now ask the LLM to analyze all the papers
    # We format the raw content into a readable string for the prompt
    papers_text = "\n\n".join([
        f"Title: {c.get('title', 'Unknown')}\nSource: {c['source']}\nAbstract: {c['text']}"
        for c in state['raw_content']
    ])

    prompt = f"""You are a research analyst reviewing academic papers on: '{state['query']}'.

    For each paper below, extract and summarize:
    1. The paper title and source
    2. The methodology or approach used
    3. Key findings and conclusions
    4. Limitations mentioned

    Papers:
    {papers_text}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"analyzed_content": response.content}


# ── AGENT 4: SYNTHESIS ───────────────────────────────────────────────────────
# This agent takes all the analyzed summaries and writes a cohesive report
# It compares and contrasts the papers, finds patterns and themes
def synthesis_node(state: ResearchState) -> dict:
    print("--- AGENT 4: SYNTHESIZER ---")

    prompt = f"""You are an academic writer creating a literature review on: '{state['query']}'.

    Using the analyzed paper summaries below, write a comprehensive literature review that:
    1. Introduces the topic and its importance
    2. Organizes findings thematically (not paper by paper)
    3. Compares and contrasts different approaches
    4. Identifies gaps and future research directions
    5. Writes in formal academic style

    Analyzed summaries:
    {state['analyzed_content']}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"report_draft": response.content}


# ── AGENT 5: CITATION MANAGER ────────────────────────────────────────────────
# This agent polishes the report and adds proper academic citations
# It formats everything in clean Markdown for easy reading and export
def citation_node(state: ResearchState) -> dict:
    print("--- AGENT 5: CITATION MANAGER ---")

    # Format the sources into a readable list for the prompt
    sources_text = "\n".join([
        f"- {c.get('title', 'Unknown')} | {c['source']}"
        for c in state['raw_content']
    ])

    prompt = f"""You are an academic editor finalizing a literature review.

    Take the draft below and:
    1. Fix any grammar or clarity issues
    2. Add in-text citations where papers are mentioned (e.g. [Author, Year])
    3. Append a proper References section at the end using the sources provided
    4. Format the entire output in clean Markdown (use ## for headings, **bold** for key terms)
    5. Make sure it reads like a polished academic paper

    Draft:
    {state['report_draft']}

    Available sources:
    {sources_text}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_report": response.content}


# ── WIRE THE AGENTS TOGETHER WITH LANGGRAPH ──────────────────────────────────
# LangGraph builds a graph (like a flowchart) of how agents connect
# Each node is an agent function, each edge is a connection between them

builder = StateGraph(ResearchState)  # create the graph with our state shape

# Add each agent as a node in the graph
# The string name is how we reference it when adding edges
builder.add_node("coordinator", coordinator_node)
builder.add_node("searcher", search_node)
builder.add_node("analyzer", analyzer_node)
builder.add_node("synthesizer", synthesis_node)
builder.add_node("citator", citation_node)

# Add edges — this defines the ORDER agents run in
# START → coordinator → searcher → analyzer → synthesizer → citator → END
builder.add_edge(START, "coordinator")
builder.add_edge("coordinator", "searcher")
builder.add_edge("searcher", "analyzer")
builder.add_edge("analyzer", "synthesizer")
builder.add_edge("synthesizer", "citator")
builder.add_edge("citator", END)

# Compile the graph — this "locks in" the pipeline and makes it runnable
research_graph = builder.compile()