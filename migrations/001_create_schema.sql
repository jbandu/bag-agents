-- Migration 001: Create Baggage Operations Database Schema
-- For Copa Airlines AI Agent System
-- Run with: psql 'postgresql://...' -f migrations/001_create_schema.sql

BEGIN;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Passengers table
CREATE TABLE IF NOT EXISTS passengers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pnr VARCHAR(6) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    loyalty_tier VARCHAR(20) DEFAULT 'Standard',
    loyalty_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_passengers_pnr ON passengers(pnr);
CREATE INDEX idx_passengers_loyalty_tier ON passengers(loyalty_tier);

-- Flights table
CREATE TABLE IF NOT EXISTS flights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flight_number VARCHAR(10) NOT NULL,
    airline_code VARCHAR(3) DEFAULT 'CM',
    departure_airport VARCHAR(3) NOT NULL,
    arrival_airport VARCHAR(3) NOT NULL,
    scheduled_departure TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_arrival TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_departure TIMESTAMP WITH TIME ZONE,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'scheduled',
    gate VARCHAR(10),
    aircraft_type VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_flights_number ON flights(flight_number);
CREATE INDEX idx_flights_departure ON flights(departure_airport, scheduled_departure);
CREATE INDEX idx_flights_arrival ON flights(arrival_airport, scheduled_arrival);
CREATE INDEX idx_flights_status ON flights(status);

