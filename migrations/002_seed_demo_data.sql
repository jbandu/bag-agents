-- Migration 002: Seed Demo Data
-- Sample data for Copa Airlines AI Agent System Demo
-- Run with: psql 'postgresql://...' -f migrations/002_seed_demo_data.sql

BEGIN;

-- ============================================================================
-- PASSENGERS
-- ============================================================================

INSERT INTO passengers (id, pnr, name, email, phone, loyalty_tier, loyalty_number) VALUES
('a0000001-0000-0000-0000-000000000001', 'ABC123', 'Juan Martinez', 'juan.martinez@email.com', '+507-6123-4567', 'Diamond', 'CM1234567'),
('a0000001-0000-0000-0000-000000000002', 'DEF456', 'Maria Rodriguez', 'maria.rodriguez@email.com', '+507-6234-5678', 'Platinum', 'CM2345678'),
('a0000001-0000-0000-0000-000000000003', 'GHI789', 'Carlos Sanchez', 'carlos.sanchez@email.com', '+57-310-123-4567', 'Gold', 'CM3456789'),
('a0000001-0000-0000-0000-000000000004', 'JKL012', 'Ana Lopez', 'ana.lopez@email.com', '+1-786-234-5678', 'Silver', 'CM4567890'),
('a0000001-0000-0000-0000-000000000005', 'MNO345', 'Roberto Gomez', 'roberto.gomez@email.com', '+507-6345-6789', 'Standard', NULL),
('a0000001-0000-0000-0000-000000000006', 'PQR678', 'Sofia Fernandez', 'sofia.f@email.com', '+1-305-345-6789', 'Standard', NULL),
('a0000001-0000-0000-0000-000000000007', 'STU901', 'Diego Ramirez', 'diego.r@email.com', '+57-320-234-5678', 'Gold', 'CM5678901'),
('a0000001-0000-0000-0000-000000000008', 'VWX234', 'Isabella Torres', 'isabella.t@email.com', '+507-6456-7890', 'Platinum', 'CM6789012'),
('a0000001-0000-0000-0000-000000000009', 'YZA567', 'Miguel Vargas', 'miguel.v@email.com', '+1-954-456-7890', 'Standard', NULL),
('a0000001-0000-0000-0000-000000000010', 'BCD890', 'Camila Herrera', 'camila.h@email.com', '+507-6567-8901', 'Diamond', 'CM7890123')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- FLIGHTS
-- ============================================================================

INSERT INTO flights (id, flight_number, airline_code, departure_airport, arrival_airport, scheduled_departure, scheduled_arrival, actual_departure, status, gate) VALUES
('b0000001-0000-0000-0000-000000000001', 'CM123', 'CM', 'BOG', 'PTY', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '2 hours', 'arrived', 'A3'),
('b0000001-0000-0000-0000-000000000002', 'CM456', 'CM', 'PTY', 'JFK', NOW() + INTERVAL '1 hour', NOW() + INTERVAL '6 hours', NULL, 'boarding', 'B2'),
('b0000001-0000-0000-0000-000000000003', 'CM789', 'CM', 'MIA', 'PTY', NOW() - INTERVAL '30 minutes', NOW() + INTERVAL '2 hours', NOW() - INTERVAL '30 minutes', 'in_flight', 'A1'),
('b0000001-0000-0000-0000-000000000004', 'CM234', 'CM', 'PTY', 'BOG', NOW() + INTERVAL '3 hours', NOW() + INTERVAL '5 hours', NULL, 'scheduled', 'B4'),
('b0000001-0000-0000-0000-000000000005', 'CM567', 'CM', 'LIM', 'PTY', NOW() - INTERVAL '1 hour', NOW() + INTERVAL '1 hour', NOW() - INTERVAL '1 hour', 'in_flight', 'A2'),
('b0000001-0000-0000-0000-000000000006', 'CM890', 'CM', 'PTY', 'MIA', NOW() + INTERVAL '2 hours', NOW() + INTERVAL '5 hours', NULL, 'scheduled', 'B3'),
('b0000001-0000-0000-0000-000000000007', 'CM345', 'CM', 'MEX', 'PTY', NOW() + INTERVAL '4 hours', NOW() + INTERVAL '8 hours', NULL, 'scheduled', 'A4'),
('b0000001-0000-0000-0000-000000000008', 'CM678', 'CM', 'PTY', 'GRU', NOW() + INTERVAL '5 hours', NOW() + INTERVAL '13 hours', NULL, 'scheduled', 'B1')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- BAGS
-- ============================================================================

