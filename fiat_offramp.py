import os
import time
import hmac
import hashlib
import json
import logging
import requests
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FIATOffRamp")

class FIATOffRamp:
    """Handles automated crypto-to-fiat (INR) conversion and bank payout via Indian Exchange API."""
    
    def __init__(self):
        self.api_key = os.getenv("EXCHANGE_API_KEY", "")
        self.api_secret = os.getenv("EXCHANGE_SECRET_KEY", "")
        self.base_url = "[https://api.coindcx.com](https://api.coindcx.com)"
        self.min_offramp_usdc = float(os.getenv("MIN_OFFRAMP_USDC", "10.0"))

    def _generate_signature(self, secret: str, body_str: str) -> str:
        return hmac.new(secret.encode('utf-8'), body_str.encode('utf-8'), hashlib.sha256).hexdigest()

    def convert_usdc_to_inr(self, amount_usdc: float) -> Dict[str, Any]:
        """Sells USDC for INR and triggers bank/UPI withdrawal if threshold is met."""
        if amount_usdc < self.min_offramp_usdc:
            return {
                "status": "skipped",
                "message": f"USDC balance ({amount_usdc:.2f}) is below minimum off-ramp threshold ({self.min_offramp_usdc:.2f} USDC)."
            }

        if not self.api_key or not self.api_secret or self.api_key == "your_exchange_api_key_here":
            return {
                "status": "dry_run",
                "message": f"Simulation: Would convert {amount_usdc:.2f} USDC into INR and initiate UPI/bank withdrawal. Add EXCHANGE_API_KEY in .env for live execution.",
                "amount_usdc": amount_usdc,
                "estimated_inr": round(amount_usdc * 87.5, 2)
            }

        try:
            timeStamp = int(round(time.time() * 1000))
            body = {
                "side": "sell",
                "order_type": "market_order",
                "market": "USDCINR",
                "total_quantity": amount_usdc,
                "timestamp": timeStamp
            }
            json_body = json.dumps(body, separators=(',', ':'))
            signature = self._generate_signature(self.api_secret, json_body)
            
            headers = {
                'Content-Type': 'application/json',
                'X-AUTH-APIKEY': self.api_key,
                'X-AUTH-SIGNATURE': signature
            }

            url = f"{self.base_url}/exchange/v1/orders/create"
            response = requests.post(url, data=json_body, headers=headers, timeout=10)
            
            if response.status_code == 200:
                order_data = response.json()
                logger.info(f"Exchange market sell order executed: {order_data}")
                return {
                    "status": "success",
                    "action": "USDC_SELL_EXECUTED",
                    "amount_usdc": amount_usdc,
                    "order_details": order_data
                }
            else:
                logger.error(f"Failed to place order on exchange: {response.text}")
                return {"status": "error", "error": response.text}

        except Exception as e:
            logger.error(f"Error during FIAT off-ramp conversion: {e}")
            return {"status": "error", "error": str(e)}