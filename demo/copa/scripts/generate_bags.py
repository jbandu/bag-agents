"""
Generate 2,000 realistic baggage records for Copa Airlines demo.

Distribution:
- 60% local bags (PTY origin or destination)
- 40% connection bags (arriving PTY, connecting to another flight)

Connection Types:
- 80% normal connections (MCT + 30 min or more)
- 15% tight connections (MCT + 10-29 min) → for Prediction Agent demo
- 5% very tight (<MCT, will miss) → for mishandling demo

MCT (Minimum Connection Time) at PTY: 45 minutes
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Load flights
with open("demo/copa/data/Copa_flights_demo.json") as f:
    FLIGHT_DATA = json.load(f)
    FLIGHTS = FLIGHT_DATA["flights"]

# Passenger names (Latin American + North American mix)
FIRST_NAMES = {
    "latin_male": ["José", "Juan", "Carlos", "Miguel", "Luis", "Jorge", "Diego", "Fernando", "Ricardo", "Roberto"],
    "latin_female": ["María", "Ana", "Carmen", "Sofía", "Lucía", "Isabella", "Camila", "Valentina", "Elena", "Patricia"],
    "us_male": ["Michael", "David", "James", "Robert", "William", "John", "Richard", "Thomas", "Daniel", "Christopher"],
    "us_female": ["Jennifer", "Jessica", "Sarah", "Michelle", "Amanda", "Emily", "Ashley", "Lisa", "Karen", "Linda"]
}

LAST_NAMES = {
    "latin": ["García", "Rodríguez", "Martínez", "López", "Hernández", "González", "Pérez", "Sánchez", "Ramírez",
              "Torres", "Rivera", "Flores", "Gómez", "Díaz", "Cruz", "Morales", "Reyes", "Jiménez", "Vargas",
              "Castro", "Romero", "Ortiz", "Silva", "Rojas", "Medina", "Ruiz", "Vega", "Mendoza", "Navarro"],
    "us": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Moore", "Taylor",
           "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]
}

# Email domains
EMAIL_DOMAINS = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "email.com", "copa.com"]

# Phone country codes (based on region)
COUNTRY_CODES = {
    "panama": "+507",
    "usa": "+1",
    "colombia": "+57",
    "brazil": "+55",
    "peru": "+51",
    "mexico": "+52",
    "chile": "+56",
    "argentina": "+54"
}

# Copa PreferMember tiers
FF_TIERS = ["Silver", "Gold", "Platinum", "Presidential Platinum", None]
FF_TIER_WEIGHTS = [0.15, 0.10, 0.05, 0.02, 0.68]  # Most passengers not in program

MCT_MINUTES = 45  # Minimum Connection Time at PTY

def generate_name(region: str = "latin") -> Tuple[str, str]:
    """Generate realistic passenger name"""
    gender = random.choice(["male", "female"])

    if region == "latin":
        first = random.choice(FIRST_NAMES[f"latin_{gender}"])
        last1 = random.choice(LAST_NAMES["latin"])
        last2 = random.choice(LAST_NAMES["latin"])
        return first, f"{last1} {last2}"  # Latin American naming convention
    else:
        first = random.choice(FIRST_NAMES[f"us_{gender}"])
        last = random.choice(LAST_NAMES["us"])
        return first, last

def generate_email(first: str, last: str) -> str:
    """Generate realistic email address"""
    # Clean names for email
    first_clean = first.lower().replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    last_clean = last.lower().replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    # Various email formats
    formats = [
        f"{first_clean}.{last_clean}",
        f"{first_clean}{last_clean}",
        f"{first_clean[0]}{last_clean}",
        f"{first_clean}_{last_clean}",
        f"{first_clean}.{last_clean}{random.randint(1, 99)}"
    ]

    email_format = random.choice(formats)
    domain = random.choice(EMAIL_DOMAINS)

    return f"{email_format}@{domain}"

def generate_phone(country: str = "panama") -> str:
    """Generate realistic phone number"""
    code = COUNTRY_CODES.get(country, "+507")

    if country == "usa":
        area = random.randint(200, 999)
        prefix = random.randint(200, 999)
        line = random.randint(1000, 9999)
        return f"{code}-{area}-{prefix}-{line}"
    else:
        # International format
        number = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        return f"{code}-{number}"

def generate_booking_ref() -> str:
    """Generate 6-character PNR"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(random.choice(chars) for _ in range(6))

def generate_ff_number(tier: str = None) -> str:
    """Generate PreferMember frequent flyer number"""
    if tier is None:
        return None
    return f"CM{random.randint(100000000, 999999999)}"

