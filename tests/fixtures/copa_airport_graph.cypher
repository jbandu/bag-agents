// Copa Airlines Airport Infrastructure Graph
// Neo4j Cypher script to create test airport infrastructure

// Clear existing test data
MATCH (n:Airport {test: true}) DETACH DELETE n;
MATCH (n:Equipment {test: true}) DETACH DELETE n;
MATCH (n:Gate {test: true}) DETACH DELETE n;
MATCH (n:Conveyor {test: true}) DETACH DELETE n;

// Create PTY (Panama Hub) infrastructure
CREATE (pty:Airport {
  code: 'PTY',
  name: 'Tocumen International Airport',
  city: 'Panama City',
  country: 'Panama',
  timezone: 'America/Panama',
  is_hub: true,
  test: true
})

// Create terminal areas
CREATE (t1:Terminal {
  id: 'PTY-T1',
  name: 'Terminal 1',
  airport: 'PTY',
  test: true
})

CREATE (t2:Terminal {
  id: 'PTY-T2',
  name: 'Terminal 2',
  airport: 'PTY',
  test: true
})

// Create gates
CREATE (g1:Gate {id: 'PTY-A1', terminal: 'T1', status: 'operational', test: true})
CREATE (g2:Gate {id: 'PTY-A2', terminal: 'T1', status: 'operational', test: true})
CREATE (g3:Gate {id: 'PTY-A3', terminal: 'T1', status: 'operational', test: true})
CREATE (g4:Gate {id: 'PTY-B1', terminal: 'T2', status: 'operational', test: true})
CREATE (g5:Gate {id: 'PTY-B2', terminal: 'T2', status: 'operational', test: true})

// Create baggage handling equipment
CREATE (conv1:Conveyor {
  id: 'CONV-1',
  name: 'Main Inbound Conveyor',
  airport: 'PTY',
  capacity_bags_per_hour: 600,
  status: 'operational',
  health_score: 95,
  test: true
})

CREATE (conv2:Conveyor {
  id: 'CONV-2',
  name: 'Transfer Conveyor A',
  airport: 'PTY',
  capacity_bags_per_hour: 450,
  status: 'operational',
  health_score: 88,
  test: true
})

CREATE (conv5:Conveyor {
  id: 'CONV-5',
  name: 'Transfer Conveyor D',
  airport: 'PTY',
  capacity_bags_per_hour: 400,
  status: 'operational',
  health_score: 75,
  test: true
})

CREATE (conv6:Conveyor {
  id: 'CONV-6',
  name: 'Backup Transfer Conveyor',
  airport: 'PTY',
  capacity_bags_per_hour: 350,
  status: 'operational',
  health_score: 92,
  test: true
})

CREATE (screen1:Scanner {
  id: 'SCAN-1',
  name: 'Security Scanner 1',
  airport: 'PTY',
  type: 'xray',
  status: 'operational',
  throughput_per_hour: 300,
  test: true
})

CREATE (sort1:Sorter {
  id: 'SORT-1',
  name: 'Main Sorting System',
  airport: 'PTY',
  capacity_bags_per_hour: 1200,
  status: 'operational',
  health_score: 90,
  test: true
})

// Create storage areas
CREATE (hold1:HoldingArea {
  id: 'HOLD-1',
  name: 'International Transfer Hold',
  airport: 'PTY',
  capacity_bags: 500,
  current_load: 120,
  test: true
})

CREATE (claim1:ClaimArea {
  id: 'CLAIM-1',
  carousel: '1',
  airport: 'PTY',
  status: 'operational',
  test: true
})

// Create other airports
CREATE (jfk:Airport {
  code: 'JFK',
  name: 'John F Kennedy International',
  city: 'New York',
  country: 'USA',
  timezone: 'America/New_York',
  is_hub: false,
  test: true
})

CREATE (mia:Airport {
  code: 'MIA',
  name: 'Miami International Airport',
  city: 'Miami',
  country: 'USA',
  timezone: 'America/New_York',
  is_hub: false,
  test: true
})

CREATE (bog:Airport {
  code: 'BOG',
  name: 'El Dorado International Airport',
  city: 'Bogota',
  country: 'Colombia',
  timezone: 'America/Bogota',
  is_hub: false,
  test: true
})

CREATE (lim:Airport {
  code: 'LIM',
  name: 'Jorge Chavez International Airport',
  city: 'Lima',
  country: 'Peru',
  timezone: 'America/Lima',
  is_hub: false,
  test: true
})

// Create routes
CREATE (pty)-[:ROUTE {
  flight_time_hours: 6.5,
  distance_km: 4180,
  frequency_daily: 2,
  test: true
}]->(jfk)

CREATE (pty)-[:ROUTE {
  flight_time_hours: 3.5,
  distance_km: 2250,
  frequency_daily: 4,
  test: true
}]->(mia)

CREATE (bog)-[:ROUTE {
  flight_time_hours: 2.0,
  distance_km: 1200,
  frequency_daily: 8,
  test: true
}]->(pty)

CREATE (pty)-[:ROUTE {
  flight_time_hours: 3.5,
  distance_km: 2100,
  frequency_daily: 3,
  test: true
}]->(lim)

// Create baggage flow paths at PTY
CREATE (t1)-[:CONNECTS_TO {
  transport_time_minutes: 5,
  method: 'conveyor',
  equipment_id: 'CONV-1',
  test: true
}]->(sort1)

CREATE (sort1)-[:CONNECTS_TO {
  transport_time_minutes: 8,
  method: 'conveyor',
  equipment_id: 'CONV-2',
  test: true
}]->(g1)

CREATE (sort1)-[:CONNECTS_TO {
  transport_time_minutes: 12,
  method: 'conveyor',
  equipment_id: 'CONV-5',
  test: true
}]->(g2)

CREATE (sort1)-[:CONNECTS_TO {
  transport_time_minutes: 10,
  method: 'conveyor',
  equipment_id: 'CONV-6',
  test: true
}]->(g3)

CREATE (sort1)-[:CONNECTS_TO {
  transport_time_minutes: 6,
  method: 'conveyor',
  test: true
}]->(hold1)

CREATE (hold1)-[:CONNECTS_TO {
  transport_time_minutes: 15,
  method: 'cart',
  test: true
}]->(g1)

// Return summary
RETURN 'Copa test infrastructure created successfully' AS message,
       count(DISTINCT pty) AS airports_created,
       5 AS gates_created,
       4 AS conveyors_created,
       1 AS sorters_created;
