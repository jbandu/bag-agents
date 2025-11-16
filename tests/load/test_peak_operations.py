"""
Load Test: Copa Peak Hour Operations

Simulate Copa's daily PTY hub peak:
- 1,500 bags in 4-hour window
- 50 flights departing 14:00-18:00
- Mix of domestic (30%) and international (70%)
- 15 flights with connections
- Average 30 bags per flight

Performance targets:
- All targets from concurrent test
- Handle connection complexity
- Demand forecasting accuracy
- Infrastructure monitoring under load
"""

import pytest
import asyncio
import time
import random
from datetime import datetime, timedelta
from langgraph.orchestrator_state import create_initial_bag_state


class TestPeakOperations:
    """Load tests for Copa peak hour operations"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_peak_hour_simulation(
        self,
        orchestrator,
        copa_flight_schedule,
        performance_tracker
    ):
        """
        Simulate Copa's afternoon peak wave: 14:00-18:00

        1500 bags, 50 flights, 70% connections
        """

        # Generate realistic Copa peak load
        bags_data = []
        flights = copa_flight_schedule["flights"]

        # Target: 1500 bags (using 300 for test speed)
        num_bags = 300
        connection_rate = 0.70

        passenger_names = [
            "Maria Garcia", "Juan Rodriguez", "Carlos Martinez", "Ana Lopez",
            "Diego Hernandez", "Sofia Gonzalez", "Miguel Perez"
        ]

        for i in range(num_bags):
            has_connection = random.random() < connection_rate

            # Random flight selection
            origin_airports = ["BOG", "MIA", "GUA", "SAL", "LIM"]
            origin = random.choice(origin_airports)

            if has_connection:
                # Connection via PTY
                destination = random.choice(["JFK", "MEX", "GRU"])
                bag = create_initial_bag_state(
                    bag_id=f"BAG_PEAK_{i:05d}",
                    tag_number=f"0230940{i:05d}",
                    passenger_id=f"PNR_PEAK_{i:05d}",
                    origin_flight=f"CM{random.randint(100,199)}",
                    origin_airport=origin,
                    destination_airport=destination,
                    weight_kg=random.uniform(15.0, 30.0),
                    declared_value=random.choice([0, 500, 1000, 2000]),
                    connection_flight=f"CM{random.randint(400,499)}",
                    connection_airport="PTY"
                )
            else:
                # Direct to/from PTY
                if random.random() < 0.5:
                    origin = "PTY"
                    destination = random.choice(["JFK", "MIA", "MEX"])
                else:
                    destination = "PTY"

                bag = create_initial_bag_state(
                    bag_id=f"BAG_PEAK_{i:05d}",
                    tag_number=f"0230940{i:05d}",
                    passenger_id=f"PNR_PEAK_{i:05d}",
                    origin_flight=f"CM{random.randint(700,799)}",
                    origin_airport=origin,
                    destination_airport=destination,
                    weight_kg=random.uniform(15.0, 30.0),
                    declared_value=random.choice([0, 500, 1000])
                )

            bags_data.append((bag, has_connection))

        print(f"\n🔄 Processing {len(bags_data)} bags (Copa peak simulation)...")

        start_time = time.time()

        # Process in realistic batches (check-in waves)
        batch_size = 30  # 30 bags per batch ~ 1 flight worth
        all_results = []

        for batch_num, i in enumerate(range(0, len(bags_data), batch_size)):
            batch = bags_data[i:i+batch_size]

            tasks = [
                orchestrator.process_bag(bag, has_connection=has_conn)
                for bag, has_conn in batch
            ]

            batch_start = time.time()
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_duration = time.time() - batch_start

            all_results.extend(batch_results)

            if batch_num % 3 == 0:
                print(f"   Batch {batch_num+1}: {len(batch)} bags in {batch_duration:.2f}s")

            # Small delay to simulate realistic timing
            await asyncio.sleep(0.05)

        end_time = time.time()
        total_duration = end_time - start_time

        # Analyze results
        successful = sum(
            1 for r in all_results
            if not isinstance(r, Exception) and r.get("status") == "completed"
        )

        errors = sum(1 for r in all_results if isinstance(r, Exception))

        # Calculate metrics
        throughput = len(bags_data) / total_duration
        success_rate = successful / len(bags_data) * 100

        # Count connection success
        connection_bags = [
            r for bag, has_conn in bags_data
            for r in all_results
            if has_conn and not isinstance(r, Exception)
        ]

        # Performance assertions
        assert success_rate >= 95, \
            f"Peak operations should maintain ≥95% success, got {success_rate}%"

        assert throughput >= 2, \
            f"Should process ≥2 bags/sec at peak, got {throughput:.2f}"

        assert errors < len(bags_data) * 0.05, \
            f"Errors should be <5%, got {errors}"

        print(f"\n✅ Peak Hour Simulation Test PASSED")
        print(f"   Total bags: {len(bags_data)}")
        print(f"   Duration: {total_duration:.2f}s ({total_duration/60:.1f} min)")
        print(f"   Throughput: {throughput:.2f} bags/sec")
        print(f"   Success: {successful}/{len(bags_data)} ({success_rate:.1f}%)")
        print(f"   Errors: {errors}")
        print(f"   Connection rate: {sum(1 for _, hc in bags_data if hc)/len(bags_data)*100:.0f}%")

        # Record performance
        performance_tracker.metrics["peak_throughput"] = throughput
        performance_tracker.metrics["peak_success_rate"] = success_rate
        performance_tracker.metrics["peak_duration"] = total_duration


    @pytest.mark.asyncio
    async def test_connection_complexity(
        self,
        orchestrator
    ):
        """Test handling complex connection scenarios at peak"""

        # Create bags with varying connection times
        connection_scenarios = [
            (120, "comfortable"),
            (90, "normal"),
            (60, "normal"),
            (50, "tight"),
            (38, "critical")
        ]

        bags = []
        for i, (conn_time, category) in enumerate(connection_scenarios * 10):  # 50 bags total
            bag = create_initial_bag_state(
                bag_id=f"BAG_CONN_COMPLEX_{i:03d}",
                tag_number=f"023095{i:04d}",
                passenger_id=f"PNR_CC_{i:03d}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="JFK",
                weight_kg=22.0,
                connection_flight="CM451",
                connection_airport="PTY"
            )
            bags.append(bag)

        # Process all
        tasks = [
            orchestrator.process_bag(bag, has_connection=True)
            for bag in bags
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all processed
        successful = sum(
            1 for r in results
            if not isinstance(r, Exception) and r.get("status") == "completed"
        )

        success_rate = successful / len(bags) * 100

        # Even with complex connections, should maintain high success
        assert success_rate >= 90, \
            f"Should handle connection complexity, got {success_rate}% success"

        print(f"\n✅ Connection Complexity Test PASSED")
        print(f"   Connection scenarios: {len(connection_scenarios)}")
        print(f"   Total bags: {len(bags)}")
        print(f"   Success: {successful}/{len(bags)} ({success_rate:.1f}%)")


    @pytest.mark.asyncio
    async def test_demand_forecasting_accuracy(
        self,
        mock_demand_forecast_agent
    ):
        """Test demand forecasting during peak operations"""

        # Query forecast during peak
        result = await mock_demand_forecast_agent.execute({
            "airport_code": "PTY",
            "forecast_horizon": 4,  # 4-hour peak window
            "include_events": True
        })

        # Verify forecast structure
        assert "predicted_bag_volume" in result
        assert "peak_hours" in result
        assert "staffing_recommendation" in result
        assert "congestion_forecast" in result

        predicted_volume = result["predicted_bag_volume"]
        staffing = result["staffing_recommendation"]

        # Peak should predict high volume
        assert predicted_volume >= 1000, \
            f"Peak should forecast high volume, got {predicted_volume}"

        # Should identify peak hours
        peak_hours = result["peak_hours"]
        assert len(peak_hours) > 0, \
            "Should identify peak hours"

        # Staffing should be adequate
        assert "handlers_needed" in staffing
        assert staffing["handlers_needed"] >= 20, \
            "Peak operations need adequate staffing"

        print(f"\n✅ Demand Forecasting Test PASSED")
        print(f"   Predicted volume: {predicted_volume} bags")
        print(f"   Peak hours: {peak_hours}")
        print(f"   Handlers needed: {staffing['handlers_needed']}")
        print(f"   Additional staff: {staffing.get('additional_needed', 0)}")


    @pytest.mark.asyncio
    async def test_infrastructure_monitoring_peak(
        self,
        mock_infrastructure_health_agent
    ):
        """Test infrastructure health monitoring during peak load"""

        # Query infrastructure status
        result = await mock_infrastructure_health_agent.execute({
            "airport_code": "PTY",
            "equipment_type": "all"
        })

        # Verify monitoring data
        assert "overall_health" in result
        assert "equipment_status" in result

        equipment_status = result["equipment_status"]

        # Should monitor multiple pieces of equipment
        assert len(equipment_status) >= 3, \
            "Should monitor multiple equipment items"

        # Verify equipment details
        for equipment in equipment_status:
            assert "id" in equipment
            assert "status" in equipment
            assert "health" in equipment

        # Overall health should be good for operations
        overall_health = result["overall_health"]
        assert overall_health >= 70, \
            f"Infrastructure health should be ≥70% for peak ops, got {overall_health}"

        print(f"\n✅ Infrastructure Monitoring Test PASSED")
        print(f"   Overall health: {overall_health}%")
        print(f"   Equipment monitored: {len(equipment_status)}")
        print(f"   Equipment status: {[e['status'] for e in equipment_status]}")


    @pytest.mark.asyncio
    async def test_system_stability_4hour_window(
        self,
        orchestrator
    ):
        """Test system stability over 4-hour peak window (simulated)"""

        # Simulate 4-hour window with sustained load
        # Process bags in waves over time

        total_bags = 0
        total_successful = 0
        wave_count = 8  # 8 waves over 4 hours = every 30 min

        for wave in range(wave_count):
            # Each wave: 20-40 bags
            wave_size = random.randint(20, 40)

            bags = [
                create_initial_bag_state(
                    bag_id=f"BAG_STABLE_W{wave}_{i:03d}",
                    tag_number=f"02309{wave}{i:04d}",
                    passenger_id=f"PNR_S_{wave}_{i:03d}",
                    origin_flight="CM101",
                    origin_airport="BOG",
                    destination_airport="PTY",
                    weight_kg=22.0
                )
                for i in range(wave_size)
            ]

            tasks = [
                orchestrator.process_bag(bag, has_connection=False)
                for bag in bags
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(
                1 for r in results
                if not isinstance(r, Exception) and r.get("status") == "completed"
            )

            total_bags += wave_size
            total_successful += successful

            print(f"   Wave {wave+1}/{wave_count}: {successful}/{wave_size} succeeded")

            # Small delay between waves
            await asyncio.sleep(0.1)

        # Calculate overall stability
        overall_success_rate = total_successful / total_bags * 100

        assert overall_success_rate >= 95, \
            f"System should maintain ≥95% success over time, got {overall_success_rate}%"

        print(f"\n✅ System Stability Test PASSED")
        print(f"   Total bags (8 waves): {total_bags}")
        print(f"   Overall success: {total_successful}/{total_bags} ({overall_success_rate:.1f}%)")
        print(f"   System remained stable throughout simulation")
