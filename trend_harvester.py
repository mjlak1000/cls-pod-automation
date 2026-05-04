"""
SOP 1: Trend Harvester
Automates niche discovery and hook extraction for CLS
"""
import os
from datetime import datetime, timezone
from typing import List, Dict
import json
import time
from pytrends.request import TrendReq
import praw
from dotenv import load_dotenv

load_dotenv()

# Scoring weights
GOOGLE_WEIGHT = 0.6
REDDIT_WEIGHT = 0.4

# Niche validation thresholds
GREEN_DEMAND_THRESHOLD = 4.0
GREEN_COMPETITION_THRESHOLD = 2.0
AMBER_DEMAND_THRESHOLD = 3.0
AMBER_COMPETITION_MIN = 2.0
AMBER_COMPETITION_MAX = 3.0

# TODO: Replace with live Etsy scraping once integration is implemented
DEFAULT_COMPETITION_SCORE = 2.5


class TrendHarvester:
    """Automate SOP 1 trend discovery"""

    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "trend_harvester/1.0"),
        )
        self.etsy_api_key = os.getenv("ETSY_API_KEY")

    def get_google_trends_score(self, keyword: str, days: int = 30) -> float:
        """Get Google Trends demand score (0-5)"""
        try:
            self.pytrends.build_payload([keyword], timeframe=f'today {days}-d', geo='US')
            df = self.pytrends.interest_over_time()

            if df.empty or keyword not in df.columns:
                return 0.0

            values = df[keyword].values
            if len(values) < 2:
                return 0.0

            # Calculate trend slope
            slope = (values[-1] - values[0]) / len(values)
            avg_interest = values.mean()

            score = 0.0

            # Score based on average interest
            if avg_interest >= 50:
                score += 3.0
            elif avg_interest >= 25:
                score += 2.0
            elif avg_interest >= 10:
                score += 1.0

            # Score based on trend direction
            if slope > 2:
                score += 2.0
            elif slope > 0:
                score += 1.0

            return min(score, 5.0)

        except Exception as e:
            print(f"Google Trends error: {e}")
            return 0.0

    def get_reddit_hooks(self, subreddit_name: str, keyword: str, limit: int = 100) -> List[str]:
        """Extract sentiment hooks from Reddit"""
        hooks = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            for submission in subreddit.search(keyword, limit=limit, time_filter='month'):
                submission.comments.replace_more(limit=0)
                for comment in submission.comments[:5]:
                    text = comment.body.strip()
                    if (
                        20 < len(text) < 150
                        and not text.startswith('[')
                        and not text.startswith('http')
                    ):
                        hooks.append(text)

            return hooks[:10]

        except Exception as e:
            print(f"Reddit error: {e}")
            return []

    def discover_niche(self, keyword: str, subreddit: str, emotion_tag: str) -> Dict:
        """Full niche discovery workflow"""
        print(f"\n🔍 Discovering: {keyword}")
        print("-" * 60)

        # Get Google Trends score
        google_score = self.get_google_trends_score(keyword)
        print(f"   Google Trends: {google_score:.1f}/5")

        # Get Reddit hooks
        hooks = self.get_reddit_hooks(subreddit, keyword, limit=50)
        reddit_score = min(len(hooks) / 10.0 * 5, 5.0)
        print(f"   Reddit Hooks: {len(hooks)}")

        # Calculate demand score
        demand_score = google_score * GOOGLE_WEIGHT + reddit_score * REDDIT_WEIGHT
        print(f"   📊 Final Demand: {demand_score:.1f}/5")

        competition_score = DEFAULT_COMPETITION_SCORE
        print(f"   Competition: {competition_score:.1f}/5")

        # Determine status
        if demand_score >= GREEN_DEMAND_THRESHOLD and competition_score <= GREEN_COMPETITION_THRESHOLD:
            status = "✅ GREEN - VALIDATED"
        elif demand_score >= AMBER_DEMAND_THRESHOLD and AMBER_COMPETITION_MIN <= competition_score <= AMBER_COMPETITION_MAX:
            status = "⚠️ AMBER - MONITOR"
        else:
            status = "❌ RED - SKIP"

        print(f"   {status}")

        return {
            "niche_name": keyword.title(),
            "emotion_tag": emotion_tag,
            "demand_score": round(demand_score, 1),
            "competition_score": competition_score,
            "trending_keywords": [keyword],
            "sentiment_hooks": hooks[:5],
            "primary_link": f"https://www.reddit.com/r/{subreddit}/search?q={keyword.replace(' ', '+')}",
            "status": status,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        }

    def batch_discover(self, niches: List[Dict]) -> List[Dict]:
        """Discover multiple niches in batch"""
        results = []
        for niche in niches:
            try:
                trend_data = self.discover_niche(
                    niche["keyword"],
                    niche["subreddit"],
                    niche["emotion"],
                )
                results.append(trend_data)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                print(f"Error processing {niche.get('keyword', 'unknown')}: {e}")
        return results


if __name__ == "__main__":
    harvester = TrendHarvester()

    test_niches = [
        {"keyword": "goblincore autumn", "subreddit": "goblincore", "emotion": "nostalgia"},
        {"keyword": "academic rival", "subreddit": "studying", "emotion": "pride"},
        {"keyword": "cozy chaos", "subreddit": "cottagecore", "emotion": "comfort"},
    ]

    print("=" * 60)
    print("SOP 1: TREND HARVESTER")
    print("=" * 60)

    results = harvester.batch_discover(test_niches)

    # Save results
    output_dir = "output/sop1"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/validated_niches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    validated = [r for r in results if "GREEN" in r.get("status", "")]

    print(f"\n{'=' * 60}")
    print(f"✅ Saved {len(results)} niches to: {output_path}")
    print(f"🔥 {len(validated)} GREEN niches ready for SEO generation")
    print(f"{'=' * 60}")
