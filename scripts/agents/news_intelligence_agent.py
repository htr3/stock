#!/usr/bin/env python3
"""News Intelligence Agent: FinBERT sentiment + novelty + events"""

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from utils.news_fetcher import NewsFetcher


class NewsIntelligenceAgent:
    def __init__(self):
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert"
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.fetcher = NewsFetcher()
        self.historical_titles = []  # Load from cache in production

    def analyze_news(self, symbols: list) -> dict:
        """Fetch + analyze news for symbols with novelty, severity, weights"""

        # Multi-source fetch
        articles = self.fetcher.fetch_latest(symbols)

        features = {
            'sentiment_score': 0.0,
            'novelty_score': 0.0,
            'event_severity': 0.0,
            'articles_count': len(articles)
        }

        event_keywords = {
            'earnings': 0.8, 'beat': 0.6, 'miss': -0.6,
            'downgrade': -0.8, 'upgrade': 0.8, 'merger': 0.7,
            'bankruptcy': -1.0, 'lawsuit': -0.9
        }

        source_weights = {
            'reuters': 1.5, 'bloomberg': 1.4, 'wsj': 1.3,
            'default': 1.0
        }

        historical_embeds = []
        if self.historical_titles:
            historical_embeds = self.embedding_model.encode(self.historical_titles)

        total_weight = 0.0

        for article in articles:
            title = article.get('title', '')
            summary = article.get('summary', '')
            text = title + '. ' + summary

            # Sentiment
            sentiment = self.sentiment_pipeline(text)[0]
            sent_val = sentiment['score'] * (1 if sentiment['label'] == 'positive' else -1)

            # Source weight
            source = article.get('source', {}).get('name', 'default').lower()
            weight = source_weights.get(source, 1.0)

            # Event severity
            severity = 0.0
            text_lower = text.lower()
            for keyword, score in event_keywords.items():
                if keyword in text_lower:
                    severity += score

            # Novelty
            novelty = 1.0
            if len(historical_embeds) > 0:
                embed_new = self.embedding_model.encode([text])
                sims = cosine_similarity(embed_new, historical_embeds)[0]
                novelty = 1 - np.max(sims)

            # Weighted aggregate
            features['sentiment_score'] += sent_val * weight * novelty
            features['event_severity'] += severity * weight
            features['novelty_score'] += novelty

            total_weight += weight

        n = max(features['articles_count'], 1)
        features['sentiment_score'] /= n
        features['event_severity'] /= n
        features['novelty_score'] /= n

        print(f"News: Sent={features['sentiment_score']:.3f}, Novelty={features['novelty_score']:.3f}, Severity={features['event_severity']:.3f}")
        return features
