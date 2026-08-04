import os
import json
import logging
import requests
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIEngine")

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.fear_greed_url = "https://api.alternative.me/fng/"
        self.price_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,polygon-ecosystem-token&vs_currencies=usd,inr&include_24hr_change=true"

    def fetch_market_signals(self) -> Dict[str, Any]:
        """Fetches current Fear & Greed Index and market price trends from free public APIs."""
        market_data = {}
        try:
            res_fg = requests.get(self.fear_greed_url, timeout=5)
            if res_fg.status_code == 200:
                data = res_fg.json().get("data", [{}])[0]
                market_data["fear_and_greed"] = {
                    "value": data.get("value"),
                    "classification": data.get("value_classification")
                }
        except Exception as e:
            logger.warning(f"Could not fetch Fear & Greed data: {e}")
            market_data["fear_and_greed"] = {"value": 50, "classification": "Neutral"}

        try:
            res_price = requests.get(self.price_url, timeout=5)
            if res_price.status_code == 200:
                market_data["prices"] = res_price.json()
        except Exception as e:
            logger.warning(f"Could not fetch Price data: {e}")
            market_data["prices"] = {}

        return market_data

    def evaluate_farming_strategy(self) -> Dict[str, Any]:
        """Uses Gemini API or heuristic model to analyze signals and formulate trading/farming actions."""
        signals = self.fetch_market_signals()
        
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                
                prompt = f"""
                You are an autonomous AI Crypto Farming and Sentiment Trading Agent operating on low-gas EVM networks (Polygon & Base).
                Analyze the following real-time market data:
                {json.dumps(signals, indent=2)}

                Provide a JSON response with the following keys ONLY:
                - "sentiment_score": float between -1.0 (extreme fear) and 1.0 (extreme greed)
                - "recommended_action": string, one of ["BUY", "SELL", "HOLD"]
                - "confidence": float between 0.0 and 1.0
                - "reasoning": string, concise 1-2 sentence explanation
                - "trigger_testnet_farm": boolean, set to true to execute daily testnet activity
                """

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                
                text_content = response.text.strip()
                if "```json" in text_content:
                    text_content = text_content.split("```json")[1].split("```")[0].strip()
                elif "```" in text_content:
                    text_content = text_content.split("```")[1].strip()
                
                analysis = json.loads(text_content)
                analysis["signals"] = signals
                return analysis

            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}. Falling back to rule-based engine.")

        # Fallback Rule-Based Engine
        fg_val = int(signals.get("fear_and_greed", {}).get("value", 50))
        if fg_val < 30:
            action = "BUY"
            sentiment = (fg_val - 50) / 50.0
            confidence = 0.80
            reason = f"Extreme fear detected ({fg_val}/100). Historical dollar-cost-average buying opportunity."
        elif fg_val > 70:
            action = "SELL"
            sentiment = (fg_val - 50) / 50.0
            confidence = 0.75
            reason = f"Greed detected ({fg_val}/100). Rebalancing micro-positions into USDC."
        else:
            action = "HOLD"
            sentiment = 0.0
            confidence = 0.60
            reason = f"Market is neutral ({fg_val}/100). Maintaining current yield and farming positions."

        return {
            "sentiment_score": round(sentiment, 2),
            "recommended_action": action,
            "confidence": confidence,
            "reasoning": reason,
            "trigger_testnet_farm": True,
            "signals": signals
        }