def generate_bag_id(index: int) -> str:
    """Generate unique bag tag number (Copa uses IATA code 230)"""
    return f"0230{index:06d}"

def find_connection_flights(arrival_flight: Dict, min_gap: int = MCT_MINUTES) -> List[Tuple[Dict, int]]:
    """
    Find possible connecting flights for an arriving flight.

    Returns list of (flight, connection_time_minutes) tuples
    """
    arrival_time = datetime.fromisoformat(arrival_flight["scheduled_arrival"])
    connections = []

    for outbound in FLIGHTS:
        # Must be departing from PTY
        if outbound["origin"] != "PTY":
            continue

        # Must not be the same flight
        if outbound["flight_number"] == arrival_flight["flight_number"]:
            continue

        departure_time = datetime.fromisoformat(outbound["scheduled_departure"])

        # Calculate connection time
        connection_time = (departure_time - arrival_time).total_seconds() / 60

        # Must have some connection time (even if tight)
        if connection_time >= min_gap - 15:  # Allow some very tight connections
            connections.append((outbound, int(connection_time)))

    return connections

def categorize_connection(connection_time: int) -> str:
    """Categorize connection as normal, tight, or very tight"""
    if connection_time >= MCT_MINUTES + 30:
        return "normal"  # Comfortable
    elif connection_time >= MCT_MINUTES:
        return "tight"  # Risky
    else:
        return "very_tight"  # Will likely miss

def generate_local_bag(bag_id: str, flight: Dict, region: str = "latin") -> Dict[str, Any]:
    """Generate local bag (no connection)"""
    first, last = generate_name(region)

    # Country based on origin/destination
    if flight["origin"] == "PTY":
        country = "panama"
    elif flight["destination"] in ["JFK", "EWR", "MIA", "LAX", "ORD"]:
        country = "usa"
    else:
        country = "panama"

    # FF tier
    tier = random.choices(FF_TIERS, FF_TIER_WEIGHTS)[0]

    bag = {
        "bag_id": bag_id,
        "tag_number": bag_id,
        "passenger": {
            "name": f"{first} {last}",
            "booking_ref": generate_booking_ref(),
            "contact": generate_phone(country),
            "email": generate_email(first, last),
            "frequent_flyer": generate_ff_number(tier),
            "tier": tier
        },
        "journey": {
            "type": "local",
            "origin": flight["origin"],
            "destination": flight["destination"],
            "outbound_flight": flight["flight_number"],
            "outbound_departure": flight["scheduled_departure"],
            "inbound_flight": None,
            "inbound_arrival": None,
            "final_destination": flight["destination"],
            "connection_time_min": None,
            "mct_min": MCT_MINUTES
        },
        "characteristics": {
            "weight_kg": round(random.uniform(15, 32), 1),
            "type": random.choice(["standard"] * 95 + ["oversized"] * 3 + ["fragile"] * 2),
            "special_handling": random.choice([None] * 97 + ["priority"] * 2 + ["fragile"] * 1),
            "declared_value_usd": random.choice([0] * 90 + [500, 1000, 2000, 5000] * 2 + [10000])
        },
        "risk_factors": {
            "tight_connection": False,
            "first_bag": random.choice([True, False]),
            "vip_passenger": tier in ["Platinum", "Presidential Platinum"],
            "high_value": False,
            "international": flight["origin"] != "PTY" and flight["destination"] != "PTY"
        },
        "current_status": "checked_in",
        "current_location": flight["origin"]
    }

    # High value flag
    bag["risk_factors"]["high_value"] = bag["characteristics"]["declared_value_usd"] > 2000

    return bag

