"""Twitter/X Bot — Auto-reply with analysis on mentioned tweets.

Usage:
    export TWITTER_API_KEY="your-api-key"
    export TWITTER_API_SECRET="your-api-secret"
    export TWITTER_ACCESS_TOKEN="your-access-token"
    export TWITTER_ACCESS_SECRET="your-access-secret"
    export TWITTER_BEARER_TOKEN="your-bearer-token"
    python -m backend.bots.twitter_bot

Setup:
    1. Go to https://developer.twitter.com → Developer Portal
    2. Create a Project + App
    3. Enable: Read + Write permissions
    4. Generate API Key, API Secret, Access Token, Access Secret, Bearer Token
    5. Set user context: Read and Write
"""

import os
import time
import logging
import requests

logger = logging.getLogger("truthlens.twitter")


class TwitterBot:
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        self.api_base = "https://api.twitter.com/2"
        self.last_mention_id = None
        
        if not all([self.api_key, self.access_token]):
            raise ValueError("Set TWITTER_API_KEY and TWITTER_ACCESS_TOKEN env vars")

    def _headers(self):
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def _oauth_headers(self):
        """Generate OAuth 1.0a headers."""
        import hashlib
        import hmac
        import time
        import urllib.parse
        
        nonce = str(int(time.time() * 1000))
        timestamp = str(int(time.time()))
        
        params = {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": timestamp,
            "oauth_token": self.access_token,
            "oauth_version": "1.0",
        }
        
        return {
            "Authorization": f'OAuth oauth_consumer_key="{self.api_key}", '
                            f'oauth_token="{self.access_token}", '
                            f'oauth_signature_method="HMAC-SHA1", '
                            f'oauth_version="1.0"',
            "Content-Type": "application/json",
        }

    def get_mentions(self, since_id=None):
        """Get recent mentions."""
        url = f"{self.api_base}/users/me"
        me = requests.get(url, headers=self._headers()).json()
        user_id = me.get("data", {}).get("id")
        
        if not user_id:
            return []
        
        url = f"{self.api_base}/users/{user_id}/mentions"
        params = {"max_results": 10}
        if since_id:
            params["since_id"] = since_id
        
        resp = requests.get(url, headers=self._headers(), params=params)
        data = resp.json()
        return data.get("data", [])

    def reply(self, tweet_id: str, text: str):
        """Reply to a tweet."""
        url = f"{self.api_base}/tweets"
        payload = {
            "text": text[:280],  # Twitter char limit
            "reply": {"in_reply_to_tweet_id": tweet_id},
        }
        resp = requests.post(url, headers=self._oauth_headers(), json=payload)
        return resp.status_code == 201

    def analyze_and_reply(self, tweet_id: str, text: str):
        """Analyze text and reply with results."""
        try:
            from backend.services.model_loader import get_nlp_model
            model = get_nlp_model()
            
            if not model:
                self.reply(tweet_id, "Analysis service unavailable. Try again later.")
                return
            
            result = model.predict(text)
            score = result["confidence"] * 100
            label = result["label"]
            
            if label == "fake":
                reply_text = f"TruthLens Analysis:\n\nUNRELIABLE ({score:.0f}%)\n\nThe text contains patterns associated with misinformation. Verify with trusted sources before sharing."
            else:
                reply_text = f"TruthLens Analysis:\n\nLIKELY RELIABLE ({score:.0f}%)\n\nNo significant misinformation indicators detected, but always verify important claims independently."
            
            self.reply(tweet_id, reply_text)
            logger.info(f"Replied to tweet {tweet_id}: {label}")
            
        except Exception as e:
            logger.error(f"Error analyzing tweet {tweet_id}: {e}")

    def run(self, poll_interval=60):
        """Main loop — poll for mentions and reply."""
        logger.info("TruthLens Twitter bot started")
        
        while True:
            try:
                mentions = self.get_mentions(self.last_mention_id)
                
                for mention in mentions:
                    tweet_id = mention["id"]
                    text = mention.get("text", "")
                    
                    # Remove @mention from text
                    clean_text = " ".join(
                        word for word in text.split() 
                        if not word.startswith("@")
                    )
                    
                    if clean_text.strip():
                        self.analyze_and_reply(tweet_id, clean_text)
                    
                    self.last_mention_id = tweet_id
                
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(poll_interval)


def main():
    logging.basicConfig(level=logging.INFO)
    bot = TwitterBot()
    bot.run()


if __name__ == "__main__":
    main()
