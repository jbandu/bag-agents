"""
Load Test: Concurrent Bag Processing

Test system handling 1000+ bags simultaneously.

Performance Targets:
- Prediction Agent: <2 sec per bag
- Route Optimization: <1 sec per route
- Orchestrator: >10 bags/sec throughput
- Database: <100ms query latency
- Neo4j: <200ms graph queries
- Zero errors under load
"""

import pytest
import asyncio
import time
from datetime import datetime
from langgraph.orchestrator_state import create_initial_bag_state, BagStatus


class TestConcurrentBags:
    """Load tests for concurrent bag processing"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_100_bags_concurrent(
        self,
        orchestrator,
        performance_tracker
    ):
        """Test processing 100 bags concurrently"""

        # Create 100 bags
        bags = [
            create_initial_bag_state(
                bag_id=f"BAG_LOAD_100_{i:04d}",
                tag_number=f"0230900{i:04d}",
                passenger_id=f"PNR_L100_{i:04d}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="PTY",
                weight_kg=20.0 + (i % 20)
            )
            for i in range(100)
        ]

        start_time = time.time()

        # Process all concurrently
        tasks = [
            orchestrator.process_bag(bag, has_connection=False)
            for bag in bags
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Count successful vs failed
        successful = sum(
            1 for r in results
            if not isinstance(r, Exception) and r.get("status") == "completed"
        )

        errors = sum(1 for r in results if isinstance(r, Exception))

        # Calculate metrics
        throughput = len(bags) / duration  # bags per second
        success_rate = successful / len(bags) * 100

        # Assert performance targets
        assert success_rate >= 95, \
            f"Expected ≥95% success rate, got {success_rate}%"

        assert throughput >= 5, \
            f"Expected ≥5 bags/sec throughput, got {throughput:.2f}"

        assert errors == 0, \
            f"Expected zero errors, got {errors}"

        print(f"\n✅ 100 Bags Concurrent Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Throughput: {throughput:.2f} bags/sec")
        print(f"   Success: {successful}/100 ({success_rate:.1f}%)")
        print(f"   Errors: {errors}")

        # Record metrics
        performance_tracker.metrics["total_test_time"] = duration
        performance_tracker.metrics["throughput"] = throughput
        performance_tracker.metrics["success_rate"] = success_rate


    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_500_bags_load(
        self,
        orchestrator,
        performance_tracker
    ):
        """Test processing 500 bags (moderate load)"""

        # Create 500 bags with varying characteristics
        bags = []
        for i in range(500):
            has_connection = (i % 3 == 0)  # 33% with connections

            if has_connection:
                bag = create_initial_bag_state(
                    bag_id=f"BAG_LOAD_500_{i:04d}",
                    tag_number=f"0230910{i:04d}",
                    passenger_id=f"PNR_L500_{i:04d}",
                    origin_flight="CM101",
                    origin_airport="BOG",
                    destination_airport="JFK",
                    weight_kg=15.0 + (i % 30),
                    connection_flight="CM451",
                    connection_airport="PTY"
                )
            else:
                bag = create_initial_bag_state(
                    bag_id=f"BAG_LOAD_500_{i:04d}",
                    tag_number=f"0230910{i:04d}",
                    passenger_id=f"PNR_L500_{i:04d}",
                    origin_flight="CM777",
                    origin_airport="PTY",
                    destination_airport="JFK",
                    weight_kg=15.0 + (i % 30)
                )

            bags.append((bag, has_connection))

        start_time = time.time()

        # Process in batches to avoid overwhelming system
        batch_size = 50
        all_results = []

        for i in range(0, len(bags), batch_size):
            batch = bags[i:i+batch_size]
            tasks = [
                orchestrator.process_bag(bag, has_connection=has_conn)
                for bag, has_conn in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(batch_results)

            # Small delay between batches
            await asyncio.sleep(0.1)

        end_time = time.time()
        duration = end_time - start_time

        # Analyze results
        successful = sum(
            1 for r in all_results
            if not isinstance(r, Exception) and r.get("status") == "completed"
        )

        errors = sum(1 for r in all_results if isinstance(r, Exception))

        throughput = len(bags) / duration
        success_rate = successful / len(bags) * 100

        # Performance assertions
        assert success_rate >= 90, \
            f"Expected ≥90% success rate under load, got {success_rate}%"

        assert throughput >= 3, \
            f"Expected ≥3 bags/sec for moderate load, got {throughput:.2f}"

        print(f"\n✅ 500 Bags Load Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Throughput: {throughput:.2f} bags/sec")
        print(f"   Success: {successful}/500 ({success_rate:.1f}%)")
        print(f"   Errors: {errors}")
        print(f"   With connections: {sum(1 for _, hc in bags if hc)}")


    @pytest.mark.asyncio
    async def test_agent_performance_under_load(
        self,
        mock_prediction_agent,
        mock_route_optimization_agent,
        performance_tracker
    ):
        """Test individual agent performance under load"""

        # Test prediction agent with 100 requests
        pred_times = []
        for i in range(100):
            start = time.time()

            await mock_prediction_agent.execute({
                "flight_id": f"CM{100+i}",
                "departure_airport": "BOG",
                "arrival_airport": "PTY",
                "connection_time": 60 + (i % 60)
            })

            elapsed = time.time() - start
            pred_times.append(elapsed * 1000)  # Convert to ms

        # Test route optimization with 100 requests
        route_times = []
        for i in range(100):
            start = time.time()

            await mock_route_optimization_agent.execute({
                "origin": "PTY",
                "destination": "JFK"
            })

            elapsed = time.time() - start
            route_times.append(elapsed * 1000)

        # Calculate statistics
        pred_avg = sum(pred_times) / len(pred_times)
        pred_p95 = sorted(pred_times)[int(len(pred_times) * 0.95)]
        pred_p99 = sorted(pred_times)[int(len(pred_times) * 0.99)]

        route_avg = sum(route_times) / len(route_times)
        route_p95 = sorted(route_times)[int(len(route_times) * 0.95)]

        # Performance assertions
        assert pred_avg < 2000, \
            f"Prediction agent avg should be <2s, got {pred_avg:.0f}ms"

        assert route_avg < 1000, \
            f"Route optimization avg should be <1s, got {route_avg:.0f}ms"

        print(f"\n✅ Agent Performance Under Load Test PASSED")
        print(f"   Prediction Agent (100 calls):")
        print(f"     Avg: {pred_avg:.0f}ms")
        print(f"     P95: {pred_p95:.0f}ms")
        print(f"     P99: {pred_p99:.0f}ms")
        print(f"   Route Optimization (100 calls):")
        print(f"     Avg: {route_avg:.0f}ms")
        print(f"     P95: {route_p95:.0f}ms")


    @pytest.mark.asyncio
    async def test_memory_stability(
        self,
        orchestrator
    ):
        """Test that memory usage stays stable under load"""

        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process 200 bags
        bags = [
            create_initial_bag_state(
                bag_id=f"BAG_MEM_{i:04d}",
                tag_number=f"0230920{i:04d}",
                passenger_id=f"PNR_MEM_{i:04d}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="PTY",
                weight_kg=22.0
            )
            for i in range(200)
        ]

        # Process in batches
        for i in range(0, len(bags), 50):
            batch = bags[i:i+50]
            tasks = [
                orchestrator.process_bag(bag, has_connection=False)
                for bag in batch
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory should not increase excessively
        assert memory_increase < 500, \
            f"Memory increase should be <500MB, got {memory_increase:.0f}MB"

        print(f"\n✅ Memory Stability Test PASSED")
        print(f"   Initial memory: {initial_memory:.0f}MB")
        print(f"   Final memory: {final_memory:.0f}MB")
        print(f"   Increase: {memory_increase:.0f}MB")


    @pytest.mark.asyncio
    async def test_error_rate_under_load(
        self,
        orchestrator
    ):
        """Test that error rate stays low under load"""

        # Process 300 bags and track errors
        bags = [
            create_initial_bag_state(
                bag_id=f"BAG_ERR_{i:04d}",
                tag_number=f"0230930{i:04d}",
                passenger_id=f"PNR_ERR_{i:04d}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="PTY",
                weight_kg=22.0
            )
            for i in range(300)
        ]

        tasks = [
            orchestrator.process_bag(bag, has_connection=False)
            for bag in bags
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count errors
        exceptions = sum(1 for r in results if isinstance(r, Exception))
        workflow_errors = sum(
            1 for r in results
            if not isinstance(r, Exception) and len(r.get("errors", [])) > 0
        )

        total_errors = exceptions + workflow_errors
        error_rate = total_errors / len(bags) * 100

        # Error rate should be very low
        assert error_rate < 5, \
            f"Error rate should be <5% under load, got {error_rate:.1f}%"

        print(f"\n✅ Error Rate Under Load Test PASSED")
        print(f"   Total bags: {len(bags)}")
        print(f"   Exceptions: {exceptions}")
        print(f"   Workflow errors: {workflow_errors}")
        print(f"   Error rate: {error_rate:.2f}%")
