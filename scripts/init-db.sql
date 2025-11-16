-- Database initialization script for baggage operations
-- This script creates the necessary tables and initial data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Airports table
CREATE TABLE IF NOT EXISTS airports (
    id SERIAL PRIMARY KEY,
    iata_code VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    timezone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flights table
CREATE TABLE IF NOT EXISTS flights (
    id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    departure_airport VARCHAR(3) REFERENCES airports(iata_code),
    arrival_airport VARCHAR(3) REFERENCES airports(iata_code),
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,
    actual_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Baggage table
CREATE TABLE IF NOT EXISTS baggage (
    id SERIAL PRIMARY KEY,
    tag_number VARCHAR(20) UNIQUE NOT NULL,
    flight_id INTEGER REFERENCES flights(id),
    passenger_id VARCHAR(50),
    weight_kg DECIMAL(5,2),
    status VARCHAR(20),
    current_location VARCHAR(100),
    destination VARCHAR(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) UNIQUE NOT NULL,
    incident_type VARCHAR(50) NOT NULL,
    flight_id INTEGER REFERENCES flights(id),
    baggage_id INTEGER REFERENCES baggage(id),
    description TEXT,
    severity VARCHAR(20),
    status VARCHAR(20),
    resolution TEXT,
    occurred_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compensation claims table
CREATE TABLE IF NOT EXISTS compensation_claims (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(50) UNIQUE NOT NULL,
    incident_id INTEGER REFERENCES incidents(id),
    customer_id VARCHAR(50) NOT NULL,
    claim_type VARCHAR(50),
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20),
    approved_by VARCHAR(100),
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Equipment table
CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(50) UNIQUE NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    airport_code VARCHAR(3) REFERENCES airports(iata_code),
    status VARCHAR(20),
    health_score INTEGER,
    last_maintenance TIMESTAMP,
    next_maintenance TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Equipment metrics table
CREATE TABLE IF NOT EXISTS equipment_metrics (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(id),
    metric_name VARCHAR(50),
    metric_value DECIMAL(10,2),
    unit VARCHAR(20),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(50) UNIQUE NOT NULL,
    flight_id INTEGER REFERENCES flights(id),
    risk_score INTEGER,
    risk_level VARCHAR(20),
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accuracy_score DECIMAL(3,2),
    model_version VARCHAR(20)
);

-- Agent execution logs table
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    execution_id UUID DEFAULT uuid_generate_v4(),
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(20),
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_flights_departure ON flights(departure_airport, scheduled_departure);
CREATE INDEX IF NOT EXISTS idx_flights_arrival ON flights(arrival_airport, scheduled_arrival);
CREATE INDEX IF NOT EXISTS idx_baggage_tag ON baggage(tag_number);
CREATE INDEX IF NOT EXISTS idx_baggage_status ON baggage(status);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_claims_status ON compensation_claims(status);
CREATE INDEX IF NOT EXISTS idx_equipment_airport ON equipment(airport_code);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_name, created_at);

-- Insert sample airports
INSERT INTO airports (iata_code, name, city, country, timezone)
VALUES
    ('JFK', 'John F. Kennedy International Airport', 'New York', 'USA', 'America/New_York'),
    ('LAX', 'Los Angeles International Airport', 'Los Angeles', 'USA', 'America/Los_Angeles'),
    ('ORD', 'O''Hare International Airport', 'Chicago', 'USA', 'America/Chicago'),
    ('DFW', 'Dallas/Fort Worth International Airport', 'Dallas', 'USA', 'America/Chicago'),
    ('ATL', 'Hartsfield-Jackson Atlanta International Airport', 'Atlanta', 'USA', 'America/New_York')
ON CONFLICT (iata_code) DO NOTHING;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_airports_updated_at BEFORE UPDATE ON airports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flights_updated_at BEFORE UPDATE ON flights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_baggage_updated_at BEFORE UPDATE ON baggage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_incidents_updated_at BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compensation_claims_updated_at BEFORE UPDATE ON compensation_claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