INSERT INTO bags (id, tag_number, passenger_id, flight_id, status, risk_level, current_location, destination, weight_kg, connection_time_minutes) VALUES
-- At-risk bag: tight connection BOG->PTY->JFK
('c0000001-0000-0000-0000-000000000001', '0230556789', 'a0000001-0000-0000-0000-000000000001', 'b0000001-0000-0000-0000-000000000002', 'in_transit', 'high', 'SORT_HUB_A', 'JFK', 23.5, 45),

-- Normal bags
('c0000001-0000-0000-0000-000000000002', '0230556790', 'a0000001-0000-0000-0000-000000000002', 'b0000001-0000-0000-0000-000000000002', 'loaded', 'low', 'GATE_B2', 'JFK', 18.2, 120),
('c0000001-0000-0000-0000-000000000003', '0230556791', 'a0000001-0000-0000-0000-000000000003', 'b0000001-0000-0000-0000-000000000003', 'in_transit', 'medium', 'TRANSFER_POINT_1', 'PTY', 22.0, 90),
('c0000001-0000-0000-0000-000000000004', '0230556792', 'a0000001-0000-0000-0000-000000000004', 'b0000001-0000-0000-0000-000000000004', 'checked', 'low', 'CHECK_IN_2', 'BOG', 19.5, 180),
('c0000001-0000-0000-0000-000000000005', '0230556793', 'a0000001-0000-0000-0000-000000000005', 'b0000001-0000-0000-0000-000000000005', 'in_transit', 'low', 'GATE_A2', 'PTY', 21.8, 150),

-- Delayed bag
('c0000001-0000-0000-0000-000000000006', '0230556794', 'a0000001-0000-0000-0000-000000000006', 'b0000001-0000-0000-0000-000000000001', 'delayed', 'critical', 'SORT_HUB_B', 'PTY', 25.0, 30),

-- VIP passenger bags
('c0000001-0000-0000-0000-000000000007', '0230556795', 'a0000001-0000-0000-0000-000000000008', 'b0000001-0000-0000-0000-000000000006', 'checked', 'low', 'CHECK_IN_1', 'MIA', 20.5, 240),
('c0000001-0000-0000-0000-000000000008', '0230556796', 'a0000001-0000-0000-0000-000000000010', 'b0000001-0000-0000-0000-000000000008', 'checked', 'low', 'CHECK_IN_3', 'GRU', 22.5, 300)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- BAG EVENTS
-- ============================================================================

INSERT INTO bag_events (bag_id, event_type, location, timestamp, equipment_id) VALUES
-- Events for at-risk bag
('c0000001-0000-0000-0000-000000000001', 'checked', 'BOG_CHECK_IN_5', NOW() - INTERVAL '3 hours', 'CHECK-BOG-05'),
('c0000001-0000-0000-0000-000000000001', 'loaded', 'BOG_GATE_12', NOW() - INTERVAL '2 hours 15 minutes', 'LOADER-BOG-03'),
('c0000001-0000-0000-0000-000000000001', 'transferred', 'PTY_TRANSFER_1', NOW() - INTERVAL '45 minutes', 'CART-01'),
('c0000001-0000-0000-0000-000000000001', 'sorting', 'SORT_HUB_A', NOW() - INTERVAL '30 minutes', 'SORT-A'),

-- Events for delayed bag
('c0000001-0000-0000-0000-000000000006', 'checked', 'MIA_CHECK_IN_3', NOW() - INTERVAL '4 hours', 'CHECK-MIA-03'),
('c0000001-0000-0000-0000-000000000006', 'loaded', 'MIA_GATE_8', NOW() - INTERVAL '3 hours', 'LOADER-MIA-02'),
('c0000001-0000-0000-0000-000000000006', 'transferred', 'PTY_TRANSFER_2', NOW() - INTERVAL '1 hour 30 minutes', 'CART-03'),
('c0000001-0000-0000-0000-000000000006', 'sorting', 'SORT_HUB_B', NOW() - INTERVAL '1 hour', 'SORT-B'),
('c0000001-0000-0000-0000-000000000006', 'delayed', 'SORT_HUB_B', NOW() - INTERVAL '30 minutes', 'SORT-B'),

