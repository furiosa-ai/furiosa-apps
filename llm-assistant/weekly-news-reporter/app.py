# Adapted from NirDiamant/GenAI_Agents (see README.md for details).

import json
import os
from pathlib import Path
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from pydantic import BaseModel

BASE_URL = os.environ.get("FURIOSA_BASE_URL", "http://localhost:8000/v1")
BASE_MODEL = os.environ.get("FURIOSA_MODEL", "furiosa-ai/Llama-3.1-8B-Instruct")

# Initialize API clients
llm = ChatOpenAI(
    model=BASE_MODEL,
    temperature=0.1,
    base_url=BASE_URL,
    openai_api_key="EMPTY",
)


class Article(BaseModel):
    """
    Represents a single news article

    Attributes:
        title (str): Article headline
        url (str): Source URL
        content (str): Article content
    """

    title: str
    url: str
    content: str


class Summary(TypedDict):
    """
    Represents a processed article summary

    Attributes:
        title (str): Original article title
        summary (str): Generated summary
        url (str): Source URL for reference
    """

    title: str
    summary: str
    url: str


# This defines what information we can store and pass between nodes later
class GraphState(TypedDict):
    """
    Maintains workflow state between agents

    Attributes:
        articles (list[Article] | None): Found articles
        summaries (list[Summary] | None): Generated summaries
        report (str | None): Final compiled report
    """

    articles: list[Article] | None
    summaries: list[Summary] | None
    report: str | None


class NewsSearcher:
    """
    Agent responsible for finding relevant AI/ML news articles
    using the Tavily search API
    """

    def search(self) -> list[Article]:
        """
        Performs news search with configured parameters

        Returns:
            list[Article]: Collection of found articles
        """

        # We would normally call the Tavily API here, but for this example,
        # we will load a pre-saved response to avoid needing an API key.
        #
        # response = tavily.search(
        # query="artificial intelligence and machine learning news",
        # topic="news",
        # time_period="1w",
        # search_depth="advanced",
        # max_results=5
        # )

        with Path("response.json").open() as f:
            response = json.load(f)

        articles = []
        for result in response["results"]:
            articles.append(Article(title=result["title"], url=result["url"], content=result["content"]))

        return articles


class Summarizer:
    """
    Agent that processes articles and generates accessible summaries
    using the configured LLM (BASE_MODEL).
    """

    def __init__(self):
        self.system_prompt = """
        You are an AI expert who makes complex topics accessible
        to general audiences. Summarize this article in 2-3 sentences, focusing on the key points
        and explaining any technical terms simply.
        """

    def summarize(self, article: Article) -> str:
        """
        Generates an accessible summary of a single article

        Args:
            article (Article): Article to summarize

        Returns:
            str: Generated summary
        """
        response = llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Title: {article.title}\n\nContent: {article.content}"),
            ]
        )
        return response.content


class Publisher:
    """
    Agent that compiles summaries into a formatted report
    and saves it to disk
    """

    def create_report(self, summaries: list[dict]) -> str:
        """
        Creates and saves a formatted markdown report

        Args:
            summaries (list[dict]): Collection of article summaries

        Returns:
            str: Generated report content
        """
        prompt = """
        Create a weekly AI/ML news report for the general public.
        Format it with:
        1. A brief introduction
        2. The main news items with their summaries
        3. Links for further reading

        Make it engaging and accessible to non-technical readers.
        """

        # Format summaries for the LLM
        summaries_text = "\n\n".join(
            [f"Title: {item['title']}\nSummary: {item['summary']}\nSource: {item['url']}" for item in summaries]
        )

        # Generate report
        response = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=summaries_text)])

        return response.content


def search_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node for article search

    Args:
        state (dict[str, Any]): Current workflow state

    Returns:
        dict[str, Any]: Updated state with found articles
    """
    searcher = NewsSearcher()
    state["articles"] = searcher.search()
    return state


def summarize_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node for article summarization

    Args:
        state (dict[str, Any]): Current workflow state

    Returns:
        dict[str, Any]: Updated state with summaries
    """
    summarizer = Summarizer()
    state["summaries"] = []

    for article in state["articles"]:  # Uses articles from previous node
        summary = summarizer.summarize(article)
        state["summaries"].append({"title": article.title, "summary": summary, "url": article.url})
    return state


def publish_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node for report generation

    Args:
        state (dict[str, Any]): Current workflow state

    Returns:
        dict[str, Any]: Updated state with final report
    """
    publisher = Publisher()
    report_content = publisher.create_report(state["summaries"])
    state["report"] = report_content
    return state


def create_workflow() -> StateGraph:
    """
    Constructs and configures the workflow graph
    search -> summarize -> publish

    Returns:
        StateGraph: Compiled workflow ready for execution
    """

    # Create a workflow (graph) initialized with our state schema
    workflow = StateGraph(state_schema=GraphState)

    # Add processing nodes that we will flow between
    workflow.add_node("search", search_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("publish", publish_node)

    # Define the flow with edges
    workflow.add_edge("search", "summarize")  # search results flow to summarizer
    workflow.add_edge("summarize", "publish")  # summaries flow to publisher

    # Set where to start
    workflow.set_entry_point("search")

    return workflow.compile()


if __name__ == "__main__":
    # Initialize and run workflow
    workflow = create_workflow()
    final_state = workflow.invoke({"articles": None, "summaries": None, "report": None})

    # Display results
    print("\n=== AI/ML Weekly News Report ===\n")
    print(final_state["report"])
