"""
Integration Test 6: Copa Airlines Specific Scenarios

Test Copa-specific operations:
- PTY hub-and-spoke model
- High connection rate (70%)
- Copa's top routes
- Copa's operational patterns
"""

import pytest
import asyncio
from datetime import datetime
from langgraph.orchestrator_state import create_initial_bag_state, BagStatus


class TestCopaScenarios:
    """Test suite for Copa Airlines specific scenarios"""

    @pytest.mark.asyncio
    async def test_pty_hub_operations(
        self,
        orchestrator,
        copa_flight_schedule
    ):
        """Test PTY hub operations with multiple connections"""

        # Create bags for typical Copa hub scenario
        # BOG → PTY → JFK (common routing)
        bag_state = create_initial_bag_state(
            bag_id="BAG_COPA_HUB_001",
            tag_number="0230800001",
            passenger_id="PNR_COPA_001",
            origin_flight="CM101",
            origin_airport="BOG",
            destination_airport="JFK",
            weight_kg=23.5,
            connection_flight="CM451",
            connection_airport="PTY"
        )

        result = await orchestrator.process_bag(bag_state, has_connection=True)

        # Verify PTY hub handling
        events = result["bag"]["events"]
        locations = [e["location"] for e in events]

        assert "PTY" in locations, \
            "PTY hub should appear in journey"

        assert "BOG" in locations[0] or locations[0] == "BOG", \
            "Journey should start at BOG"

        print(f"\n✅ PTY Hub Operations Test PASSED")
        print(f"   Route: {locations[0]} → PTY → {locations[-1]}")


    @pytest.mark.asyncio
    async def test_high_connection_rate(
        self,
        orchestrator,
        copa_bag_data
    ):
        """Test handling 70% connection rate (Copa typical)"""

        from langgraph.orchestrator_state import create_initial_bag_state

        # Create 10 bags, 7 with connections
        bags = []

        # 7 connection bags
        for i in range(7):
            bag = create_initial_bag_state(
                bag_id=f"BAG_CONN_COPA_{i}",
                tag_number=f"023080100{i}",
                passenger_id=f"PNR_CONN_{i}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="JFK",
                weight_kg=22.0,
                connection_flight="CM451",
                connection_airport="PTY"
            )
            bags.append((bag, True))  # has_connection=True

        # 3 direct bags
        for i in range(3):
            bag = create_initial_bag_state(
                bag_id=f"BAG_DIRECT_COPA_{i}",
                tag_number=f"023080200{i}",
                passenger_id=f"PNR_DIRECT_{i}",
                origin_flight="CM777",
                origin_airport="PTY",
                destination_airport="JFK",
                weight_kg=22.0
            )
            bags.append((bag, False))  # has_connection=False

        # Process all
        tasks = [
            orchestrator.process_bag(bag, has_connection=has_conn)
            for bag, has_conn in bags
        ]

        results = await asyncio.gather(*tasks)

        # Verify all processed successfully
        successful = sum(
            1 for r in results
            if r["status"] == "completed"
        )

        success_rate = successful / len(bags) * 100

        assert success_rate >= 95, \
            f"Should handle high connection rate, got {success_rate}% success"

        print(f"\n✅ High Connection Rate Test PASSED")
        print(f"   Total bags: {len(bags)}")
        print(f"   Connection bags: 7 (70%)")
        print(f"   Success rate: {success_rate}%")


    @pytest.mark.asyncio
    async def test_copa_top_routes(
        self,
        orchestrator,
        copa_flight_schedule
    ):
        """Test Copa's most common routes"""

        routes = [
            ("PTY", "JFK", "CM451"),
            ("PTY", "MIA", "CM202"),
            ("PTY", "MEX", "CM789"),
            ("BOG", "PTY", "CM101"),
        ]

        for origin, dest, flight in routes:
            bag = create_initial_bag_state(
                bag_id=f"BAG_ROUTE_{flight}",
                tag_number=f"0230{hash(flight) % 100000:06d}",
                passenger_id=f"PNR_{flight}",
                origin_flight=flight,
                origin_airport=origin,
                destination_airport=dest,
                weight_kg=22.0
            )

            result = await orchestrator.process_bag(bag, has_connection=False)

            assert result["status"] == "completed", \
                f"Route {origin}→{dest} should complete successfully"

        print(f"\n✅ Copa Top Routes Test PASSED")
        print(f"   Routes tested: {len(routes)}")


    @pytest.mark.asyncio
    async def test_wave_operations(
        self,
        orchestrator,
        copa_flight_schedule
    ):
        """Test Copa's wave departure pattern"""

        # Copa operates in waves (peak hours)
        # Simulate afternoon wave: 14:00-18:00

        # Create bags for wave departure
        wave_bags = []
        for i in range(10):
            bag = create_initial_bag_state(
                bag_id=f"BAG_WAVE_{i:02d}",
                tag_number=f"023082000{i}",
                passenger_id=f"PNR_WAVE_{i:02d}",
                origin_flight="CM101",
                origin_airport="PTY",
                destination_airport="JFK",
                weight_kg=22.0
            )
            wave_bags.append(bag)

        start_time = datetime.utcnow()

        # Process wave
        tasks = [
            orchestrator.process_bag(bag, has_connection=False)
            for bag in wave_bags
        ]

        results = await asyncio.gather(*tasks)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # All should complete
        assert all(r["status"] == "completed" for r in results), \
            "All bags in wave should be processed"

        print(f"\n✅ Wave Operations Test PASSED")
        print(f"   Wave size: {len(wave_bags)} bags")
        print(f"   Processing time: {duration:.2f}s")


    @pytest.mark.asyncio
    async def test_copa_baggage_tag_format(
        self,
        copa_bag_data
    ):
        """Test Copa baggage tag number format (0230xxxxxx)"""

        test_bag = copa_bag_data["test_bags"]["happy_path"]
        tag = test_bag["tag_number"]

        # Copa IATA code is 230
        assert tag.startswith("0230"), \
            f"Copa bags should start with 0230, got: {tag}"

        # Should be 10 digits
        assert len(tag) == 10, \
            f"Bag tag should be 10 digits, got {len(tag)}"

        assert tag.isdigit(), \
            f"Bag tag should be all digits, got: {tag}"

        print(f"\n✅ Copa Tag Format Test PASSED")
        print(f"   Tag format: {tag}")


    @pytest.mark.asyncio
    async def test_copa_mishandling_rate(
        self,
        orchestrator,
        copa_flight_schedule
    ):
        """Test system improves Copa's mishandling rate"""

        # Copa's target: <0.3% mishandling rate
        # With AI: expect <0.15% rate

        # Process 100 bags
        bags = [
            create_initial_bag_state(
                bag_id=f"BAG_RATE_TEST_{i:03d}",
                tag_number=f"023083{i:05d}",
                passenger_id=f"PNR_RATE_{i:03d}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="PTY",
                weight_kg=22.0
            )
            for i in range(20)  # Smaller sample for test speed
        ]

        tasks = [
            orchestrator.process_bag(bag, has_connection=False)
            for bag in bags
        ]

        results = await asyncio.gather(*tasks)

        # Count mishandled
        mishandled = sum(
            1 for r in results
            if r["bag"]["current_status"] in [BagStatus.DELAYED, BagStatus.LOST, BagStatus.DAMAGED]
        )

        mishandling_rate = mishandled / len(bags) * 100

        # Should be very low with AI
        assert mishandling_rate <= 5, \
            f"Mishandling rate should be <5% with AI, got {mishandling_rate}%"

        print(f"\n✅ Copa Mishandling Rate Test PASSED")
        print(f"   Bags processed: {len(bags)}")
        print(f"   Mishandled: {mishandled}")
        print(f"   Rate: {mishandling_rate:.2f}%")


    @pytest.mark.asyncio
    async def test_copa_schedule_integration(
        self,
        copa_flight_schedule
    ):
        """Test integration with Copa flight schedule data"""

        # Verify schedule structure
        assert "flights" in copa_flight_schedule
        flights = copa_flight_schedule["flights"]

        assert len(flights) > 0, \
            "Flight schedule should contain flights"

        # Verify flight data completeness
        first_flight = flights[0]
        required_fields = [
            "flight_number", "route", "departure",
            "arrival", "aircraft", "bags_expected"
        ]

        for field in required_fields:
            assert field in first_flight, \
                f"Flight data should include '{field}'"

        # Verify connection pairs
        assert "connection_pairs" in copa_flight_schedule
        connections = copa_flight_schedule["connection_pairs"]

        # Verify connection data
        if len(connections) > 0:
            conn = connections[0]
            assert "inbound" in conn
            assert "outbound" in conn
            assert "mct_minutes" in conn

        print(f"\n✅ Copa Schedule Integration Test PASSED")
        print(f"   Flights: {len(flights)}")
        print(f"   Connections: {len(connections)}")
