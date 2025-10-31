#!/usr/bin/env python3
"""
Test Data Generator for OSINT System Maritime Shadow Networks Test Scenario
Generates realistic test data to validate system capabilities
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

class MaritimeTestDataGenerator:
    """Generates realistic maritime investigation test data"""
    
    def __init__(self):
        self.vessels = [
            {"name": "MT OCEAN SHADOW", "imo": "9876543", "flag": "Panama"},
            {"name": "MV GOLDEN HORIZON", "imo": "8765432", "flag": "Cook Islands"},
            {"name": "MT PACIFIC BRIDGE", "imo": "7654321", "flag": "Cameroon"},
            {"name": "MT STORM RIDER", "imo": "6543210", "flag": "Liberia"},
            {"name": "MV SILVER WAVE", "imo": "5432109", "flag": "Marshall Islands"}
        ]
        
        self.shell_companies = [
            {"name": "Oceanic Shipping Ltd", "jurisdiction": "UAE", "registration": "2021-03-15"},
            {"name": "Global Maritime Investments", "jurisdiction": "Cyprus", "registration": "2020-11-22"},
            {"name": "Pacific Transport Corp", "jurisdiction": "Belize", "registration": "2022-01-08"},
            {"name": "Eastern Shipping Services", "jurisdiction": "Panama", "registration": "2019-07-30"},
            {"name": "Black Sea Logistics", "jurisdiction": "Marshall Islands", "registration": "2021-09-12"}
        ]
        
        self.ports = [
            "Piraeus", "Istanbul", "Dubai", "Singapore", "Rotterdam",
            "Fujairah", "Gibraltar", "Malta", "Limassol", "Constanta"
        ]
        
        self.individuals = [
            {"name": "Alexei Volkov", "nationality": "Russian", "role": "Captain"},
            {"name": "Mohammed Al-Rashid", "nationality": "UAE", "role": "Owner"},
            {"name": "Elena Petrova", "nationality": "Ukrainian", "role": "Manager"},
            {"name": "Chen Wei", "nationality": "Chinese", "role": "Broker"},
            {"name": "Giuseppe Rossi", "nationality": "Italian", "role": "Technical Advisor"}
        ]

    def generate_ais_data(self, vessel_imo: str, start_date: str, end_date: str) -> List[Dict]:
        """Generate realistic AIS tracking data with manipulation patterns"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        ais_data = []
        current_date = start
        
        while current_date <= end:
            # Normal positions
            for hour in range(0, 24, 3):  # Every 3 hours
                position = self._generate_position(current_date, hour)
                
                # Insert AIS manipulation patterns
                if random.random() < 0.15:  # 15% chance of manipulation
                    position.update({
                        "signal_quality": "poor",
                        "position_accuracy": "low",
                        "speed_knots": random.uniform(25, 35),  # Unrealistic speed
                        "course": random.uniform(0, 360),
                        "manipulation_indicators": ["speed_anomaly", "position_jump"]
                    })
                
                position.update({
                    "vessel_imo": vessel_imo,
                    "timestamp": current_date.replace(hour=hour).isoformat(),
                    "source": "satellite_ais" if hour % 6 == 0 else "terrestrial_ais"
                })
                
                ais_data.append(position)
            
            # Add signal gaps (typical AIS manipulation)
            if random.random() < 0.2:  # 20% chance of signal gap
                gap_hours = random.randint(6, 24)
                current_date += timedelta(hours=gap_hours)
                continue
            
            current_date += timedelta(days=1)
        
        return ais_data

    def generate_corporate_structure(self) -> Dict:
        """Generate complex corporate ownership structure"""
        structure = {
            "ultimate_beneficial_owner": {
                "name": "International Holdings Group",
                "jurisdiction": "British Virgin Islands",
                "type": "trust",
                "established": "2018-06-15"
            },
            "holding_companies": [],
            "operating_companies": [],
            "relationships": []
        }
        
        # Generate holding company chain
        previous_company = structure["ultimate_beneficial_owner"]["name"]
        for i, company in enumerate(self.shell_companies[:3]):
            holding = {
                "name": company["name"],
                "jurisdiction": company["jurisdiction"],
                "registration_date": company["registration"],
                "type": "holding_company",
                "directors": self._generate_nominee_directors(2),
                "shareholders": [previous_company] if i == 0 else [self.shell_companies[i-1]["name"]],
                "ownership_percentage": random.uniform(51, 100)
            }
            structure["holding_companies"].append(holding)
            
            structure["relationships"].append({
                "from_entity": previous_company,
                "to_entity": company["name"],
                "relationship_type": "owns",
                "percentage": holding["ownership_percentage"],
                "date_established": company["registration"]
            })
            
            previous_company = company["name"]
        
        # Add operating companies
        for vessel in self.vessels[:3]:
            operating = {
                "name": f"{vessel['name'].split()[1]} Operations Ltd",
                "jurisdiction": random.choice(["Panama", "Liberia", "Marshall Islands"]),
                "type": "operating_company",
                "managed_vessels": [vessel["imo"]],
                "registered_owner": previous_company
            }
            structure["operating_companies"].append(operating)
            
            structure["relationships"].append({
                "from_entity": previous_company,
                "to_entity": operating["name"],
                "relationship_type": "manages",
                "vessels": [vessel["imo"]]
            })
        
        return structure

    def generate_financial_transactions(self) -> List[Dict]:
        """Generate realistic financial transaction patterns"""
        transactions = []
        
        # Layered payment structure
        payment_chains = [
            {
                "amount": 2500000,
                "currency": "USD",
                "purpose": "vessel_charter_payment",
                "chain_length": 4,
                "methods": ["wire_transfer", "crypto_exchange", "cash_withdrawal", "wire_transfer"]
            },
            {
                "amount": 1800000,
                "currency": "EUR", 
                "purpose": "bunker_fuel_payment",
                "chain_length": 3,
                "methods": ["wire_transfer", "crypto_exchange", "wire_transfer"]
            },
            {
                "amount": 950000,
                "currency": "AED",
                "purpose": "port_services_payment",
                "chain_length": 5,
                "methods": ["wire_transfer", "crypto_exchange", "prepaid_card", "crypto_exchange", "wire_transfer"]
            }
        ]
        
        for chain in payment_chains:
            current_amount = chain["amount"]
            current_entity = "Originating Company"
            
            for step in range(chain["chain_length"]):
                transaction = {
                    "transaction_id": str(uuid.uuid4()),
                    "from_entity": current_entity,
                    "to_entity": f"Intermediary {step + 1}" if step < chain["chain_length"] - 1 else "Final Recipient",
                    "amount": current_amount,
                    "currency": chain["currency"],
                    "method": chain["methods"][step],
                    "date": self._random_date_in_range("2023-01-01", "2024-12-31"),
                    "purpose": chain["purpose"],
                    "sanctions_screening": "clean" if step == 0 else "flagged",
                    "suspicious_indicators": self._generate_suspicious_indicators(step)
                }
                
                transactions.append(transaction)
                
                # Add fees and adjust amount for next step
                fee_percentage = random.uniform(0.5, 2.0)
                current_amount = current_amount * (1 - fee_percentage/100)
                current_entity = transaction["to_entity"]
        
        return transactions

    def generate_social_media_data(self) -> List[Dict]:
        """Generate social media intelligence data"""
        social_data = []
        
        platforms = ["LinkedIn", "Telegram", "Facebook", "Twitter"]
        
        for individual in self.individuals:
            for platform in platforms:
                profile = {
                    "person_name": individual["name"],
                    "platform": platform,
                    "profile_data": self._generate_social_profile(individual, platform),
                    "connections": self._generate_connections(individual["name"], platform),
                    "posts": self._generate_posts(individual, platform),
                    "suspicious_patterns": self._identify_suspicious_patterns(individual, platform)
                }
                social_data.append(profile)
        
        return social_data

    def generate_satellite_imagery_metadata(self) -> List[Dict]:
        """Generate satellite imagery analysis metadata"""
        imagery_data = []
        
        port_dates = [
            ("Piraeus", "2024-03-15"),
            ("Dubai", "2024-05-22"),
            ("Singapore", "2024-07-10"),
            ("Istanbul", "2024-09-08")
        ]
        
        for port, date in port_dates:
            for vessel in self.vessels[:3]:
                imagery = {
                    "satellite": "WorldView-3",
                    "image_date": date,
                    "location": port,
                    "vessel_detected": vessel["imo"],
                    "vessel_name": vessel["name"],
                    "confidence": random.uniform(0.85, 0.98),
                    "analysis": {
                        "vessel_length": random.uniform(180, 250),
                        "vessel_draft": random.uniform(8, 15),
                        "cargo_indicators": ["oil_stains", "loading_equipment"],
                        "activity_type": random.choice(["loading", "unloading", "anchored", "transit"]),
                        "accompanying_vessels": random.randint(0, 3)
                    },
                    "anomalies": self._detect_imagery_anomalies()
                }
                imagery_data.append(imagery)
        
        return imagery_data

    def _generate_position(self, date: datetime, hour: int) -> Dict:
        """Generate realistic vessel position"""
        # Simulate movement between Mediterranean ports
        mediterranean_coords = [
            (36.0, 29.0),  # Eastern Mediterranean
            (37.5, 27.0),  # Aegean Sea
            (41.0, 29.0),  # Sea of Marmara
            (25.5, 55.0),  # Persian Gulf
            (1.3, 104.0),  # Singapore Strait
        ]
        
        base_coord = random.choice(mediterranean_coords)
        lat = base_coord[0] + random.uniform(-2, 2)
        lon = base_coord[1] + random.uniform(-2, 2)
        
        return {
            "latitude": lat,
            "longitude": lon,
            "speed_knots": random.uniform(8, 18),
            "course": random.uniform(0, 360),
            "status": random.choice(["under_way", "anchored", "moored"]),
            "signal_quality": random.choice(["excellent", "good", "fair"])
        }

    def _generate_nominee_directors(self, count: int) -> List[Dict]:
        """Generate nominee director profiles"""
        directors = []
        names = ["John Smith", "Maria Garcia", "David Chen", "Sarah Johnson", "Ahmed Hassan"]
        
        for i in range(count):
            director = {
                "name": random.choice(names),
                "nationality": random.choice(["British", "Irish", "Maltese", "Cypriot"]),
                "appointments_count": random.randint(5, 25),
                "appointment_date": self._random_date_in_range("2020-01-01", "2023-12-31"),
                "is_nominee": True
            }
            directors.append(director)
        
        return directors

    def _generate_suspicious_indicators(self, step: int) -> List[str]:
        """Generate suspicious transaction indicators"""
        indicators = [
            ["round_amount", "high_velocity", "unusual_timing"],
            ["shell_company_involved", "jurisdiction_hopping"],
            ["crypto_mixer", "privacy_coin"],
            ["structuring", "smurfing"],
            ["trade_based_money_laundering", "over_invoicing"]
        ]
        
        return indicators[min(step, len(indicators) - 1)]

    def _generate_social_profile(self, individual: Dict, platform: str) -> Dict:
        """Generate social media profile data"""
        profile = {
            "name": individual["name"],
            "headline": f"{individual['role']} at Maritime Company",
            "location": random.choice(["Dubai", "Limassol", "Athens", "Singapore"]),
            "connections_count": random.randint(100, 5000) if platform == "LinkedIn" else random.randint(50, 500)
        }
        
        if platform == "LinkedIn":
            profile.update({
                "experience": [
                    {
                        "company": random.choice(self.shell_companies)["name"],
                        "position": individual["role"],
                        "duration": f"{random.randint(1, 5)} years"
                    }
                ],
                "skills": ["Maritime Operations", "Logistics", "International Trade"]
            })
        
        return profile

    def _generate_connections(self, person_name: str, platform: str) -> List[Dict]:
        """Generate social media connections"""
        connections = []
        connection_count = random.randint(5, 15)
        
        for _ in range(connection_count):
            other_person = random.choice([i["name"] for i in self.individuals if i["name"] != person_name])
            connection = {
                "connected_to": other_person,
                "connection_date": self._random_date_in_range("2022-01-01", "2024-12-31"),
                "mutual_connections": random.randint(1, 50),
                "connection_strength": random.choice(["strong", "moderate", "weak"])
            }
            connections.append(connection)
        
        return connections

    def _generate_posts(self, individual: Dict, platform: str) -> List[Dict]:
        """Generate social media posts with coded language"""
        posts = []
        
        coded_messages = [
            "Smooth sailing in the Mediterranean this week",
            "New routes opening up in the east",
            "Weather conditions favorable for operations",
            "Meeting partners in Dubai next month",
            "Equipment upgrade completed successfully"
        ]
        
        for _ in range(random.randint(3, 8)):
            post = {
                "date": self._random_date_in_range("2023-01-01", "2024-12-31"),
                "content": random.choice(coded_messages),
                "likes": random.randint(1, 100),
                "comments": random.randint(0, 20),
                "platform": platform,
                "sentiment": random.choice(["neutral", "positive"])
            }
            posts.append(post)
        
        return posts

    def _identify_suspicious_patterns(self, individual: Dict, platform: str) -> List[str]:
        """Identify suspicious social media patterns"""
        patterns = []
        
        if individual["nationality"] in ["Russian", "Ukrainian"]:
            patterns.append("sanctioned_nationality")
        
        if random.random() < 0.3:
            patterns.append("frequent_location_changes")
        
        if random.random() < 0.2:
            patterns.append("coded_communication")
        
        if platform == "Telegram":
            patterns.append("encrypted_platform")
        
        return patterns

    def _detect_imagery_anomalies(self) -> List[str]:
        """Detect anomalies in satellite imagery"""
        anomalies = []
        
        if random.random() < 0.3:
            anomalies.append("vessel_name_obscured")
        
        if random.random() < 0.2:
            anomalies.append("unusual_cargo_handling")
        
        if random.random() < 0.15:
            anomalies.append("night_operations")
        
        return anomalies

    def _random_date_in_range(self, start_date: str, end_date: str) -> str:
        """Generate random date within range"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        random_date = start + timedelta(
            days=random.randint(0, (end - start).days)
        )
        
        return random_date.strftime("%Y-%m-%d")

    def generate_complete_test_dataset(self) -> Dict:
        """Generate complete test dataset for maritime scenario"""
        dataset = {
            "scenario_metadata": {
                "name": "Maritime Shadow Networks",
                "version": "1.0",
                "generated_date": datetime.now().isoformat(),
                "data_volume_estimate": "2.5GB"
            },
            "vessels": self.vessels,
            "shell_companies": self.shell_companies,
            "data_sources": {
                "ais_tracking": [],
                "corporate_records": self.generate_corporate_structure(),
                "financial_transactions": self.generate_financial_transactions(),
                "social_media": self.generate_social_media_data(),
                "satellite_imagery": self.generate_satellite_imagery_metadata(),
                "port_authority_records": self._generate_port_records(),
                "sanctions_lists": self._generate_sanctions_data(),
                "news_articles": self._generate_news_articles()
            }
        }
        
        # Generate AIS data for each vessel
        for vessel in self.vessels:
            ais_data = self.generate_ais_data(
                vessel["imo"], 
                "2023-01-01", 
                "2024-12-31"
            )
            dataset["data_sources"]["ais_tracking"].extend(ais_data)
        
        return dataset

    def _generate_port_records(self) -> List[Dict]:
        """Generate port authority records"""
        records = []
        
        for vessel in self.vessels:
            for port in random.sample(self.ports, 3):
                record = {
                    "vessel_imo": vessel["imo"],
                    "vessel_name": vessel["name"],
                    "port": port,
                    "arrival_date": self._random_date_in_range("2023-01-01", "2024-12-31"),
                    "departure_date": self._random_date_in_range("2023-01-01", "2024-12-31"),
                    "purpose": random.choice(["bunkering", "cargo_operations", "crew_change", "repairs"]),
                    "agent": f"{port} Maritime Services",
                    "declared_cargo": random.choice(["crude_oil", "fuel_oil", "diesel", "empty"]),
                    "inspector_notes": random.choice([
                        "Routine inspection completed",
                        "Minor documentation irregularities",
                        "All documents in order",
                        "Requires follow-up inspection"
                    ])
                }
                records.append(record)
        
        return records

    def _generate_sanctions_data(self) -> List[Dict]:
        """Generate sanctions list data"""
        sanctions = [
            {
                "entity_name": "Oceanic Shipping Ltd",
                "sanctioning_authority": "OFAC",
                "sanction_type": "Sectoral Sanctions",
                "date_listed": "2023-03-15",
                "reason": "Operating in sanctioned energy sector",
                "confidence": "high"
            },
            {
                "entity_name": "Alexei Volkov",
                "sanctioning_authority": "EU",
                "sanction_type": "Individual Sanctions",
                "date_listed": "2023-06-22",
                "reason": "Facilitating sanctions evasion",
                "confidence": "medium"
            }
        ]
        
        return sanctions

    def _generate_news_articles(self) -> List[Dict]:
        """Generate news article metadata"""
        articles = [
            {
                "title": "Shadow Fleet Continues Sanctioned Oil Trade",
                "publication": "Maritime Intelligence Weekly",
                "date": "2024-08-15",
                "summary": "Investigation reveals continued use of shadow fleet for oil transport",
                "entities_mentioned": ["MT OCEAN SHADOW", "Oceanic Shipping Ltd"],
                "sentiment": "negative"
            },
            {
                "title": "Port Authorities Increase Monitoring of Suspicious Vessels",
                "publication": "Shipping Today",
                "date": "2024-07-22",
                "summary": "Enhanced surveillance measures implemented at major Mediterranean ports",
                "entities_mentioned": ["Piraeus", "Dubai"],
                "sentiment": "neutral"
            }
        ]
        
        return articles

def main():
    """Generate and save test dataset"""
    generator = MaritimeTestDataGenerator()
    dataset = generator.generate_complete_test_dataset()
    
    # Save dataset
    with open("maritime_test_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2, default=str)
    
    print(f"Test dataset generated successfully!")
    print(f"Dataset contains:")
    print(f"- {len(dataset['vessels'])} vessels")
    print(f"- {len(dataset['shell_companies'])} shell companies")
    print(f"- {len(dataset['data_sources']['ais_tracking'])} AIS records")
    print(f"- {len(dataset['data_sources']['financial_transactions'])} transactions")
    print(f"- {len(dataset['data_sources']['social_media'])} social media profiles")

if __name__ == "__main__":
    main()