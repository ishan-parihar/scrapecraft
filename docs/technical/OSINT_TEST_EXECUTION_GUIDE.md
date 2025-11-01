# OSINT System Test Execution Guide

## Overview
This guide provides step-by-step instructions for executing the "Maritime Shadow Networks" test scenario to comprehensively audit the OSINT system capabilities.

## Pre-Test Preparation

### 1. System Configuration
```bash
# Verify system components are operational
python -m pytest tests/test_osint_system.py -v

# Check data source connections
python scripts/verify_data_sources.py --config test_config.json

# Validate language processing capabilities
python scripts/test_language_processing.py --languages en,ru,ar,zh,el,tr
```

### 2. Test Data Setup
```bash
# Load test scenario configuration
python scripts/load_test_scenario.py --scenario maritime_shadow_networks

# Initialize test environment
python scripts/setup_test_environment.py --clean --seed-data
```

### 3. Performance Baseline
```bash
# Establish baseline metrics
python scripts/benchmark_system.py --test basic_collection

# Resource monitoring setup
python scripts/start_monitoring.py --metrics cpu,memory,network,disk_io
```

## Test Execution Phases

### Phase 1: Data Collection Validation (Hours 0-12)

#### 1.1 Maritime Data Sources
```python
# Test AIS data collection
from src.agents.collection.maritime_agent import MaritimeDataCollector

collector = MaritimeDataCollector()
results = collector.collect_vessel_data(
    vessels=["9876543", "8765432", "7654321"],
    timeframe=("2023-01-01", "2024-12-31"),
    data_types=["position", "voyage", "technical"]
)

# Validate collection success rate
assert len(results) >= 3, "Minimum vessel data collection failed"
```

#### 1.2 Corporate Records Collection
```python
# Test corporate registry access
from src.agents.collection.corporate_agent import CorporateRegistryCollector

corp_collector = CorporateRegistryCollector()
companies = corp_collector.search_companies(
    jurisdictions=["UAE", "Cyprus", "Belize"],
    keywords=["shipping", "maritime", "transport"]
)

# Verify multi-jurisdiction coverage
jurisdictions_covered = set(c["jurisdiction"] for c in companies)
assert len(jurisdictions_covered) >= 3, "Insufficient jurisdiction coverage"
```

#### 1.3 Financial Data Collection
```python
# Test financial transaction tracking
from src.agents.collection.financial_agent import FinancialDataCollector

fin_collector = FinancialDataCollector()
transactions = fin_collector.trace_transactions(
    entities=["shell_companies", "vessel_operators"],
    timeframe=("2023-01-01", "2024-12-31")
)

# Validate transaction pattern detection
assert len(transactions) > 0, "No financial transactions detected"
```

### Phase 2: Entity Resolution Testing (Hours 12-20)

#### 2.1 Vessel Entity Resolution
```python
# Test vessel identification across multiple data sources
from src.agents.resolution.entity_resolver import EntityResolver

resolver = EntityResolver()
vessel_entities = resolver.resolve_vessels(
    data_sources=["ais", "registries", "insurance", "class_societies"]
)

# Check resolution accuracy
known_vessels = ["MT OCEAN SHADOW", "MV GOLDEN HORIZON", "MT PACIFIC BRIDGE"]
found_vessels = [v["name"] for v in vessel_entities if v["name"] in known_vessels]
assert len(found_vessels >= 2, "Insufficient vessel entity resolution"
```

#### 2.2 Corporate Entity Linking
```python
# Test corporate relationship mapping
corporate_links = resolver.resolve_corporate_structure(
    seed_entities=["target_companies"],
    depth=5,
    relationship_types=["ownership", "management", "directorship"]
)

# Validate shell company chain detection
max_depth = max(link["depth"] for link in corporate_links)
assert max_depth >= 3, "Shell company chain detection failed"
```

### Phase 3: Pattern Recognition Testing (Hours 20-36)

#### 3.1 AIS Manipulation Detection
```python
# Test AIS spoofing pattern detection
from src.agents.analysis.pattern_detector import PatternDetector

detector = PatternDetector()
ais_patterns = detector.detect_ais_manipulation(
    vessel_data=ais_data,
    analysis_types=["signal_gaps", "position_jumps", "speed_anomalies"]
)

# Verify pattern identification
manipulation_indicators = sum(1 for p in ais_patterns if p["confidence"] > 0.8)
assert manipulation_indicators >= 5, "AIS manipulation patterns not detected"
```

