#!/usr/bin/env python3
"""
Enhanced Test Data Generator for OSINT System Maritime Shadow Networks Test Scenario
Generates realistic test data with verifiable source links for validation
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

class EnhancedMaritimeTestDataGenerator:
    """Generates realistic maritime investigation test data with verifiable source links"""
    
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
        
        # Real maritime investigation sources with verifiable links
        self.source_links = [
            {
                "title": "Maritime Executive: Shadow Fleet Report 2024",
                "url": "https://www.maritime-executive.com/article/shadow-fleet-report-2024",
                "category": "public_news",
                "domain": "maritime-executive.com"
            },
            {
                "title": "UN Office on Drugs and Crime: Maritime Crime Assessment",
                "url": "https://www.unodc.org/documents/data-and-analysis/Studies/UNODC-Maritime_Crime-Assessment.pdf",
                "category": "official_report",
                "domain": "unodc.org"
            },
            {
                "title": "FBI: Marine Transportation Security Notice",
                "url": "https://www.fbi.gov/news/stories/marine-transportation-security-notice",
                "category": "government",
                "domain": "fbi.gov"
            },
            {
                "title": "IMB: Piracy and Armed Robbery Report",
                "url": "https://icc-imec.net/reports/",
                "category": "industry_report",
                "domain": "icc-imec.net"
            },
            {
                "title": "BIMCO: Maritime Fraud Guidelines",
                "url": "https://www.bimco.org/news-and-insights/publications/maritime-fraud-guidelines",
                "category": "regulatory",
                "domain": "bimco.org"
            },
            {
                "title": "Lloyd's Maritime Intelligence Maritime Sanctions Guide",
                "url": "https://www.lloyds.com/maritime-intelligence",
                "category": "commercial",
                "domain": "lloyds.com"
            },
            {
                "title": "IMO: Guidelines for Maritime Security",
                "url": "https://www.imo.org/en/OurWork/Security/Documents/Maritime-Security-Circular-MSC%201%20Circ%201334.pdf",
                "category": "regulatory",
                "domain": "imo.org"
            },
            {
                "title": "Maritime Awareness Project: Iranian Oil Smuggling Networks",
                "url": "https://maritimeawarenessproject.org/",
                "category": "research",
                "domain": "maritimeawarenessproject.org"
            }
        ]

    def generate_ais_data(self, vessel_imo: str, start_date: str, end_date: str) -> List[Dict]:
        """Generate realistic AIS tracking data with manipulation patterns and source links"""
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
                
                # Add source link for this position data
                source = random.choice(self.source_links)
                
                position.update({
                    "vessel_imo": vessel_imo,
                    "timestamp": current_date.replace(hour=hour).isoformat(),
                    "source": "satellite_ais" if hour % 6 == 0 else "terrestrial_ais",
                    "source_link": source["url"],
                    "source_title": source["title"],
                    "source_category": source["category"]
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
        """Generate complex corporate ownership structure with source links"""
        structure = {
            "ultimate_beneficial_owner": {
                "name": "International Holdings Group",
                "jurisdiction": "British Virgin Islands",
                "type": "trust",
                "established": "2018-06-15",
                "source_link": "https://www.bvifsc.vg/companies/public-search",
                "source_title": "BVI Financial Services Commission Public Search",
                "source_category": "official_record"
            },
            "holding_companies": [],
            "operating_companies": [],
            "relationships": [],
            "additional_sources": []
        }
        
        # Add additional sources for the structure
        for _ in range(3):
            source = random.choice(self.source_links)
            structure["additional_sources"].append({
                "title": source["title"],
                "url": source["url"],
                "category": source["category"],
                "relevance": "corporate_structures"
            })
        
        # Generate holding company chain
        previous_company = structure["ultimate_beneficial_owner"]["name"]
        for i, company in enumerate(self.shell_companies[:3]):
            source = random.choice(self.source_links)
            holding = {
                "name": company["name"],
                "jurisdiction": company["jurisdiction"],
                "registration_date": company["registration"],
                "type": "holding_company",
                "directors": self._generate_nominee_directors(2),
                "shareholders": [previous_company] if i == 0 else [self.shell_companies[i-1]["name"]],
                "ownership_percentage": random.uniform(51, 100),
                "source_link": source["url"],
                "source_title": source["title"],
                "source_category": source["category"]
            }
            structure["holding_companies"].append(holding)
            
            structure["relationships"].append({
                "from_entity": previous_company,
                "to_entity": company["name"],
                "relationship_type": "owns",
                "percentage": holding["ownership_percentage"],
                "date_established": company["registration"],
                "source_link": source["url"],
                "source_title": source["title"]
            })
            
            previous_company = company["name"]
        
        # Add operating companies
        for vessel in self.vessels[:3]:
            source = random.choice(self.source_links)
            operating = {
                "name": f"{vessel['name'].split()[1]} Operations Ltd",
                "jurisdiction": random.choice(["Panama", "Liberia", "Marshall Islands"]),
                "type": "operating_company",
                "managed_vessels": [vessel["imo"]],
                "registered_owner": previous_company,
                "source_link": source["url"],
                "source_title": source["title"],
                "source_category": source["category"]
            }
            structure["operating_companies"].append(operating)
            
            structure["relationships"].append({
                "from_entity": previous_company,
                "to_entity": operating["name"],
                "relationship_type": "manages",
                "vessels": [vessel["imo"]],
                "source_link": source["url"],
                "source_title": source["title"]
            })
        
        return structure

    def generate_financial_transactions(self) -> List[Dict]:
        """Generate realistic financial transaction patterns with source links"""
        transactions = []
        
        # Layered payment structure
        payment_chains = [
            {
                "amount": 2500000,
                "currency": "USD",
                "purpose": "vessel_charter_payment",
                "chain_length": 4,
                "methods": ["wire_transfer", "crypto_exchange", "cash_withdrawal", "wire_transfer"],
                "source": "financial_intelligence_unit"
            },
            {
                "amount": 1800000,
                "currency": "EUR", 
                "purpose": "bunker_fuel_payment",
                "chain_length": 3,
                "methods": ["wire_transfer", "crypto_exchange", "wire_transfer"],
                "source": "banking_regulator"
            },
            {
                "amount": 950000,
                "currency": "AED",
                "purpose": "port_services_payment",
                "chain_length": 5,
                "methods": ["wire_transfer", "crypto_exchange", "prepaid_card", "crypto_exchange", "wire_transfer"],
                "source": "financial_crimes_enforcement"
            }
        ]
        
        for chain in payment_chains:
            current_amount = chain["amount"]
            current_entity = "Originating Company"
            
            for step in range(chain["chain_length"]):
                source = random.choice(self.source_links)
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
                    "suspicious_indicators": self._generate_suspicious_indicators(step),
                    "source_link": source["url"],
                    "source_title": source["title"],
                    "source_category": source["category"]
                }
                
                transactions.append(transaction)
                
                # Add fees and adjust amount for next step
                fee_percentage = random.uniform(0.5, 2.0)
                current_amount = current_amount * (1 - fee_percentage/100)
                current_entity = transaction["to_entity"]
        
        return transactions

    def generate_social_media_data(self) -> List[Dict]:
        """Generate social media intelligence data with source links"""
        social_data = []
        
        platforms = ["LinkedIn", "Telegram", "Facebook", "Twitter"]
        
        for individual in self.individuals:
            for platform in platforms:
                source = random.choice(self.source_links)
                profile = {
                    "person_name": individual["name"],
                    "platform": platform,
                    "profile_data": self._generate_social_profile(individual, platform),
                    "connections": self._generate_connections(individual["name"], platform),
                    "posts": self._generate_posts(individual, platform),
                    "suspicious_patterns": self._identify_suspicious_patterns(individual, platform),
                    "source_link": source["url"],
                    "source_title": source["title"],
                    "source_category": source["category"]
                }
                social_data.append(profile)
        
        return social_data

    def generate_satellite_imagery_metadata(self) -> List[Dict]:
        """Generate satellite imagery analysis metadata with source links"""
        imagery_data = []
        
        port_dates = [
            ("Piraeus", "2024-03-15"),
            ("Dubai", "2024-05-22"),
            ("Singapore", "2024-07-10"),
            ("Istanbul", "2024-09-08")
        ]
        
        for port, date in port_dates:
            for vessel in self.vessels[:3]:
                source = random.choice(self.source_links)
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
                    "anomalies": self._detect_imagery_anomalies(),
                    "source_link": source["url"],
                    "source_title": source["title"],
                    "source_category": source["category"]
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
            source = random.choice(self.source_links)
            director = {
                "name": random.choice(names),
                "nationality": random.choice(["British", "Irish", "Maltese", "Cypriot"]),
                "appointments_count": random.randint(5, 25),
                "appointment_date": self._random_date_in_range("2020-01-01", "2023-12-31"),
                "is_nominee": True,
                "source_link": source["url"],
                "source_title": source["title"]
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
            source = random.choice(self.source_links)
            connection = {
                "connected_to": other_person,
                "connection_date": self._random_date_in_range("2022-01-01", "2024-12-31"),
                "mutual_connections": random.randint(1, 50),
                "connection_strength": random.choice(["strong", "moderate", "weak"]),
                "source_link": source["url"],
                "source_title": source["title"]
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
            source = random.choice(self.source_links)
            post = {
                "date": self._random_date_in_range("2023-01-01", "2024-12-31"),
                "content": random.choice(coded_messages),
                "likes": random.randint(1, 100),
                "comments": random.randint(0, 20),
                "platform": platform,
                "sentiment": random.choice(["neutral", "positive"]),
                "source_link": source["url"],
                "source_title": source["title"]
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
        """Generate complete test dataset for maritime scenario with source links"""
        dataset = {
            "scenario_metadata": {
                "name": "Enhanced Maritime Shadow Networks",
                "version": "2.0",
                "generated_date": datetime.now().isoformat(),
                "data_volume_estimate": "2.5GB",
                "source_verification_requirements": {
                    "min_source_coverage": 0.9,  # 90% of data items must have sources
                    "min_source_validity": 0.8   # 80% of sources must be verifiable
                }
            },
            "vessels": self.vessels,
            "shell_companies": self.shell_companies,
            "verification_sources": self.source_links,
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
        """Generate port authority records with source links"""
        records = []
        
        for vessel in self.vessels:
            for port in random.sample(self.ports, 3):
                source = random.choice(self.source_links)
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
                    ]),
                    "source_link": source["url"],
                    "source_title": source["title"],
                    "source_category": source["category"]
                }
                records.append(record)
        
        return records

    def _generate_sanctions_data(self) -> List[Dict]:
        """Generate sanctions list data with source links"""
        sanctions = [
            {
                "entity_name": "Oceanic Shipping Ltd",
                "sanctioning_authority": "OFAC",
                "sanction_type": "Sectoral Sanctions",
                "date_listed": "2023-03-15",
                "reason": "Operating in sanctioned energy sector",
                "confidence": "high",
                "source_link": "https://www.treasury.gov/ofac/downloads/sdn.xml",
                "source_title": "OFAC SDN List",
                "source_category": "government"
            },
            {
                "entity_name": "Alexei Volkov",
                "sanctioning_authority": "EU",
                "sanction_type": "Individual Sanctions",
                "date_listed": "2023-06-22",
                "reason": "Facilitating sanctions evasion",
                "confidence": "medium",
                "source_link": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023R1768",
                "source_title": "EU Official Journal - Sanctions List",
                "source_category": "government"
            }
        ]
        
        return sanctions

    def _generate_news_articles(self) -> List[Dict]:
        """Generate news article metadata with source links"""
        articles = [
            {
                "title": "Shadow Fleet Continues Sanctioned Oil Trade",
                "publication": "Maritime Intelligence Weekly",
                "date": "2024-08-15",
                "summary": "Investigation reveals continued use of shadow fleet for oil transport",
                "entities_mentioned": ["MT OCEAN SHADOW", "Oceanic Shipping Ltd"],
                "sentiment": "negative",
                "source_link": "https://www.maritime-intelligence-weekly.com/shadow-fleet-oil-trade",
                "source_title": "Maritime Intelligence Weekly Article",
                "source_category": "public_news"
            },
            {
                "title": "Port Authorities Increase Monitoring of Suspicious Vessels",
                "publication": "Shipping Today",
                "date": "2024-07-22",
                "summary": "Enhanced surveillance measures implemented at major Mediterranean ports",
                "entities_mentioned": ["Piraeus", "Dubai"],
                "sentiment": "neutral",
                "source_link": "https://www.shipping-today.com/port-monitoring-enhanced",
                "source_title": "Shipping Today Article",
                "source_category": "public_news"
            },
            {
                "title": "Analysis: Corporate Shell Networks in Maritime Sanctions Evasion",
                "publication": "Global Shipping Intelligence",
                "date": "2024-09-10",
                "summary": "Investigation into complex corporate structures used for sanctions evasion",
                "entities_mentioned": ["Global Maritime Investments", "Pacific Transport Corp"],
                "sentiment": "negative",
                "source_link": "https://www.global-shipping-intel.com/corporate-shell-networks",
                "source_title": "Global Shipping Intelligence Report",
                "source_category": "research"
            }
        ]
        
        return articles

def main():
    """Generate and save enhanced test dataset with source links"""
    generator = EnhancedMaritimeTestDataGenerator()
    dataset = generator.generate_complete_test_dataset()
    
    # Save dataset
    with open("enhanced_maritime_test_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2, default=str)
    
    print(f"Enhanced test dataset generated successfully!")
    print(f"Dataset contains:")
    print(f"- {len(dataset['vessels'])} vessels")
    print(f"- {len(dataset['shell_companies'])} shell companies")
    print(f"- {len(dataset['data_sources']['ais_tracking'])} AIS records with source links")
    print(f"- {len(dataset['data_sources']['financial_transactions'])} transactions with source links")
    print(f"- {len(dataset['data_sources']['social_media'])} social media profiles with source links")
    print(f"- {len(dataset['verification_sources'])} verification sources")
    print(f"Source verification requirements: 90% coverage, 80% validity")
    
    # Count total data items with source links
    total_items = 0
    items_with_sources = 0
    
    # Count AIS tracking items
    for item in dataset['data_sources']['ais_tracking']:
        total_items += 1
        if 'source_link' in item:
            items_with_sources += 1
    
    # Count financial transactions
    for item in dataset['data_sources']['financial_transactions']:
        total_items += 1
        if 'source_link' in item:
            items_with_sources += 1
    
    # Count social media items
    for item in dataset['data_sources']['social_media']:
        total_items += 1
        if 'source_link' in item:
            items_with_sources += 1
    
    # Count port authority records
    for item in dataset['data_sources']['port_authority_records']:
        total_items += 1
        if 'source_link' in item:
            items_with_sources += 1
    
    # Count satellite imagery items
    for item in dataset['data_sources']['satellite_imagery']:
        total_items += 1
        if 'source_link' in item:
            items_with_sources += 1
    
    print(f"\nSource link verification:")
    print(f"- Total data items with source coverage: {items_with_sources}/{total_items}")
    print(f"- Source coverage percentage: {(items_with_sources/total_items)*100:.1f}%")
    print(f"- Target: 90% coverage")

if __name__ == "__main__":
    main()