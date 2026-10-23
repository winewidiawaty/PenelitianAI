import hashlib
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from src.config import CACHE_DIR, S2_API_KEY
from src.models import Paper

def _generate_paper_id(title: str, doi: str | None = None, arxiv_id: str | None = None) -> str:
    seed = doi or arxiv_id or "".join(title.lower().split())
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:12]

def _read_cache(key: str) -> list[dict] | None:
    cache_path = CACHE_DIR / f"{key}.json"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _write_cache(key: str, data: list[dict]):
    cache_path = CACHE_DIR / f"{key}.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def search_arxiv(query: str, limit: int = 10) -> list[Paper]:
    base_url = "http://export.arxiv.org/api/query?"
    params = {"search_query": f"all:{query}", "start": 0, "max_results": limit}
    url = base_url + urllib.parse.urlencode(params)
    
    papers: list[Paper] = []
    try:
        response = httpx.get(url, timeout=15.0)
        if response.status_code != 200:
            return []
        
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            raw_id = entry.find("atom:id", ns).text.strip()
            arxiv_id = raw_id.split("/abs/")[-1]
            published = entry.find("atom:published", ns).text
            year = int(published[:4]) if published else None
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]

            p_id = _generate_paper_id(title=title, arxiv_id=arxiv_id)
            papers.append(Paper(
                paper_id=p_id,
                title=title,
                authors=authors,
                year=year,
                venue="arXiv",
                abstract=abstract,
                doi=None,
                arxiv_id=arxiv_id,
                url=raw_id,
                citation_count=None,
                source="arxiv"
            ))
    except Exception:
        return []
    return papers

def search_semantic_scholar(query: str, limit: int = 10) -> list[Paper]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,authors,venue,citationCount,externalIds,url"
    }
    headers = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY

    papers: list[Paper] = []
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=15.0)
        if response.status_code != 200:
            return []
        
        data = response.json().get("data", [])
        for item in data:
            if not item.get("title"):
                continue
            title = item.get("title", "")
            ext_ids = item.get("externalIds") or {}
            doi = ext_ids.get("DOI")
            arxiv_id = ext_ids.get("ArXiv")
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            p_id = _generate_paper_id(title=title, doi=doi, arxiv_id=arxiv_id)

            papers.append(Paper(
                paper_id=p_id,
                title=title,
                authors=authors,
                year=item.get("year"),
                venue=item.get("venue"),
                abstract=item.get("abstract") or "Tidak ada abstrak.",
                doi=doi,
                arxiv_id=arxiv_id,
                url=item.get("url"),
                citation_count=item.get("citationCount"),
                source="semantic_scholar"
            ))
    except Exception:
        return []
    return papers

def search_papers(query: str, limit: int = 10, source: str = "both") -> list[Paper]:
    cache_key = hashlib.md5(f"{query}_{limit}_{source}".encode()).hexdigest()
    cached = _read_cache(cache_key)
    if cached is not None:
        return [Paper(**p) for p in cached]

    results: list[Paper] = []
    if source in ["both", "arxiv"]:
        results.extend(search_arxiv(query, limit=limit))
        time.sleep(1)  # Menghindari rate limit ketat
    if source in ["both", "semantic_scholar"]:
        results.extend(search_semantic_scholar(query, limit=limit))

    # Deduplikasi koleksi
    unique: dict[str, Paper] = {}
    for p in results:
        if p.paper_id not in unique:
            unique[p.paper_id] = p

    final_papers = list(unique.values())
    _write_cache(cache_key, [p.model_dump() for p in final_papers])
    return final_papers