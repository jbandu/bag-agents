"""
Generate realistic Copa Airlines flight schedule for December 15, 2025 demo.

Creates 60 flights across 3 operational waves:
- Morning Wave (06:00-09:00): 15 flights
- Midday Wave (11:00-14:00): 20 flights
- Afternoon Peak (14:00-18:00): 25 flights (main demo period)
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# Copa's primary routes
COPA_ROUTES = {
    # North America
    "USA_EAST": [("PTY", "JFK", 6.5), ("PTY", "EWR", 6.5), ("PTY", "IAD", 5.5),
                 ("PTY", "MCO", 4.5), ("PTY", "FLL", 4.0)],
    "USA_WEST": [("PTY", "LAX", 8.5), ("PTY", "SFO", 8.0), ("PTY", "LAS", 7.5)],
    "USA_CENTRAL": [("PTY", "ORD", 6.0), ("PTY", "DFW", 5.5), ("PTY", "IAH", 4.5)],
    "MIA": [("PTY", "MIA", 3.5), ("MIA", "PTY", 3.5)],

    # South America
    "BRAZIL": [("PTY", "GRU", 8.0), ("PTY", "GIG", 7.5), ("PTY", "BSB", 7.0)],
    "ARGENTINA": [("PTY", "EZE", 9.5), ("PTY", "COR", 9.0)],
    "COLOMBIA": [("PTY", "BOG", 2.0), ("BOG", "PTY", 2.0), ("PTY", "CTG", 1.5),
                 ("PTY", "MDE", 2.0)],
    "PERU": [("PTY", "LIM", 3.5), ("LIM", "PTY", 3.5)],
    "VENEZUELA": [("PTY", "CCS", 2.5)],
    "CHILE": [("PTY", "SCL", 8.5)],

    # Central America & Caribbean
    "CENTRAL": [("PTY", "GUA", 2.0), ("PTY", "SAL", 1.5), ("PTY", "SJO", 1.0),
                ("PTY", "MGA", 1.5), ("PTY", "TGU", 2.0)],
    "CARIBBEAN": [("PTY", "CUR", 2.0), ("PTY", "SXM", 3.0), ("PTY", "SDQ", 3.5)],

    # Mexico
    "MEXICO": [("PTY", "MEX", 4.5), ("MEX", "PTY", 4.5), ("PTY", "CUN", 3.0)]
}

# Aircraft types in Copa fleet
AIRCRAFT_TYPES = {
    "737-800": {"capacity": 160, "range": "medium", "frequency": 0.50},
    "737-MAX9": {"capacity": 180, "range": "long", "frequency": 0.30},
    "737-700": {"capacity": 140, "range": "short", "frequency": 0.15},
    "E190": {"capacity": 100, "range": "short", "frequency": 0.05}
}

# Common Latin American/North American passenger names
PASSENGER_NAMES = [
    "María García", "Juan Rodríguez", "Carlos Martínez", "Ana López",
    "José Hernández", "Sofía González", "Miguel Pérez", "Isabella Sánchez",
    "Luis Ramírez", "Camila Torres", "José Rivera", "Valentina Flores",
    "Fernando Gómez", "Lucía Díaz", "Antonio Cruz", "Elena Morales",
    "Roberto Silva", "Carmen Jiménez", "Diego Vargas", "Patricia Reyes",
    "Jorge Castro", "Laura Ruiz", "Ricardo Mendoza", "Angela Romero",
    "Eduardo Ortiz", "Monica Herrera", "Francisco Rojas", "Teresa Vega",
    "Alejandro Medina", "Rosa Aguilar", "Daniel Navarro", "Sandra Gutierrez",
    "Michael Johnson", "Jennifer Smith", "David Williams", "Sarah Brown",
    "Robert Jones", "Jessica Davis", "William Miller", "Amanda Wilson",
    "James Moore", "Emily Taylor", "Christopher Anderson", "Michelle Thomas"
]

def generate_flight_number() -> str:
    """Generate Copa flight number (CM### format)"""
    return f"CM{random.randint(100, 999)}"

def select_aircraft() -> str:
    """Select aircraft type based on fleet distribution"""
    r = random.random()
    cumulative = 0
    for aircraft, specs in AIRCRAFT_TYPES.items():
        cumulative += specs["frequency"]
        if r <= cumulative:
            return aircraft
    return "737-800"  # Default

def calculate_load_factor() -> float:
    """Generate realistic load factor (higher for peak times)"""
    # Copa typically runs 80-85% load factor
    return random.uniform(0.75, 0.92)

def generate_flights_for_wave(
    wave_name: str,
    start_hour: int,
    end_hour: int,
    num_flights: int,
    base_date: datetime
) -> List[Dict[str, Any]]:
    """Generate flights for a specific operational wave"""

    flights = []

    # Select routes for this wave
    all_routes = []
    for category, routes in COPA_ROUTES.items():
        all_routes.extend(routes)

    for i in range(num_flights):
        # Select random route
        origin, destination, duration = random.choice(all_routes)

        # Generate departure time within wave window
        hour = random.randint(start_hour, end_hour - 1)
        minute = random.choice([0, 15, 30, 45])  # Copa typically departs on quarters

        scheduled_departure = base_date.replace(hour=hour, minute=minute, second=0)
        scheduled_arrival = scheduled_departure + timedelta(hours=duration)

        # Select aircraft
        aircraft = select_aircraft()
        capacity = AIRCRAFT_TYPES[aircraft]["capacity"]

        # Calculate passengers and bags
        load_factor = calculate_load_factor()
        pax_count = int(capacity * load_factor)

        # Bags: avg 1.1 bags per passenger
        expected_bags = int(pax_count * random.uniform(1.0, 1.2))

        # Connection bags: higher percentage for hub (PTY origin/destination)
        if origin == "PTY":
            connection_bags = int(expected_bags * random.uniform(0.60, 0.75))  # Departures have connections
        elif destination == "PTY":
            connection_bags = int(expected_bags * random.uniform(0.50, 0.70))  # Arrivals bringing connections
        else:
            connection_bags = 0

        # Status: most on-time, some slight delays
        status_options = ["on-time"] * 85 + ["delayed"] * 10 + ["boarding"] * 5
        status = random.choice(status_options)

        # Gate assignment (Copa uses gates A1-A30 primarily in Terminal 1)
        gate = f"A{random.randint(1, 30)}"

        # Flight number
        flight_number = generate_flight_number()

        flight = {
            "flight_number": flight_number,
            "aircraft_type": aircraft,
            "aircraft_registration": f"HP-{random.randint(1000, 9999)}CMP",  # Copa uses HP- registration
            "origin": origin,
            "destination": destination,
            "scheduled_departure": scheduled_departure.isoformat(),
            "scheduled_arrival": scheduled_arrival.isoformat(),
            "actual_departure": None if status == "on-time" else (scheduled_departure + timedelta(minutes=random.randint(5, 30))).isoformat(),
            "actual_arrival": None,
            "gate": gate,
            "terminal": "1",  # Copa operates from Terminal 1 at PTY
            "status": status,
            "pax_count": pax_count,
            "pax_capacity": capacity,
            "expected_bags": expected_bags,
            "connection_bags": connection_bags,
            "local_bags": expected_bags - connection_bags,
            "wave": wave_name,
            "is_hub_operation": origin == "PTY" or destination == "PTY"
        }

        flights.append(flight)

    # Sort by departure time
    flights.sort(key=lambda f: f["scheduled_departure"])

    return flights

def generate_demo_flights() -> Dict[str, Any]:
    """Generate complete flight schedule for December 15, 2025"""

    # Base date: December 15, 2025 (Panama time: UTC-5)
    base_date = datetime(2025, 12, 15, 0, 0, 0)

    # Generate each wave
    morning_flights = generate_flights_for_wave("morning", 6, 9, 15, base_date)
    midday_flights = generate_flights_for_wave("midday", 11, 14, 20, base_date)
    afternoon_flights = generate_flights_for_wave("afternoon_peak", 14, 18, 25, base_date)

    all_flights = morning_flights + midday_flights + afternoon_flights

    # Calculate statistics
    total_pax = sum(f["pax_count"] for f in all_flights)
    total_bags = sum(f["expected_bags"] for f in all_flights)
    total_connections = sum(f["connection_bags"] for f in all_flights)

    # Return structured data
    return {
        "demo_info": {
            "date": "2025-12-15",
            "timezone": "America/Panama (UTC-5)",
            "airline": "Copa Airlines",
            "hub": "PTY - Tocumen International Airport",
            "total_flights": len(all_flights),
            "total_passengers": total_pax,
            "total_bags": total_bags,
            "total_connection_bags": total_connections,
            "connection_rate": round(total_connections / total_bags * 100, 1) if total_bags > 0 else 0,
            "demo_focus_period": "14:00-18:00 (Afternoon Peak Wave)"
        },
        "waves": {
            "morning": {
                "time_range": "06:00-09:00",
                "flights": len(morning_flights),
                "description": "Arrivals from overnight USA flights, departures to South America"
            },
            "midday": {
                "time_range": "11:00-14:00",
                "flights": len(midday_flights),
                "description": "Arrivals from South America, departures to USA/Caribbean"
            },
            "afternoon_peak": {
                "time_range": "14:00-18:00",
                "flights": len(afternoon_flights),
                "description": "Main demo period - hub operations peak with heavy connection traffic"
            }
        },
        "flights": all_flights
    }

if __name__ == "__main__":
    print("Generating Copa Airlines Demo Flight Schedule...")
    print("Date: December 15, 2025")
    print("=" * 60)

    flight_data = generate_demo_flights()

    # Save to JSON
    output_file = "demo/copa/data/Copa_flights_demo.json"
    with open(output_file, 'w') as f:
        json.dump(flight_data, f, indent=2)

    print(f"\n✅ Generated {flight_data['demo_info']['total_flights']} flights")
    print(f"   Total passengers: {flight_data['demo_info']['total_passengers']:,}")
    print(f"   Total bags: {flight_data['demo_info']['total_bags']:,}")
    print(f"   Connection bags: {flight_data['demo_info']['total_connection_bags']:,} ({flight_data['demo_info']['connection_rate']}%)")
    print(f"\n📁 Saved to: {output_file}")

    # Print wave summary
    print("\n📊 Wave Distribution:")
    for wave_name, wave_info in flight_data['waves'].items():
        print(f"   {wave_name.title()}: {wave_info['flights']} flights ({wave_info['time_range']})")