def generate_connection_bag(
    bag_id: str,
    inbound: Dict,
    outbound: Dict,
    connection_time: int,
    region: str = "latin"
) -> Dict[str, Any]:
    """Generate connection bag"""
    first, last = generate_name(region)

    # Determine country from inbound origin
    if inbound["origin"] in ["JFK", "EWR", "MIA", "LAX", "ORD", "IAH", "DFW"]:
        country = "usa"
    elif inbound["origin"] in ["BOG", "MDE", "CTG"]:
        country = "colombia"
    elif inbound["origin"] in ["GRU", "GIG", "BSB"]:
        country = "brazil"
    else:
        country = "panama"

    # FF tier (connection passengers more likely to be frequent flyers)
    tier_weights = [0.20, 0.15, 0.08, 0.03, 0.54]  # Higher than local
    tier = random.choices(FF_TIERS, tier_weights)[0]

    # Connection category
    conn_category = categorize_connection(connection_time)

    # Determine current status
    current_status = "in_transit" if inbound["status"] in ["departed", "boarding"] else "checked_in"
    current_location = inbound["origin"] if current_status == "checked_in" else "in_flight"

    bag = {
        "bag_id": bag_id,
        "tag_number": bag_id,
        "passenger": {
            "name": f"{first} {last}",
            "booking_ref": generate_booking_ref(),
            "contact": generate_phone(country),
            "email": generate_email(first, last),
            "frequent_flyer": generate_ff_number(tier),
            "tier": tier
        },
        "journey": {
            "type": "connection",
            "origin": inbound["origin"],
            "destination": outbound["destination"],
            "inbound_flight": inbound["flight_number"],
            "inbound_arrival": inbound["scheduled_arrival"],
            "outbound_flight": outbound["flight_number"],
            "outbound_departure": outbound["scheduled_departure"],
            "connection_airport": "PTY",
            "final_destination": outbound["destination"],
            "connection_time_min": connection_time,
            "connection_category": conn_category,
            "mct_min": MCT_MINUTES
        },
        "characteristics": {
            "weight_kg": round(random.uniform(15, 32), 1),
            "type": random.choice(["standard"] * 95 + ["oversized"] * 3 + ["fragile"] * 2),
            "special_handling": random.choice([None] * 95 + ["priority"] * 3 + ["fragile"] * 2),
            "declared_value_usd": random.choice([0] * 88 + [500, 1000, 2000, 5000] * 2 + [10000, 15000])
        },
        "risk_factors": {
            "tight_connection": conn_category in ["tight", "very_tight"],
            "first_bag": random.choice([True, False]),
            "vip_passenger": tier in ["Platinum", "Presidential Platinum"],
            "high_value": False,
            "international": True  # All connections are international
        },
        "current_status": current_status,
        "current_location": current_location
    }

    # High value flag
    bag["risk_factors"]["high_value"] = bag["characteristics"]["declared_value_usd"] > 2000

    return bag