-- Events for normal bags
('c0000001-0000-0000-0000-000000000002', 'checked', 'PTY_CHECK_IN_1', NOW() - INTERVAL '2 hours', 'CHECK-PTY-01'),
('c0000001-0000-0000-0000-000000000002', 'sorting', 'SORT_HUB_A', NOW() - INTERVAL '1 hour 30 minutes', 'SORT-A'),
('c0000001-0000-0000-0000-000000000002', 'loaded', 'GATE_B2', NOW() - INTERVAL '15 minutes', 'LOADER-PTY-05')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- EQUIPMENT
-- ============================================================================

INSERT INTO equipment (equipment_id, equipment_type, airport_code, location, status, health_score, utilization, installed_date, last_maintenance) VALUES
-- Carousels
('CAR-01', 'baggage_carousel', 'PTY', 'Terminal 1', 'operational', 92, 0.68, '2022-01-15', NOW() - INTERVAL '35 days'),
('CAR-02', 'baggage_carousel', 'PTY', 'Terminal 1', 'operational', 88, 0.72, '2022-01-15', NOW() - INTERVAL '40 days'),
('CAR-03', 'baggage_carousel', 'PTY', 'Terminal 2', 'operational', 85, 0.75, '2021-06-20', NOW() - INTERVAL '55 days'),

-- Sorting systems
('SORT-A', 'sorting_system', 'PTY', 'Sorting Hub A', 'degraded', 73, 0.85, '2020-03-10', NOW() - INTERVAL '48 days'),
('SORT-B', 'sorting_system', 'PTY', 'Sorting Hub B', 'operational', 90, 0.78, '2021-11-05', NOW() - INTERVAL '30 days'),

-- Scanners
('SCAN-01', 'scanner', 'PTY', 'Gate A1', 'operational', 95, 0.65, '2023-01-10', NOW() - INTERVAL '70 days'),
('SCAN-02', 'scanner', 'PTY', 'Gate A2', 'operational', 93, 0.68, '2023-01-10', NOW() - INTERVAL '70 days'),
('SCAN-03', 'scanner', 'PTY', 'Gate B1', 'operational', 94, 0.70, '2023-02-15', NOW() - INTERVAL '65 days'),

-- Conveyors
('CONV-01', 'conveyor_belt', 'PTY', 'Section A', 'operational', 87, 0.73, '2020-08-20', NOW() - INTERVAL '28 days'),
('CONV-02', 'conveyor_belt', 'PTY', 'Section B', 'operational', 82, 0.76, '2020-08-20', NOW() - INTERVAL '32 days'),
('CONV-03', 'conveyor_belt', 'PTY', 'Section C', 'degraded', 68, 0.88, '2019-05-15', NOW() - INTERVAL '45 days'),

-- Tugs and carts
('TUG-01', 'tug', 'PTY', 'Ramp Area 1', 'operational', 78, 0.62, '2022-07-10', NOW() - INTERVAL '25 days'),
('CART-01', 'cart', 'PTY', 'Transfer Point 1', 'operational', 90, 0.55, '2023-03-20', NOW() - INTERVAL '85 days')
ON CONFLICT (equipment_id) DO NOTHING;

-- ============================================================================
-- EQUIPMENT METRICS (Recent data)
-- ============================================================================

INSERT INTO equipment_metrics (equipment_id, throughput, error_rate, utilization, temperature, vibration_level, timestamp)
SELECT
    'SORT-A',
    800 + (random() * 200)::int,
    0.01 + (random() * 0.04),
    0.75 + (random() * 0.15),
    40 + (random() * 15),
    0.15 + (random() * 0.15),
    NOW() - (interval '1 minute' * generate_series)
FROM generate_series(0, 100, 10);

-- ============================================================================
-- INCIDENTS
-- ============================================================================

