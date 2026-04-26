#!/usr/bin/env python3
"""Multi-source news fetcher with deduplication"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).resolve().parents[2]


class NewsFetcher:
    def __init__(self):
        self.cache_dir = ROOT / "data" / "news_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_latest(self, symbols: list, hours_back: int = 24) -> list:
        """Fetch from NewsAPI + RSS with dedup"""
        cutoff = datetime.now() - timedelta(hours=hours_back)

        all_articles = []

        # NewsAPI (requires key)
        all_articles.extend(self._fetch_newsapi(symbols, cutoff))

        # Google RSS
        all_articles.extend(self._fetch_rss_feeds())

        # Deduplicate by hash
        unique_articles = self._deduplicate_articles(all_articles)

        self._cache_articles(unique_articles)
        return unique_articles[:50]  # Top 50 recent

    def _fetch_newsapi(self, symbols, cutoff):
        try:
            api_key = os.getenv('NEWSAPI_KEY', '')
            if not api_key:
                return []

            articles = []
            for symbol in symbols:
                url = f'https://newsapi.org/v2/everything?q={symbol}&apiKey={api_key}&sortBy=publishedAt'
                resp = requests.get(url)
                data = resp.json()
                articles.extend(data.get('articles', []))
            return articles
        except Exception:
            return []

    def _fetch_rss_feeds(self):
        feeds = [
            'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'https://www.moneycontrol.com/rss/stocksmarket.xml'
        ]
        articles = []
        for url in feeds:
            try:
                feed = feedparser.parse(url)
                articles.extend(feed.entries)
            except Exception:
                pass
        return articles

    def _deduplicate_articles(self, articles: list) -> list:
        seen_hashes = set()
        unique = []
        for article in articles:
            content = (article.get('title', '') + article.get('description', '')).lower()
            h = hashlib.md5(content.encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique.append(article)
        return unique

    def _cache_articles(self, articles):
        cache_file = self.cache_dir / f"news_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(articles, f, default=str)
        except Exception:
            pass
