import logging
from typing import Dict, Any
from web3_handler import Web3Handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestnetFarmer")

class TestnetFarmer:
    def __init__(self, web3_handler: Web3Handler):
        self.w3_handler = web3_handler

    def run_daily_farming_routine(self) -> Dict[str, Any]:
        """Runs the testnet airdrop farming routine."""
        logger.info("Starting daily testnet farming routine...")
        
        testnet_balance = self.w3_handler.get_native_balance("base_sepolia")
        tx_result = self.w3_handler.execute_testnet_interaction()
        
        report = {
            "routine": "Base Sepolia Testnet Daily Active Address Farming",
            "testnet_balance_eth": testnet_balance,
            "interaction_result": tx_result,
            "airdrop_status": "Eligible / Active" if testnet_balance > 0 else "Needs Testnet Faucet Funds"
        }
        
        logger.info(f"Testnet farming completed: {report}")
        return report