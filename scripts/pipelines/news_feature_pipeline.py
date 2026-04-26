#!/usr/bin/env python3
"""News -> Features pipeline"""

from agents.news_intelligence_agent import NewsIntelligenceAgent
from utils.feature_store import FeatureStore
from utils.news_fetcher import NewsFetcher


class NewsFeaturePipeline:
    def __init__(self):
        self.news_agent = NewsIntelligenceAgent()
        self.fetcher = NewsFetcher()
        self.feature_store = FeatureStore()

    def execute(self, symbols: list):
        """Full news-to-feature pipeline"""
        print("Running news feature pipeline...")

        # 1. Fetch multi-source news
        articles = self.fetcher.fetch_latest(symbols)

        # 2. Analyze with FinBERT
        news_features = self.news_agent.analyze_news(symbols)

        # 3. Store timestamped features
        self.feature_store.store_features(news_features, symbols)

        print(f"Stored {len(news_features)} news features")
        return news_features
