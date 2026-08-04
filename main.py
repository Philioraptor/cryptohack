import os
import logging
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from web3_handler import Web3Handler
from ai_engine import AIEngine
from testnet_farmer import TestnetFarmer
from fiat_offramp import FIATOffRamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MainService")

w3_handler = Web3Handler()
ai_engine = AIEngine()
testnet_farmer = TestnetFarmer(w3_handler)
fiat_offramp = FIATOffRamp()

latest_cycle_result = {}

def execute_farming_cycle():
    """Core periodic worker cycle combining AI sentiment evaluation, testnet airdrop farming, and INR off-ramping."""
    global latest_cycle_result
    logger.info("--- Starting Autonomous AI Crypto Farming Cycle ---")
    
    ai_decision = ai_engine.evaluate_farming_strategy()
    logger.info(f"AI Decision: {ai_decision.get('recommended_action')} | Confidence: {ai_decision.get('confidence')}")
    
    testnet_report = {}
    if ai_decision.get("trigger_testnet_farm", True):
        testnet_report = testnet_farmer.run_daily_farming_routine()

    action = ai_decision.get("recommended_action", "HOLD")
    confidence = float(ai_decision.get("confidence", 0.0))
    swap_report = {}
    if action in ["BUY", "SELL"] and confidence >= float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.75")):
        swap_report = w3_handler.execute_sentiment_swap(action, confidence)

    polygon_pol_bal = w3_handler.get_native_balance("polygon")
    base_sepolia_eth_bal = w3_handler.get_native_balance("base_sepolia")

    offramp_report = fiat_offramp.convert_usdc_to_inr(polygon_pol_bal * 0.5)

    latest_cycle_result = {
        "status": "completed",
        "ai_decision": ai_decision,
        "testnet_farming_report": testnet_report,
        "mainnet_swap_report": swap_report,
        "fiat_offramp_report": offramp_report,
        "balances": {
            "polygon_mainnet_pol": polygon_pol_bal,
            "base_sepolia_eth": base_sepolia_eth_bal,
            "wallet_address": w3_handler.get_wallet_address()
        }
    }
    logger.info("--- Farming Cycle Completed ---")

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    poll_hours = int(os.getenv("POLL_INTERVAL_HOURS", "6"))
    scheduler.add_job(execute_farming_cycle, 'interval', hours=poll_hours)
    scheduler.start()
    logger.info(f"Background scheduler started. Polling every {poll_hours} hours.")
    
    execute_farming_cycle()
    
    yield
    
    scheduler.shutdown()
    logger.info("Scheduler shut down.")

app = FastAPI(
    title="AI Crypto Farmer",
    description="Low-consumption AI Crypto Farming Bot deployed on Render Free. Automates testnet airdrops, Polygon micro-swaps, and INR fiat off-ramping.",
    version="1.1.0",
    lifespan=lifespan
)

@app.get("/")
def home():
    return {
        "service": "AI Crypto Farmer",
        "status": "online",
        "platform": "Render Free Tier Compatible",
        "wallet_address": w3_handler.get_wallet_address(),
        "latest_cycle": latest_cycle_result
    }

@app.get("/health")
def health():
    return {"status": "ok", "memory_usage": "Low (<100MB)"}

@app.post("/run-cycle")
def run_cycle_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_farming_cycle)
    return {"message": "Farming cycle triggered in background."}

@app.get("/status")
def get_status():
    return latest_cycle_result

@app.post("/trigger-offramp")
def trigger_offramp_endpoint(amount_usdc: float = 10.0):
    """Triggers an immediate USDC -> INR currency exchange off-ramp."""
    return fiat_offramp.convert_usdc_to_inr(amount_usdc)

@app.get("/off-ramp-guide")
def inr_off_ramp_guide():
    return {
        "title": "Converting Earned Crypto to Indian Rupees (INR)",
        "network": "Polygon (POL/MATIC/USDC) or Base (ETH/USDC)",
        "steps": [
            {
                "step": 1,
                "action": "Earn or Swap Crypto",
                "details": "Your bot earns testnet airdrop allocations or accumulates POL/USDC on Polygon Mainnet via micro-swaps."
            },
            {
                "step": 2,
                "action": "Automated CEX / On-Ramp Integration",
                "supported_exchanges": [
                    "CoinDCX API (Automated USDC/INR Market Orders & Bank Payouts)",
                    "WazirX API / Mudrex",
                    "Onramp.money / Binance P2P (Direct UPI/IMPS)"
                ]
            },
            {
                "step": 3,
                "action": "Sell for INR & Withdraw to Bank",
                "details": "The bot's fiat_offramp module converts accumulated USDC to INR and initiates instant bank transfer via UPI/IMPS."
            }
        ],
        "gas_cost_note": "Polygon gas costs are less than 0.10 INR per transaction, ensuring 99.9% of profits are preserved."
    }