"""
Keyword-based financial news sentiment analysis.

Uses curated positive and negative financial keyword lists (50+ each)
to score text and classify sentiment as Positive / Neutral / Negative.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Keyword lists ──────────────────────────────────────────────────────────────
POSITIVE_WORDS: List[str] = [
    "earnings beat",
    "beats expectations",
    "record revenue",
    "revenue growth",
    "profit surge",
    "strong earnings",
    "dividend increase",
    "dividend hike",
    "buyback",
    "share repurchase",
    "acquisition",
    "merger success",
    "partnership",
    "bull",
    "bullish",
    "rally",
    "surge",
    "soar",
    "soaring",
    "jump",
    "gain",
    "gains",
    "growth",
    "outperform",
    "upgrade",
    "raised guidance",
    "guidance raised",
    "positive outlook",
    "strong demand",
    "record high",
    "all-time high",
    "breakthrough",
    "innovation",
    "expansion",
    "new contract",
    "new deal",
    "strategic alliance",
    "market share gain",
    "margin expansion",
    "cash flow positive",
    "debt reduction",
    "credit upgrade",
    "analyst upgrade",
    "price target raised",
    "overweight",
    "buy rating",
    "strong buy",
    "optimistic",
    "recovery",
    "rebound",
    "turnaround",
    "momentum",
    "upside potential",
    "beat",
    "exceeded",
    "outperformed",
    "robust",
    "resilient",
    "accelerating",
    "improving",
    "milestone",
    "launched",
    "approved",
    "fda approval",
]

NEGATIVE_WORDS: List[str] = [
    "loss",
    "net loss",
    "revenue miss",
    "earnings miss",
    "misses expectations",
    "below expectations",
    "guidance cut",
    "guidance lowered",
    "warning",
    "profit warning",
    "lawsuit",
    "litigation",
    "investigation",
    "sec investigation",
    "fraud",
    "scandal",
    "recall",
    "decline",
    "declining",
    "drop",
    "plunge",
    "crash",
    "collapse",
    "bear",
    "bearish",
    "downgrade",
    "sell rating",
    "underweight",
    "price target cut",
    "debt",
    "default",
    "bankruptcy",
    "layoffs",
    "job cuts",
    "restructuring",
    "workforce reduction",
    "plant closure",
    "factory shutdown",
    "supply chain issues",
    "inflation pressure",
    "margin compression",
    "cost overrun",
    "write-off",
    "write-down",
    "impairment",
    "missed",
    "shortfall",
    "disappointing",
    "weak demand",
    "slowing growth",
    "competition threat",
    "market share loss",
    "regulatory risk",
    "tariff impact",
    "fine",
    "penalty",
    "rejected",
    "failed",
    "withdrawal",
    "delisted",
    "dilution",
    "secondary offering",
    "going concern",
]


def _preprocess_text(text: str) -> str:
    """Lowercase and normalise text for keyword matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def score_text(text: str) -> float:
    """
    Score a single text string for financial sentiment.

    Returns:
        Float in [-1.0, 1.0]:
            -1.0 = maximally negative
             0.0 = neutral
             1.0 = maximally positive
    """
    if not text:
        return 0.0

    processed = _preprocess_text(text)
    pos_count = sum(1 for w in POSITIVE_WORDS if w in processed)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in processed)

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    raw = (pos_count - neg_count) / total
    # Clamp to [-1, 1]
    return max(-1.0, min(1.0, raw))


def analyze_news_sentiment(
    news_items: List[Any],
) -> Dict[str, Any]:
    """
    Aggregate sentiment across a list of news items.

    Args:
        news_items: List of NewsItem objects (or dicts) with 'title' and 'summary'.

    Returns:
        Dict with:
          - sentiment_score: float in [-1, 1]
          - label: "Positive" | "Neutral" | "Negative"
          - article_scores: list of per-article scores
          - positive_count: int
          - negative_count: int
          - neutral_count: int
    """
    if not news_items:
        return {
            "sentiment_score": 0.0,
            "label": "Neutral",
            "article_scores": [],
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
        }

    article_scores: List[Dict[str, Any]] = []
    total_score = 0.0

    for item in news_items:
        if hasattr(item, "title"):
            title = item.title or ""
            summary = item.summary or ""
        elif isinstance(item, dict):
            title = item.get("title", "")
            summary = item.get("summary", "")
        else:
            continue

        combined = f"{title} {summary}"
        s = score_text(combined)
        total_score += s
        article_scores.append(
            {
                "title": title[:100],
                "score": round(s, 4),
                "sentiment": "Positive" if s > 0.1 else ("Negative" if s < -0.1 else "Neutral"),
            }
        )

    n = len(article_scores)
    avg_score = total_score / n if n > 0 else 0.0

    positive_count = sum(1 for a in article_scores if a["sentiment"] == "Positive")
    negative_count = sum(1 for a in article_scores if a["sentiment"] == "Negative")
    neutral_count = sum(1 for a in article_scores if a["sentiment"] == "Neutral")

    if avg_score > 0.1:
        label = "Positive"
    elif avg_score < -0.1:
        label = "Negative"
    else:
        label = "Neutral"

    return {
        "sentiment_score": round(avg_score, 4),
        "label": label,
        "article_scores": article_scores,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
    }


async def get_overall_market_sentiment() -> Dict[str, Any]:
    """
    Compute aggregate market sentiment from news across a basket of major stocks.

    Fetches news for SPY, AAPL, MSFT, AMZN, NVDA and averages sentiment.
    """
    from app.market.yfinance_client import get_news

    basket = ["SPY", "AAPL", "MSFT", "AMZN", "NVDA"]
    all_news = []

    for symbol in basket:
        try:
            news = await get_news(symbol)
            all_news.extend(news)
        except Exception as exc:
            logger.warning("Could not fetch news for %s: %s", symbol, exc)

    result = analyze_news_sentiment(all_news)
    result["source_symbols"] = basket
    result["total_articles"] = len(all_news)
    return result
