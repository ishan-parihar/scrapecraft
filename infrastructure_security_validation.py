#!/usr/bin/env python3
"""
Infrastructure Security Validation for ScrapeCraft OSINT Platform

This script validates the security infrastructure components without requiring
Python dependencies, focusing on Kubernetes security, file structure, and configuration.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class InfrastructureSecurityValidator:
    """Infrastructure security validation suite."""
    
    def __init__(self):
        self.validation_results: List[Dict[str, Any]] = []
        self.critical_issues = []
        self.warnings = []
        self.passed_checks = []
        self.project_root = Path(__file__).parent
    
    def add_result(self, check_name: str, passed: bool, details: str = "", severity: str = "MEDIUM"):
        """Add validation result."""
        result = {
            "check_name": check_name,
            "passed": passed,
            "details": details,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.validation_results.append(result)
        
        if passed:
            self.passed_checks.append(check_name)
        else:
            if severity.upper() in ["CRITICAL", "HIGH"]:
                self.critical_issues.append(f"{check_name}: {details}")
            else:
                self.warnings.append(f"{check_name}: {details}")
    
    def validate_kubernetes_security_infrastructure(self):
        """Validate Kubernetes security manifests."""
        print("Validating Kubernetes security infrastructure...")
        
        security_files = [
            "k8s/security/network-policies.yaml",
            "k8s/security/rbac.yaml", 
            "k8s/security/falco.yaml"
        ]
        
        for security_file in security_files:
            file_path = self.project_root / security_file
            if file_path.exists():
                self.add_result(
                    f"K8s Security File: {security_file}",
                    True,
                    f"Security manifest exists: {file_path.stat().st_size} bytes"
                )
                
                # Validate YAML syntax
                try:
                    with open(file_path, 'r') as f:
                        docs = list(yaml.safe_load_all(f))
                    self.add_result(
                        f"K8s YAML Syntax: {security_file}",
                        True,
                        f"Valid YAML syntax ({len(docs)} documents)"
                    )
                except yaml.YAMLError as e:
                    self.add_result(
                        f"K8s YAML Syntax: {security_file}",
                        False,
                        f"YAML syntax error: {e}",
                        "HIGH"
                    )
            else:
                self.add_result(
                    f"K8s Security File: {security_file}",
                    False,
                    "Critical security manifest missing",
                    "CRITICAL"
                )
    
    def validate_network_policies(self):
        """Validate network policy configuration."""
        print("Validating network policies...")
        
        network_policy_path = self.project_root / "k8s/security/network-policies.yaml"
        if not network_policy_path.exists():
            return
        
        try:
            with open(network_policy_path, 'r') as f:
                policies = list(yaml.safe_load_all(f))
            
            # Check for default deny policy
            default_deny_found = False
            dns_policy_found = False
            
            for policy in policies:
                if policy and policy.get('metadata', {}).get('name') == 'default-deny-all':
                    default_deny_found = True
                    self.add_result(
                        "Default Deny Network Policy",
                        True,
                        "Default deny all traffic policy found"
                    )
                
                if policy and policy.get('metadata', {}).get('name') == 'allow-dns':
                    dns_policy_found = True
                    self.add_result(
                        "DNS Allow Network Policy",
                        True,
                        "DNS resolution policy found"
                    )
            
            if not default_deny_found:
                self.add_result(
                    "Default Deny Network Policy",
                    False,
                    "Default deny all policy not found",
                    "CRITICAL"
                )
            
            if not dns_policy_found:
                self.add_result(
                    "DNS Allow Network Policy",
                    False,
                    "DNS allow policy not found - services may not resolve",
                    "HIGH"
                )
                
        except Exception as e:
            self.add_result(
                "Network Policy Validation",
                False,
                f"Error validating network policies: {e}",
                "HIGH"
            )
    
    def validate_rbac_configuration(self):
        """Validate RBAC configuration."""
        print("Validating RBAC configuration...")
        
        rbac_path = self.project_root / "k8s/security/rbac.yaml"
        if not rbac_path.exists():
            return
        
        try:
            with open(rbac_path, 'r') as f:
                rbac_resources = list(yaml.safe_load_all(f))
            
            # Check for essential RBAC components
            roles_found = False
            role_bindings_found = False
            service_accounts_found = False
            
            for resource in rbac_resources:
                if not resource:
                    continue
                    
                resource_type = resource.get('kind', '').lower()
                if resource_type == 'role':
                    roles_found = True
                elif resource_type == 'rolebinding':
                    role_bindings_found = True
                elif resource_type == 'serviceaccount':
                    service_accounts_found = True
            
            if roles_found:
                self.add_result(
                    "RBAC Roles",
                    True,
                    "RBAC roles defined"
                )
            else:
                self.add_result(
                    "RBAC Roles",
                    False,
                    "No RBAC roles found",
                    "HIGH"
                )
            
            if role_bindings_found:
                self.add_result(
                    "RBAC Role Bindings",
                    True,
                    "RBAC role bindings defined"
                )
            else:
                self.add_result(
                    "RBAC Role Bindings",
                    False,
                    "No RBAC role bindings found",
                    "HIGH"
                )
            
            if service_accounts_found:
                self.add_result(
                    "Service Accounts",
                    True,
                    "Service accounts defined"
                )
            else:
                self.add_result(
                    "Service Accounts",
                    False,
                    "No service accounts found",
                    "MEDIUM"
                )
                
        except Exception as e:
            self.add_result(
                "RBAC Validation",
                False,
                f"Error validating RBAC: {e}",
                "HIGH"
            )
    
    def validate_runtime_security(self):
        """Validate Falco runtime security configuration."""
        print("Validating runtime security...")
        
        falco_path = self.project_root / "k8s/security/falco.yaml"
        if not falco_path.exists():
            return
        
        try:
            with open(falco_path, 'r') as f:
                falco_configs = list(yaml.safe_load_all(f))
                # Get the first document (ConfigMap) for validation
                falco_config = falco_configs[0] if falco_configs else None
            
            if falco_config:
                self.add_result(
                    "Falco Security Configuration",
                    True,
                    "Falco runtime security configuration found"
                )
                
                # Check for security rules
                if 'rules' in falco_config or 'spec' in falco_config:
                    self.add_result(
                        "Falco Security Rules",
                        True,
                        "Security rules defined in Falco configuration"
                    )
                else:
                    self.add_result(
                        "Falco Security Rules",
                        False,
                        "No security rules found in Falco configuration",
                        "MEDIUM"
                    )
            else:
                self.add_result(
                    "Falco Security Configuration",
                    False,
                    "Empty Falco configuration",
                    "MEDIUM"
                )
                
        except Exception as e:
            self.add_result(
                "Runtime Security Validation",
                False,
                f"Error validating Falco configuration: {e}",
                "HIGH"
            )
    
    def validate_security_file_structure(self):
        """Validate security file structure."""
        print("Validating security file structure...")
        
        # Backend security files
        backend_security_files = [
            "backend/app/security/config.py",
            "backend/app/security/integration.py",
            "backend/app/services/enhanced_auth_service.py",
            "backend/app/api/enhanced_auth.py",
            "backend/app/main_enhanced.py"
        ]
        
        for security_file in backend_security_files:
            file_path = self.project_root / security_file
            if file_path.exists():
                self.add_result(
                    f"Security Code File: {security_file}",
                    True,
                    f"Security module exists: {file_path.stat().st_size} bytes"
                )
            else:
                self.add_result(
                    f"Security Code File: {security_file}",
                    False,
                    "Security module missing",
                    "HIGH"
                )
        
        # Test files
        test_security_files = [
            "tests/security/comprehensive_security_test.py",
            "tests/security/test_security.py"
        ]
        
        for test_file in test_security_files:
            file_path = self.project_root / test_file
            if file_path.exists():
                self.add_result(
                    f"Security Test File: {test_file}",
                    True,
                    f"Security test exists: {file_path.stat().st_size} bytes"
                )
            else:
                self.add_result(
                    f"Security Test File: {test_file}",
                    False,
                    "Security test missing",
                    "MEDIUM"
                )
    
    def validate_deployment_configuration(self):
        """Validate deployment security configurations."""
        print("Validating deployment security configurations...")
        
        # Check main deployment files
        deployment_files = [
            "k8s/backend-deployment.yaml",
            "k8s/frontend-deployment.yaml",
            "k8s/postgres-deployment.yaml",
            "k8s/redis-deployment.yaml"
        ]
        
        for deployment_file in deployment_files:
            file_path = self.project_root / deployment_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        deployments = list(yaml.safe_load_all(f))
                        # Get the first deployment document for validation
                        deployment = deployments[0] if deployments else None
                    
                    if deployment and deployment.get('spec'):
                        # Check for security context
                        security_context = deployment['spec'].get('template', {}).get('spec', {}).get('securityContext')
                        if security_context:
                            self.add_result(
                                f"Security Context: {deployment_file}",
                                True,
                                "Pod security context defined"
                            )
                        else:
                            self.add_result(
                                f"Security Context: {deployment_file}",
                                False,
                                "No pod security context defined",
                                "MEDIUM"
                            )
                        
                        # Check for non-root user
                        containers = deployment['spec'].get('template', {}).get('spec', {}).get('containers', [])
                        non_root_found = False
                        
                        for container in containers:
                            container_security = container.get('securityContext', {})
                            if container_security.get('runAsNonRoot') or container_security.get('runAsUser', 0) != 0:
                                non_root_found = True
                                break
                        
                        if non_root_found:
                            self.add_result(
                                f"Non-Root User: {deployment_file}",
                                True,
                                "Containers configured to run as non-root"
                            )
                        else:
                            self.add_result(
                                f"Non-Root User: {deployment_file}",
                                False,
                                "Containers may run as root user",
                                "MEDIUM"
                            )
                    
                except Exception as e:
                    self.add_result(
                        f"Deployment Validation: {deployment_file}",
                        False,
                        f"Error validating deployment: {e}",
                        "HIGH"
                    )
            else:
                self.add_result(
                    f"Deployment File: {deployment_file}",
                    False,
                    "Deployment file missing",
                    "HIGH"
                )
    
    def validate_environment_configuration(self):
        """Validate environment and configuration files."""
        print("Validating environment configuration...")
        
        config_files = [
            "config/environments/development.yaml",
            "config/environments/production.yaml",
            "config/environments/staging.yaml",
            ".env.example"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                self.add_result(
                    f"Config File: {config_file}",
                    True,
                    f"Configuration file exists: {file_path.stat().st_size} bytes"
                )
            else:
                self.add_result(
                    f"Config File: {config_file}",
                    False,
                    "Configuration file missing",
                    "MEDIUM"
                )
    
    def check_security_documentation(self):
        """Check for security documentation."""
        print("Validating security documentation...")
        
        security_docs = [
            "SECURITY_DEPLOYMENT_GUIDE.md",
            "SECURITY_HARDENING_IMPLEMENTATION.md",
            "OSINT_REMEDIATION_PLAN.md"
        ]
        
        for doc in security_docs:
            doc_path = self.project_root / doc
            if doc_path.exists():
                self.add_result(
                    f"Security Documentation: {doc}",
                    True,
                    f"Security documentation exists: {doc_path.stat().st_size} bytes"
                )
            else:
                self.add_result(
                    f"Security Documentation: {doc}",
                    False,
                    "Security documentation missing",
                    "MEDIUM"
                )
    
    def run_comprehensive_validation(self):
        """Run all infrastructure security validations."""
        print("=" * 80)
        print("SCRAPECRAFT INFRASTRUCTURE SECURITY VALIDATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"Project Root: {self.project_root}")
        print()
        
        # Run validations
        self.validate_kubernetes_security_infrastructure()
        self.validate_network_policies()
        self.validate_rbac_configuration()
        self.validate_runtime_security()
        self.validate_security_file_structure()
        self.validate_deployment_configuration()
        self.validate_environment_configuration()
        self.check_security_documentation()
        
        # Generate report
        total_checks = len(self.validation_results)
        passed_checks = len(self.passed_checks)
        failed_checks = total_checks - passed_checks
        
        print(f"\nINFRASTRUCTURE SECURITY VALIDATION SUMMARY:")
        print(f"  Total Checks: {total_checks}")
        print(f"  Passed: {passed_checks}")
        print(f"  Failed: {failed_checks}")
        print(f"  Critical Issues: {len(self.critical_issues)}")
        print(f"  Warnings: {len(self.warnings)}")
        print()
        
        # Print critical issues first
        if self.critical_issues:
            print("CRITICAL ISSUES:")
            for issue in self.critical_issues:
                print(f"  🚨 {issue}")
            print()
        
        # Print warnings
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()
        
        # Print passed checks (summary only)
        if self.passed_checks:
            print(f"PASSED CHECKS ({len(self.passed_checks)}):")
            # Show first 10 passed checks
            for check in self.passed_checks[:10]:
                print(f"  ✅ {check}")
            if len(self.passed_checks) > 10:
                print(f"  ... and {len(self.passed_checks) - 10} more")
            print()
        
        # Overall assessment
        if self.critical_issues:
            overall_status = "CRITICAL"
            status_emoji = "🚨"
        elif self.warnings:
            overall_status = "WARNING"
            status_emoji = "⚠️"
        else:
            overall_status = "SECURE"
            status_emoji = "✅"
        
        print(f"OVERALL INFRASTRUCTURE SECURITY STATUS: {status_emoji} {overall_status}")
        print("=" * 80)
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "validation_type": "infrastructure_security",
            "overall_status": overall_status,
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "critical_issues": len(self.critical_issues),
                "warnings": len(self.warnings)
            },
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "passed_checks": self.passed_checks,
            "detailed_results": self.validation_results
        }
        
        report_path = self.project_root / "infrastructure_security_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")
        
        return overall_status, report_data

def main():
    """Main validation function."""
    validator = InfrastructureSecurityValidator()
    status, report = validator.run_comprehensive_validation()
    
    # Exit with appropriate code
    if status == "CRITICAL":
        sys.exit(2)
    elif status == "WARNING":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()