-- Bags table
CREATE TABLE IF NOT EXISTS bags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_number VARCHAR(10) UNIQUE NOT NULL,
    passenger_id UUID REFERENCES passengers(id) ON DELETE CASCADE,
    flight_id UUID REFERENCES flights(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'checked',
    risk_level VARCHAR(20) DEFAULT 'low',
    current_location VARCHAR(100),
    destination VARCHAR(3),
    destination_gate VARCHAR(10),
    weight_kg DECIMAL(5,2),
    special_handling BOOLEAN DEFAULT FALSE,
    priority VARCHAR(20) DEFAULT 'normal',
    connection_time_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bags_tag ON bags(tag_number);
CREATE INDEX idx_bags_passenger ON bags(passenger_id);
CREATE INDEX idx_bags_flight ON bags(flight_id);
CREATE INDEX idx_bags_status ON bags(status);
CREATE INDEX idx_bags_risk_level ON bags(risk_level);
CREATE INDEX idx_bags_destination ON bags(destination);

-- Bag Events table
CREATE TABLE IF NOT EXISTS bag_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bag_id UUID REFERENCES bags(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    equipment_id VARCHAR(50),
    handler_id VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bag_events_bag ON bag_events(bag_id);
CREATE INDEX idx_bag_events_timestamp ON bag_events(timestamp DESC);
CREATE INDEX idx_bag_events_type ON bag_events(event_type);
CREATE INDEX idx_bag_events_location ON bag_events(location);

-- ============================================================================
-- INCIDENT MANAGEMENT
-- ============================================================================

-- Incidents table (for mishandled bags and PIRs)
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pir_number VARCHAR(50) UNIQUE,
    bag_id UUID REFERENCES bags(id) ON DELETE CASCADE,
    incident_type VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    root_cause VARCHAR(100),
    root_cause_confidence DECIMAL(3,2),
    pattern_detected BOOLEAN DEFAULT FALSE,
    reported_by VARCHAR(100),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_incidents_pir ON incidents(pir_number);
CREATE INDEX idx_incidents_bag ON incidents(bag_id);
CREATE INDEX idx_incidents_type ON incidents(incident_type);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_created ON incidents(created_at DESC);
CREATE INDEX idx_incidents_root_cause ON incidents(root_cause);

-- Root Cause Analysis Results table
CREATE TABLE IF NOT EXISTS root_cause_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    cause VARCHAR(100) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    evidence JSONB,
    similar_incidents_count INTEGER DEFAULT 0,
    pattern_type VARCHAR(50),
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rca_incident ON root_cause_analysis(incident_id);
CREATE INDEX idx_rca_cause ON root_cause_analysis(cause);

-- ============================================================================
-- COMPENSATION & CLAIMS
-- ============================================================================

-- Compensation Claims table
CREATE TABLE IF NOT EXISTS compensation_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    passenger_id UUID REFERENCES passengers(id) ON DELETE CASCADE,
    claimed_amount DECIMAL(10,2) NOT NULL,
    approved_amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    approval_status VARCHAR(50) DEFAULT 'pending',
    approver_required VARCHAR(50),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    fraud_risk_score DECIMAL(3,2),
    fraud_indicators JSONB,
    breakdown JSONB,
    receipt_analysis JSONB,
    expected_resolution_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_claims_number ON compensation_claims(claim_number);
CREATE INDEX idx_claims_incident ON compensation_claims(incident_id);
CREATE INDEX idx_claims_passenger ON compensation_claims(passenger_id);
CREATE INDEX idx_claims_status ON compensation_claims(approval_status);
CREATE INDEX idx_claims_created ON compensation_claims(created_at DESC);

-- ============================================================================
-- CUSTOMER SERVICE
-- ============================================================================

-- Customer Service Interactions table
CREATE TABLE IF NOT EXISTS customer_service_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,
    passenger_id UUID REFERENCES passengers(id) ON DELETE SET NULL,
    bag_tag VARCHAR(10),
    channel VARCHAR(20) NOT NULL,
    language VARCHAR(5) DEFAULT 'en',
    query TEXT NOT NULL,
    response TEXT,
    intent VARCHAR(50),
    sentiment VARCHAR(20),
    escalated BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs_conversation ON customer_service_interactions(conversation_id);
CREATE INDEX idx_cs_passenger ON customer_service_interactions(passenger_id);
CREATE INDEX idx_cs_timestamp ON customer_service_interactions(timestamp DESC);
CREATE INDEX idx_cs_intent ON customer_service_interactions(intent);
CREATE INDEX idx_cs_escalated ON customer_service_interactions(escalated);

-- ============================================================================
-- EQUIPMENT & INFRASTRUCTURE
-- ============================================================================

-- Equipment table
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id VARCHAR(50) UNIQUE NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    airport_code VARCHAR(3) NOT NULL,
    location VARCHAR(100),
    status VARCHAR(20) DEFAULT 'operational',
    health_score INTEGER DEFAULT 100,
    utilization DECIMAL(3,2) DEFAULT 0.0,
    installed_date DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_equipment_id ON equipment(equipment_id);
CREATE INDEX idx_equipment_type ON equipment(equipment_type);
CREATE INDEX idx_equipment_airport ON equipment(airport_code);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_equipment_health ON equipment(health_score);

-- Equipment Metrics table (for time-series monitoring)
CREATE TABLE IF NOT EXISTS equipment_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id VARCHAR(50) REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    throughput INTEGER,
    error_rate DECIMAL(5,4),
    utilization DECIMAL(3,2),
    temperature DECIMAL(5,2),
    vibration_level DECIMAL(5,3),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metrics_equipment ON equipment_metrics(equipment_id);
CREATE INDEX idx_metrics_timestamp ON equipment_metrics(timestamp DESC);

-- Work Orders table
CREATE TABLE IF NOT EXISTS work_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_number VARCHAR(50) UNIQUE NOT NULL,
    equipment_id VARCHAR(50) REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    maintenance_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    description TEXT,
    assigned_to VARCHAR(100),
    scheduled_for TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_work_orders_number ON work_orders(work_order_number);
CREATE INDEX idx_work_orders_equipment ON work_orders(equipment_id);
CREATE INDEX idx_work_orders_status ON work_orders(status);
CREATE INDEX idx_work_orders_priority ON work_orders(priority);

-- ============================================================================
-- PREDICTIONS & ANALYTICS
-- ============================================================================

-- Demand Forecasts table
CREATE TABLE IF NOT EXISTS demand_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airport_code VARCHAR(3) NOT NULL,
    forecast_type VARCHAR(20) NOT NULL,
    forecast_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    predicted_bags INTEGER NOT NULL,
    confidence_score DECIMAL(3,2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_forecasts_airport ON demand_forecasts(airport_code);
CREATE INDEX idx_forecasts_timestamp ON demand_forecasts(forecast_timestamp);
CREATE INDEX idx_forecasts_type ON demand_forecasts(forecast_type);

-- Agent Executions log table (for monitoring and debugging)
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_exec_name ON agent_executions(agent_name);
CREATE INDEX idx_agent_exec_created ON agent_executions(created_at DESC);
CREATE INDEX idx_agent_exec_status ON agent_executions(status);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_passengers_updated_at BEFORE UPDATE ON passengers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flights_updated_at BEFORE UPDATE ON flights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bags_updated_at BEFORE UPDATE ON bags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_incidents_updated_at BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON compensation_claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_work_orders_updated_at BEFORE UPDATE ON work_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- Success message
SELECT 'Database schema created successfully! ✅' as status;
SELECT 'Total tables created: ' || COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