INSERT INTO incidents (id, pir_number, bag_id, incident_type, description, severity, status, root_cause, created_at) VALUES
('d0000001-0000-0000-0000-000000000001', 'PTY-20241116-0001', 'c0000001-0000-0000-0000-000000000006', 'delayed', 'Bag missed connection due to tight transfer time', 'high', 'open', 'transfer_time_insufficient', NOW() - INTERVAL '2 hours'),
('d0000001-0000-0000-0000-000000000002', 'PTY-20241115-0023', NULL, 'damaged', 'Bag carousel malfunction caused damage', 'medium', 'resolved', 'equipment_failure', NOW() - INTERVAL '1 day'),
('d0000001-0000-0000-0000-000000000003', 'PTY-20241114-0045', NULL, 'lost', 'Bag routing error to wrong destination', 'high', 'resolved', 'routing_error', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- COMPENSATION CLAIMS
-- ============================================================================

INSERT INTO compensation_claims (claim_number, incident_id, passenger_id, claimed_amount, approval_status, fraud_risk_score, created_at) VALUES
('COMP-20241116-0001', 'd0000001-0000-0000-0000-000000000001', 'a0000001-0000-0000-0000-000000000006', 150.00, 'auto_approved', 0.15, NOW() - INTERVAL '1 hour'),
('COMP-20241115-0023', 'd0000001-0000-0000-0000-000000000002', 'a0000001-0000-0000-0000-000000000003', 350.00, 'pending_supervisor', 0.25, NOW() - INTERVAL '1 day'),
('COMP-20241114-0045', 'd0000001-0000-0000-0000-000000000003', 'a0000001-0000-0000-0000-000000000005', 800.00, 'pending_manager', 0.35, NOW() - INTERVAL '2 days')
ON CONFLICT (claim_number) DO NOTHING;

-- ============================================================================
-- CUSTOMER SERVICE INTERACTIONS
-- ============================================================================

INSERT INTO customer_service_interactions (passenger_id, bag_tag, channel, language, query, response, intent, sentiment, escalated) VALUES
('a0000001-0000-0000-0000-000000000006', '0230556794', 'web_chat', 'en', 'Where is my bag? It did not arrive with my flight.', 'I understand your bag hasn''t arrived. Let me check its current location...', 'bag_status', 'negative', FALSE),
('a0000001-0000-0000-0000-000000000003', NULL, 'email', 'es', '¿Puedo reclamar compensación por mi maleta dañada?', 'Sí, puede ser elegible para compensación. Le ayudaré a iniciar un reclamo...', 'compensation', 'neutral', FALSE),
('a0000001-0000-0000-0000-000000000001', '0230556789', 'whatsapp', 'en', 'My connecting bag shows as at-risk. Will it make my flight?', 'Your bag is currently being expedited through our system. Our AI predicts 85% chance of making your connection.', 'bag_status', 'neutral', FALSE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- WORK ORDERS
-- ============================================================================

INSERT INTO work_orders (work_order_number, equipment_id, maintenance_type, priority, status, description, scheduled_for) VALUES
('WO-20241116-1001', 'SORT-A', 'preventive', 'high', 'open', 'Belt tension adjustment and lubrication - predicted failure detected', NOW() + INTERVAL '2 days'),
('WO-20241116-1002', 'CONV-03', 'corrective', 'critical', 'open', 'Immediate inspection required - performance degradation', NOW() + INTERVAL '6 hours'),
('WO-20241115-2034', 'CAR-03', 'preventive', 'medium', 'completed', 'Routine inspection and cleaning', NOW() - INTERVAL '1 day')
ON CONFLICT (work_order_number) DO NOTHING;

COMMIT;

-- Success message
SELECT '✅ Demo data seeded successfully!' as status;
SELECT 'Passengers: ' || COUNT(*) FROM passengers UNION ALL
SELECT 'Flights: ' || COUNT(*) FROM flights UNION ALL
SELECT 'Bags: ' || COUNT(*) FROM bags UNION ALL
SELECT 'Equipment: ' || COUNT(*) FROM equipment UNION ALL
SELECT 'Incidents: ' || COUNT(*) FROM incidents UNION ALL
SELECT 'Claims: ' || COUNT(*) FROM compensation_claims;
