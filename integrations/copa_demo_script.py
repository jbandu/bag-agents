"""
Copa Airlines Demo Script for December 15th

This script sets up and runs the demo scenarios for the presentation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from .integration_service import get_integration_service
from .mock_copa_data import get_mock_generator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CopaDemoRunner:
    """Runs Copa Airlines demo scenarios"""

    def __init__(self):
        self.service = None
        self.mock_generator = None
        self.scenarios = []

    async def setup(self):
        """Set up the demo environment"""
        logger.info("=" * 80)
        logger.info("COPA AIRLINES BAGGAGE OPERATIONS DEMO - December 15th, 2024")
        logger.info("=" * 80)

        # Initialize services
        self.service = await get_integration_service()
        self.mock_generator = get_mock_generator()

        # Load demo scenarios
        self.scenarios = self.mock_generator.get_demo_scenarios()

        logger.info(f"Loaded {len(self.scenarios)} demo scenarios")
        logger.info("")

    async def run_scenario_1(self):
        """
        Demo Scenario 1: Normal International Connection
        BOG → PTY → JFK

        Shows normal bag flow through Copa's Panama hub
        """
        logger.info("=" * 80)
        logger.info("SCENARIO 1: Normal International Connection")
        logger.info("=" * 80)
        logger.info("")

        scenario = self.scenarios[0]

        logger.info("📍 Passenger: Maria Rodriguez")
        logger.info("📍 Journey: Bogota (BOG) → Panama (PTY) → New York (JFK)")
        logger.info("📍 Bag Tag: 0230556789")
        logger.info("")

        bag = scenario["bag"]
        journey = scenario["journey"]

        logger.info("Bag Journey Timeline:")
        logger.info("-" * 80)

        for event in journey:
            logger.info(
                f"  ✓ {event['location']:4s} | {event['event']:25s} | "
                f"{datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')}"
            )
            await asyncio.sleep(0.5)  # Dramatic pause

        logger.info("")
        logger.info("✅ Bag delivered successfully to JFK carousel")
        logger.info("✅ Connection time: 120 minutes (healthy margin)")
        logger.info("")

        return scenario

    async def run_scenario_2(self):
        """
        Demo Scenario 2: At-Risk Connection Saved by AI
        MIA → PTY → LIM with tight connection

        Demonstrates AI prediction and intervention
        """
        logger.info("=" * 80)
        logger.info("SCENARIO 2: At-Risk Connection Saved by AI")
        logger.info("=" * 80)
        logger.info("")

        scenario = self.scenarios[1]

        logger.info("📍 Passenger: Carlos Martinez")
        logger.info("📍 Journey: Miami (MIA) → Panama (PTY) → Lima (LIM)")
        logger.info("📍 Bag Tag: 0230667890")
        logger.info("📍 Issue: Incoming flight delayed by 30 minutes")
        logger.info("📍 Connection Time: Only 30 minutes! ⚠️")
        logger.info("")

        ai_intervention = scenario["ai_intervention"]

        logger.info("🤖 AI PREDICTION SYSTEM ACTIVATED")
        logger.info("-" * 80)
        logger.info(f"  Predicted At: {datetime.fromisoformat(ai_intervention['predicted_at']).strftime('%H:%M:%S')}")
        logger.info(f"  Risk Score: {ai_intervention['risk_score']} (CRITICAL)")
        logger.info("")
        logger.info("  Recommended Actions:")
        for action in ai_intervention["recommended_actions"]:
            logger.info(f"    • {action}")
            await asyncio.sleep(0.3)

        logger.info("")
        logger.info("Bag Journey Timeline:")
        logger.info("-" * 80)

        for event in scenario["journey"]:
            priority_indicator = "⚡" if event.get("priority") == "RUSH" else "  "
            logger.info(
                f"  {priority_indicator} {event['location']:4s} | {event['event']:30s} | "
                f"{datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')}"
            )
            await asyncio.sleep(0.5)

        logger.info("")
        logger.info("✅ AI Intervention Successful!")
        logger.info("✅ Bag made tight connection despite delay")
        logger.info("✅ Customer satisfaction maintained")
        logger.info("")

        return scenario

    async def run_scenario_3(self):
        """
        Demo Scenario 3: Mishandled Bag Recovery
        PTY → JFK with bag left behind

        Shows PIR creation, AI-powered search, and recovery
        """
        logger.info("=" * 80)
        logger.info("SCENARIO 3: Mishandled Bag with AI-Powered Recovery")
        logger.info("=" * 80)
        logger.info("")

        scenario = self.scenarios[2]

        logger.info("📍 Passenger: Ana Lopez (VIP)")
        logger.info("📍 Flight: CM777 PTY → JFK")
        logger.info("📍 Bag Tag: 0230778901")
        logger.info("📍 Issue: Bag missed loading, passenger arrived without bag")
        logger.info("")

        case = scenario["mishandling_case"]
        ai_analysis = scenario["ai_analysis"]

        logger.info("🚨 PROBLEM REPORTED")
        logger.info("-" * 80)
        logger.info(f"  PIR Number: {case['pir_number']}")
        logger.info(f"  Reported: {datetime.fromisoformat(case['reported_at']).strftime('%H:%M:%S')}")
        logger.info(f"  Type: {case['type'].upper()}")
        logger.info("")

        await asyncio.sleep(1)

        logger.info("🤖 AI ROOT CAUSE ANALYSIS")
        logger.info("-" * 80)
        logger.info(f"  Root Cause: {ai_analysis['root_cause']}")
        logger.info(f"  Location Prediction: {ai_analysis['location_prediction']}")
        logger.info(f"  Confidence: {ai_analysis['confidence']} (94%)")
        logger.info("")
        logger.info("  Recommended Actions:")
        for action in ai_analysis["recommended_actions"]:
            logger.info(f"    • {action}")
            await asyncio.sleep(0.3)

        logger.info("")
        logger.info("Recovery Timeline:")
        logger.info("-" * 80)

        for event in scenario["journey"]:
            logger.info(
                f"  • {event['event']:35s} | "
                f"{datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')}"
            )
            await asyncio.sleep(0.5)

        logger.info("")
        logger.info("✅ Bag located in PTY holding area (as predicted)")
        logger.info("✅ Loaded on next PTY-JFK flight")
        logger.info("✅ Delivery arranged to passenger residence")
        logger.info("✅ Resolution time: 4 hours (vs industry avg 24+ hours)")
        logger.info("")

        return scenario

    async def run_all_scenarios(self):
        """Run all demo scenarios in sequence"""
        await self.setup()

        logger.info("Starting Copa Airlines Demo Scenarios...")
        logger.info("")
        await asyncio.sleep(2)

        # Scenario 1
        await self.run_scenario_1()
        await asyncio.sleep(3)

        # Scenario 2
        await self.run_scenario_2()
        await asyncio.sleep(3)

        # Scenario 3
        await self.run_scenario_3()
        await asyncio.sleep(2)

        # Summary
        logger.info("=" * 80)
        logger.info("DEMO SUMMARY")
        logger.info("=" * 80)
        logger.info("")
        logger.info("✅ Demonstrated normal bag flow through Copa hub")
        logger.info("✅ Showed AI prediction preventing misconnection")
        logger.info("✅ Demonstrated rapid mishandled bag recovery")
        logger.info("")
        logger.info("KEY BENEFITS:")
        logger.info("  • Real-time visibility across Copa network")
        logger.info("  • Proactive intervention reduces mishandling")
        logger.info("  • AI-powered root cause analysis")
        logger.info("  • 85% faster resolution times")
        logger.info("  • Improved customer satisfaction")
        logger.info("")
        logger.info("=" * 80)

    async def get_demo_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard visualization during demo"""
        return {
            "active_flights": await self.service.get_flights(airport="PTY"),
            "total_bags_today": len(self.mock_generator.generated_bags),
            "at_risk_bags": len([
                b for b in self.mock_generator.generated_bags
                if b.get("risk_level") in ["high", "critical"]
            ]),
            "mishandling_rate": 0.3,  # 0.3% - excellent rate
            "scenarios": self.scenarios,
        }


async def main():
    """Main demo entry point"""
    demo = CopaDemoRunner()
    await demo.run_all_scenarios()


if __name__ == "__main__":
    asyncio.run(main())