#### 3.2 Financial Flow Analysis
```python
# Test money laundering pattern detection
financial_patterns = detector.detect_money_laundering(
    transaction_data=transactions,
    pattern_types=["layering", "structuring", "trade_based"]
)

# Validate layered payment detection
layered_payments = [p for p in financial_patterns if p["type"] == "layering"]
assert len(layered_payments) >= 3, "Layered payment patterns not detected"
```

### Phase 4: Quality Assurance Testing (Hours 36-44)

#### 4.1 Source Reliability Validation
```python
# Test source quality assessment
from src.agents.synthesis.quality_assurance_agent import QualityAssuranceAgent

qa_agent = QualityAssuranceAgent()
quality_scores = qa_agent.assess_source_quality(
    data_sources=all_collected_data,
    criteria=["reliability", "freshness", "completeness", "bias"]
)

# Verify quality threshold compliance
high_quality_sources = [s for s in quality_scores if s["overall_score"] > 0.7]
assert len(high_quality_sources) >= 10, "Insufficient high-quality data sources"
```

#### 4.2 Cross-Validation Testing
```python
# Test finding validation across sources
validation_results = qa_agent.cross_validate_findings(
    findings=identified_patterns,
    min_sources=2,
    confidence_threshold=0.8
)

# Validate cross-validation success rate
validated_findings = [f for f in validation_results if f["validated"]]
validation_rate = len(validated_findings) / len(validation_results)
assert validation_rate >= 0.7, "Cross-validation rate below threshold"
```

### Phase 5: Report Generation Testing (Hours 44-48)

#### 5.1 Comprehensive Report Generation
```python
# Test full report generation
from src.agents.synthesis.report_generation_agent import ReportGenerator

generator = ReportGenerator()
report = generator.generate_comprehensive_report(
    investigation_data=all_findings,
    template="maritime_investigation",
    formats=["pdf", "json", "csv"]
)

# Validate report completeness
required_sections = [
    "executive_summary", "methodology", "network_architecture",
    "operational_analysis", "risk_assessment"
]

missing_sections = [s for s in required_sections if s not in report]
assert len(missing_sections) == 0, f"Missing report sections: {missing_sections}"
```

#### 5.2 Intelligence Quality Assessment
```python
# Test intelligence insight quality
insight_quality = generator.assess_intelligence_quality(
    report=report,
    criteria=["relevance", "novelty", "actionability", "accuracy"]
)

# Verify intelligence standards
overall_quality = insight_quality["overall_score"]
assert overall_quality >= 0.8, "Intelligence quality below acceptable threshold"
```

## Performance Monitoring

### Real-time Metrics Collection
```python
# Monitor system performance during test
from src.utils.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_monitoring(
    metrics=["cpu_usage", "memory_usage", "processing_time", "data_throughput"],
    interval=60  # seconds
)

# Collect performance data
performance_data = monitor.get_metrics()
```

### Resource Utilization Analysis
```bash
# Generate performance report
python scripts/generate_performance_report.py --test_run maritime_test

# Compare against baseline
python scripts/compare_performance.py --baseline baseline.json --current test_run.json
```

## Success Criteria Validation

### Quantitative Metrics Check
```python
# Automated success criteria validation
def validate_success_criteria(test_results):
    criteria = {
        "data_sources_accessed": len(test_results["data_sources"]) >= 12,
        "entities_identified": len(test_results["entities"]) >= 300,
        "relationships_mapped": len(test_results["relationships"]) >= 1000,
        "patterns_identified": len(test_results["patterns"]) >= 15,
        "accuracy_rate": test_results["accuracy"] >= 0.90,
        "processing_time": test_results["duration_hours"] <= 72
    }
    
    passed_criteria = sum(criteria.values())
    total_criteria = len(criteria)
    
    return {
        "overall_success": passed_criteria / total_criteria >= 0.8,
        "detailed_results": criteria,
        "score": passed_criteria / total_criteria
    }

validation_results = validate_success_criteria(test_results)
```

### Qualitative Assessment
```python
# Subject matter expert validation template
qualitative_assessment = {
    "insight_quality": {
        "depth": "Scale 1-5",
        "relevance": "Scale 1-5", 
        "novelty": "Scale 1-5",
        "actionability": "Scale 1-5"
    },
    "contextual_understanding": {
        "geopolitical_awareness": "Scale 1-5",
        "cultural_sensitivity": "Scale 1-5",
        "legal_compliance": "Scale 1-5"
    },
    "report_clarity": {
        "executive_summary": "Scale 1-5",
        "technical_details": "Scale 1-5",
        "recommendations": "Scale 1-5"
    }
}
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Data Collection Failures
```python
# Symptom: Missing data sources
# Solution: Implement fallback sources
if len(collected_data) < expected_sources:
    fallback_sources = activate_fallback_data_sources()
    collected_data.extend(fallback_sources)
