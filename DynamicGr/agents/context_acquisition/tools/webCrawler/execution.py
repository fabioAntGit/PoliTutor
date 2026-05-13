import asyncio
import re
import sys
from typing import Any, Dict, List, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from markdownify import markdownify as md
from rank_bm25 import BM25Okapi
import tldextract


INSTITUTIONAL_KEYWORDS = [
    "about", "who-we-are", "where-we-are", "institution",
    "company", "mission", "vision", "values",
    "our-company", "a-nossa-empresa",
    "products", "solutions", "services",
    "organization", "management", "structure",
    "locations", "offices", "global",
]

NOISE_KEYWORDS = [
    "news", "blog", "press", "events", "media",
    "publications", "article", "post", "insights",
    "careers", "podcast", "cookies", "contact",
    "legal", "privacy", "terms",
]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized_path = parsed.path.rstrip("/") or "/"
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            parsed.params,
            parsed.query,
            "",
        )
    )


def _is_internal_link(base_url: str, link: str) -> bool:
    base_domain = tldextract.extract(base_url).top_domain_under_public_suffix
    link_domain = tldextract.extract(link).top_domain_under_public_suffix
    return base_domain == link_domain or link_domain == ""


def _score_link(link: str, anchor_text: str = "") -> float:
    parsed = urlparse(link)
    path = parsed.path.lower().strip("/")
    anchor_text = anchor_text.lower()

    score = 0.0
    segments = [segment for segment in path.split("/") if segment]

    if any(keyword in path for keyword in INSTITUTIONAL_KEYWORDS):
        score += 6.0
    if any(keyword in anchor_text for keyword in INSTITUTIONAL_KEYWORDS):
        score += 4.0
    if any(noise in path for noise in NOISE_KEYWORDS):
        score -= 8.0

    depth = len(segments)
    score -= depth * 0.8
    if depth <= 1:
        score += 2.0

    return score


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "meta", "nav", "footer", "header", "aside", "form", "noscript"]):
        tag.decompose()

    for selector in [".cookie-banner", ".gdpr-consent", ".consent-popup", ".consent-banner", ".cookies", ".consent-notice"]:
        for element in soup.select(selector):
            element.decompose()

    for tag in soup.find_all(["img", "video", "source", "audio", "iframe"]):
        tag.decompose()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip().lower()
        if (
            href.startswith(("#", "javascript:", "mailto:", "tel:"))
            or href.endswith((".jpg", ".png", ".gif", ".webm", ".mp4", ".pdf"))
            or any(noise in href for noise in ["news", "blog", "press", "events", "media", "publications", "article", "post", "tag"])
        ):
            anchor.decompose()
        else:
            anchor.replace_with(anchor.get_text(strip=True))

    markdown = md(str(soup), heading_style="ATX")
    return _normalize_whitespace(markdown)


def split_markdown_sections(markdown: str) -> List[str]:
    sections: List[str] = []
    current: List[str] = []

    for line in markdown.split("\n"):
        if re.match(r"^#{1,3}\s+", line):
            if current:
                sections.append("\n".join(current).strip())
                current = []
        current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [section for section in sections if len(section) > 80]


def bm25_filter_sections(sections: List[str], keywords: List[str], top_k: int = 10) -> List[str]:
    if not sections:
        return []

    clean_sections = [
        section for section in sections if len(section.split()) > 30]
    if not clean_sections:
        return sections[:top_k]

    tokenized = [section.lower().split() for section in clean_sections]
    bm25 = BM25Okapi(tokenized)
    query_tokens = " ".join(keywords).lower().split()
    scores = bm25.get_scores(query_tokens)

    scored_sections: List[Tuple[str, float]] = []
    for section, score in zip(clean_sections, scores):
        noise_penalty = 2.0 if any(noise in section.lower()
                                   for noise in NOISE_KEYWORDS) else 0
        length_bonus = min(len(section) / 2000, 3)
        final_score = score + length_bonus - noise_penalty
        scored_sections.append((section, final_score))

    ranked = sorted(scored_sections, key=lambda item: item[1], reverse=True)
    max_score = ranked[0][1]

    if max_score <= 0:
        return [section for section, _ in ranked][:top_k]

    threshold = max_score * 0.25
    filtered = [section for section, score in ranked if score >= threshold]
    return filtered[:top_k]