def generate_demo_bags(total_bags: int = 2000) -> Dict[str, Any]:
    """Generate complete bag dataset for demo"""

    print(f"Generating {total_bags:,} bags...")

    # Target distribution
    target_local = int(total_bags * 0.40)  # 40% local
    target_connections = total_bags - target_local  # 60% connections

    # Connection type distribution
    target_normal_conn = int(target_connections * 0.80)  # 80% normal
    target_tight_conn = int(target_connections * 0.15)   # 15% tight
    target_very_tight_conn = target_connections - target_normal_conn - target_tight_conn  # 5% very tight

    bags = []
    bag_counter = 1

    # Generate local bags
    print(f"  Generating {target_local:,} local bags...")
    for i in range(target_local):
        # Pick random flight
        flight = random.choice(FLIGHTS)

        # Determine region from flight
        if flight["origin"] in ["JFK", "MIA", "LAX", "ORD"] or flight["destination"] in ["JFK", "MIA", "LAX", "ORD"]:
            region = "us" if random.random() < 0.6 else "latin"
        else:
            region = "latin"

        bag_id = generate_bag_id(bag_counter)
        bag = generate_local_bag(bag_id, flight, region)
        bags.append(bag)
        bag_counter += 1

    # Generate connection bags
    print(f"  Generating {target_connections:,} connection bags...")

    # Find all arriving flights (potential inbound legs)
    arriving_flights = [f for f in FLIGHTS if f["destination"] == "PTY"]

    # Pre-compute all possible connections
    all_possible_connections = []
    for inbound in arriving_flights:
        connections = find_connection_flights(inbound)
        for outbound, conn_time in connections:
            conn_category = categorize_connection(conn_time)
            all_possible_connections.append((inbound, outbound, conn_time, conn_category))

    # Categorize connections
    normal_connections = [(i, o, t, c) for i, o, t, c in all_possible_connections if c == "normal"]
    tight_connections = [(i, o, t, c) for i, o, t, c in all_possible_connections if c == "tight"]
    very_tight_connections = [(i, o, t, c) for i, o, t, c in all_possible_connections if c == "very_tight"]

    # Generate bags for each category
    for i in range(target_normal_conn):
        if bag_counter > total_bags or not normal_connections:
            break

        inbound, outbound, conn_time, _ = random.choice(normal_connections)

        # Determine region
        if inbound["origin"] in ["JFK", "MIA", "LAX", "ORD", "EWR", "IAH"]:
            region = "us" if random.random() < 0.7 else "latin"
        else:
            region = "latin"

        bag_id = generate_bag_id(bag_counter)
        bag = generate_connection_bag(bag_id, inbound, outbound, conn_time, region)
        bags.append(bag)
        bag_counter += 1

    for i in range(target_tight_conn):
        if bag_counter > total_bags or not tight_connections:
            # If not enough tight connections, use normal ones
            if normal_connections:
                inbound, outbound, conn_time, _ = random.choice(normal_connections)
            else:
                break
        else:
            inbound, outbound, conn_time, _ = random.choice(tight_connections)

        # Determine region
        if inbound["origin"] in ["JFK", "MIA", "LAX", "ORD", "EWR", "IAH"]:
            region = "us" if random.random() < 0.7 else "latin"
        else:
            region = "latin"

        bag_id = generate_bag_id(bag_counter)
        bag = generate_connection_bag(bag_id, inbound, outbound, conn_time, region)
        bags.append(bag)
        bag_counter += 1

    for i in range(target_very_tight_conn):
        if bag_counter > total_bags or not very_tight_connections:
            # If not enough very tight, use tight or normal
            if tight_connections:
                inbound, outbound, conn_time, _ = random.choice(tight_connections)
            elif normal_connections:
                inbound, outbound, conn_time, _ = random.choice(normal_connections)
            else:
                break
        else:
            inbound, outbound, conn_time, _ = random.choice(very_tight_connections)

        # Determine region
        if inbound["origin"] in ["JFK", "MIA", "LAX", "ORD", "EWR", "IAH"]:
            region = "us" if random.random() < 0.7 else "latin"
        else:
            region = "latin"

        bag_id = generate_bag_id(bag_counter)
        bag = generate_connection_bag(bag_id, inbound, outbound, conn_time, region)
        bags.append(bag)
        bag_counter += 1

    # Calculate statistics
    connection_bags = [b for b in bags if b["journey"]["type"] == "connection"]
    normal_conn_bags = [b for b in connection_bags if b["journey"]["connection_category"] == "normal"]
    tight_conn_bags = [b for b in connection_bags if b["journey"]["connection_category"] == "tight"]
    very_tight_conn_bags = [b for b in connection_bags if b["journey"]["connection_category"] == "very_tight"]

    vip_bags = [b for b in bags if b["risk_factors"]["vip_passenger"]]
    high_value_bags = [b for b in bags if b["risk_factors"]["high_value"]]
    tight_connection_bags = [b for b in bags if b["risk_factors"]["tight_connection"]]

    return {
        "demo_info": {
            "date": "2025-12-15",
            "total_bags": len(bags),
            "local_bags": len([b for b in bags if b["journey"]["type"] == "local"]),
            "connection_bags": len(connection_bags),
            "connection_rate": round(len(connection_bags) / len(bags) * 100, 1) if bags else 0,
            "connection_distribution": {
                "normal": len(normal_conn_bags),
                "tight": len(tight_conn_bags),
                "very_tight": len(very_tight_conn_bags)
            },
            "risk_profile": {
                "vip_passengers": len(vip_bags),
                "high_value_bags": len(high_value_bags),
                "tight_connections": len(tight_connection_bags),
                "risk_score_high": len([b for b in tight_connection_bags if b["journey"].get("connection_category") == "very_tight"])
            }
        },
        "bags": bags
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Copa Airlines Demo - Baggage Data Generation")
    print("=" * 60)

    bag_data = generate_demo_bags(2000)

    # Save to JSON
    output_file = "demo/copa/data/Copa_bags_demo.json"
    with open(output_file, 'w') as f:
        json.dump(bag_data, f, indent=2)

    print(f"\n✅ Generated {bag_data['demo_info']['total_bags']:,} bags")
    print(f"\n📊 Distribution:")
    print(f"   Local bags: {bag_data['demo_info']['local_bags']:,} ({100 - bag_data['demo_info']['connection_rate']:.1f}%)")
    print(f"   Connection bags: {bag_data['demo_info']['connection_bags']:,} ({bag_data['demo_info']['connection_rate']:.1f}%)")

    print(f"\n🔗 Connection Types:")
    for conn_type, count in bag_data['demo_info']['connection_distribution'].items():
        pct = count / bag_data['demo_info']['connection_bags'] * 100 if bag_data['demo_info']['connection_bags'] > 0 else 0
        print(f"   {conn_type.title()}: {count:,} ({pct:.1f}%)")

    print(f"\n⚠️  Risk Profile:")
    for risk_type, count in bag_data['demo_info']['risk_profile'].items():
        print(f"   {risk_type.replace('_', ' ').title()}: {count:,}")

    print(f"\n📁 Saved to: {output_file}")