```

#### Entity Resolution Issues
```python
# Symptom: Low entity resolution accuracy
# Solution: Adjust matching thresholds
resolver = EntityResolver(match_threshold=0.7)  # Lower threshold for testing
resolved_entities = resolver.resolve_entities(data)
```

#### Pattern Detection Problems
```python
# Symptom: Few patterns detected
# Solution: Adjust sensitivity parameters
detector = PatternDetector(
    sensitivity=0.6,  # Increase sensitivity
    min_occurrences=2  # Lower minimum occurrences
)
```

#### Performance Bottlenecks
```python
# Symptom: Slow processing
# Solution: Implement parallel processing
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(process_data_chunk, data_chunks))
```

## Post-Test Analysis

### Results Summary Generation
```python
# Generate comprehensive test results
def generate_test_summary(test_results, performance_data, validation_results):
    summary = {
        "test_metadata": {
            "scenario": "Maritime Shadow Networks",
            "execution_time": datetime.now().isoformat(),
            "duration_hours": test_results["duration_hours"]
        },
        "collection_metrics": {
            "data_sources_accessed": len(test_results["data_sources"]),
            "data_volume_mb": test_results["data_volume"],
            "languages_processed": test_results["languages"]
        },
        "analysis_metrics": {
            "entities_identified": len(test_results["entities"]),
            "relationships_mapped": len(test_results["relationships"]),
            "patterns_detected": len(test_results["patterns"])
        },
        "quality_metrics": {
            "accuracy_rate": test_results["accuracy"],
            "cross_validation_rate": validation_results["validation_rate"],
            "source_quality_score": test_results["source_quality"]
        },
        "performance_metrics": {
            "peak_cpu_usage": max(performance_data["cpu_usage"]),
            "peak_memory_gb": max(performance_data["memory_usage"]),
            "processing_efficiency": test_results["entities_per_hour"]
        },
        "overall_assessment": {
            "success_rate": validation_results["score"],
            "critical_findings": test_results["critical_findings"],
            "recommendations": test_results["recommendations"]
        }
    }
    
    return summary

test_summary = generate_test_summary(test_results, performance_data, validation_results)
```

### System Optimization Recommendations
```python
# Generate optimization suggestions based on test results
def generate_optimization_recommendations(test_summary):
    recommendations = []
    
    if test_summary["collection_metrics"]["data_sources_accessed"] < 15:
        recommendations.append({
            "category": "Data Collection",
            "priority": "HIGH",
            "recommendation": "Expand data source portfolio to include additional maritime databases",
            "expected_improvement": "15% increase in data coverage"
        })
    
    if test_summary["quality_metrics"]["accuracy_rate"] < 0.95:
        recommendations.append({
            "category": "Entity Resolution",
            "priority": "MEDIUM", 
            "recommendation": "Improve entity matching algorithms with fuzzy logic",
            "expected_improvement": "5% increase in resolution accuracy"
        })
    
    if test_summary["performance_metrics"]["peak_cpu_usage"] > 0.8:
        recommendations.append({
            "category": "Performance",
            "priority": "HIGH",
            "recommendation": "Implement distributed processing for large datasets",
            "expected_improvement": "30% reduction in processing time"
        })
    
    return recommendations

optimization_recommendations = generate_optimization_recommendations(test_summary)
```

## Test Completion Checklist

### Pre-Test Validation
- [ ] All system components operational
- [ ] Data source connections verified
- [ ] Language processing capabilities confirmed
- [ ] Performance monitoring active
- [ ] Test environment initialized

### During Test Execution
- [ ] Data collection proceeding from all required sources
- [ ] Entity resolution meeting accuracy thresholds
- [ ] Pattern detection identifying expected patterns
- [ ] Quality assurance processes functioning
- [ ] Performance metrics within acceptable ranges

### Post-Test Validation
- [ ] All report sections generated
- [ ] Success criteria met or exceeded
- [ ] Performance data collected and analyzed
- [ ] Issues documented and resolved
- [ ] Optimization recommendations generated

### Final Deliverables
- [ ] Comprehensive test report
- [ ] Performance analysis report
- [ ] System optimization recommendations
- [ ] Quality assurance validation
- [ ] Executive summary of findings

This execution guide provides a complete framework for conducting a thorough audit of the OSINT system capabilities using the maritime shadow networks scenario.