def _discover_internal_links(base_url: str, html: str, max_links: int = 20) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    scored_links: List[Tuple[str, float]] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue

        full_url = urljoin(base_url, href)
        if not full_url.startswith(("http://", "https://")):
            continue
        if not _is_internal_link(base_url, full_url):
            continue

        score = _score_link(full_url, anchor.get_text(strip=True))
        scored_links.append((full_url, score))

    deduped: Dict[str, float] = {}
    for url, score in scored_links:
        if url not in deduped or score > deduped[url]:
            deduped[url] = score

    sorted_links = sorted(
        deduped.items(), key=lambda item: item[1], reverse=True)
    return [url for url, _ in sorted_links[:max_links]]


def _resolve_recommended_pages(base_url: str, recommended_pages: List[str] | None) -> List[str]:
    if not recommended_pages:
        return []

    resolved: List[str] = []
    seen: Set[str] = set()
    for page in recommended_pages:
        candidate = str(page).strip()
        if not candidate:
            continue

        full_url = urljoin(base_url, candidate)
        if not full_url.startswith(("http://", "https://")):
            continue
        if not _is_internal_link(base_url, full_url):
            continue

        normalized = _normalize_url(full_url)
        if normalized in seen:
            continue

        seen.add(normalized)
        resolved.append(normalized)

    return resolved


async def _crawl_web_content_impl(
    url: str,
    max_pages: int = 20,
    max_depth: int = 2,
    recommended_pages: List[str] | None = None,
) -> Dict[str, Any]:
    if not url:
        return {"status": "error", "message": "URL is required."}

    base_url = _normalize_url(url)
    resolved_recommended_pages = _resolve_recommended_pages(base_url, recommended_pages)

    visited: Set[str] = set()
    queue: List[Tuple[str, int]] = [(base_url, 0)]
    queue.extend((recommended_url, 1) for recommended_url in resolved_recommended_pages)
    recommended_set = set(resolved_recommended_pages)
    extracted_profile: List[Dict[str, Any]] = []

    async with AsyncWebCrawler() as crawler:
        while queue and len(visited) < max_pages:
            current_url, depth = queue.pop(0)
            current_url = _normalize_url(current_url)

            if current_url in visited or depth > max_depth:
                continue
            if any(noise in current_url.lower() for noise in NOISE_KEYWORDS):
                continue

            visited.add(current_url)

            try:
                response = await crawler.arun(url=current_url)
                html = response.html
            except Exception:
                continue

            markdown = html_to_markdown(html)
            sections = split_markdown_sections(markdown)
            relevant_sections = bm25_filter_sections(
                sections,
                keywords=INSTITUTIONAL_KEYWORDS,
                top_k=10,
            )

            if relevant_sections:
                extracted_profile.append(
                    {
                        "url": current_url,
                        "sections": relevant_sections,
                    }
                )

            if depth < max_depth:
                try:
                    links = _discover_internal_links(
                        base_url=base_url, html=html, max_links=20)
                    for link in links:
                        normalized_link = _normalize_url(link)
                        if normalized_link in recommended_set:
                            continue
                        if normalized_link not in visited:
                            queue.append((normalized_link, depth + 1))
                except Exception:
                    pass

    return {
        "status": "success",
        "base_url": base_url,
        "recommended_pages": resolved_recommended_pages,
        "total_visited": len(visited),
        "visited_urls": sorted(visited),
        "profile_blocks": extracted_profile,
    }


def _run_crawl_in_proactor_thread(
    url: str,
    max_pages: int,
    max_depth: int,
    recommended_pages: List[str] | None,
) -> Dict[str, Any]:
    loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            _crawl_web_content_impl(url, max_pages, max_depth, recommended_pages)
        )
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


async def crawl_web_content(
    url: str,
    max_pages: int = 20,
    max_depth: int = 2,
    recommended_pages: List[str] | None = None,
) -> Dict[str, Any]:
    # Windows needs Selector loop for psycopg and Proactor loop for Playwright subprocess.
    # Run crawling in a dedicated thread with its own Proactor loop to avoid global conflicts.
    if sys.platform == "win32":
        return await asyncio.to_thread(
            _run_crawl_in_proactor_thread,
            url,
            max_pages,
            max_depth,
            recommended_pages,
        )

    return await _crawl_web_content_impl(url, max_pages, max_depth, recommended_pages)


async def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url")
    max_pages = params.get("max_pages", 10)
    max_depth = params.get("max_depth", 2)
    recommended_pages = params.get("recommended_pages")
    return await crawl_web_content(
        url=url,
        max_pages=max_pages,
        max_depth=max_depth,
        recommended_pages=recommended_pages,
    )
