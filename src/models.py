from typing import Literal
from pydantic import BaseModel, Field

class Paper(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    citation_count: int | None = None
    source: Literal["semantic_scholar", "arxiv"]

class Screening(BaseModel):
    paper_id: str
    relevance: int  # Rentang 0 - 10
    reason: str

class Extraction(BaseModel):
    paper_id: str
    problem: str
    method: str
    dataset: str | None = "tidak disebutkan"
    metrics: str | None = "tidak disebutkan"
    key_findings: str
    limitations: str | None = "tidak disebutkan"

class SearchPlan(BaseModel):
    queries: list[str]
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]

class Synthesis(BaseModel):
    executive_summary: str
    main_themes: str
    research_gaps: str
    limitations_of_review: str

class AgentState(BaseModel):
    topic: str
    plan: SearchPlan | None = None
    papers: dict[str, Paper] = Field(default_factory=dict)
    screenings: dict[str, Screening] = Field(default_factory=dict)
    extractions: dict[str, Extraction] = Field(default_factory=dict)
    synthesis: Synthesis | None = None
    iteration: int = 0
    llm_calls: int = 0
    log: list[dict] = Field(default_factory=list)