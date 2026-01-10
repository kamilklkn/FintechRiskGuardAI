"""
Safety Engine Module - Policy-based content filtering

The Safety Engine provides guardrails for agent input/output.
Supports PII detection, content filtering, and custom policies.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Pattern
from dataclasses import dataclass, field
from enum import Enum


class PolicyAction(str, Enum):
    """Actions to take when policy is violated"""
    BLOCK = "block"           # Block the content entirely
    ANONYMIZE = "anonymize"   # Replace sensitive content
    REPLACE = "replace"       # Replace with placeholder
    WARN = "warn"            # Allow but log warning
    RAISE = "raise"          # Raise an exception


@dataclass
class PolicyViolation:
    """Represents a policy violation"""
    policy_name: str
    violation_type: str
    matched_content: str
    position: tuple  # (start, end)
    severity: str = "medium"


class DisallowedOperation(Exception):
    """Exception raised when content violates policy"""
    def __init__(self, message: str, violations: List[PolicyViolation]):
        self.message = message
        self.violations = violations
        super().__init__(message)


class Rule(ABC):
    """Base class for policy rules"""
    
    @abstractmethod
    def check(self, text: str) -> List[PolicyViolation]:
        """Check text against this rule"""
        pass


class Action(ABC):
    """Base class for policy actions"""
    
    @abstractmethod
    def apply(self, text: str, violations: List[PolicyViolation]) -> str:
        """Apply action to text based on violations"""
        pass


class RegexRule(Rule):
    """Rule that matches content using regex patterns"""
    
    def __init__(self, 
                 patterns: Dict[str, List[str]],
                 keywords: List[str] = None,
                 name: str = "RegexRule"):
        """
        Args:
            patterns: Dict mapping category -> list of regex patterns
            keywords: List of keywords to match
            name: Rule name for reporting
        """
        self.name = name
        self.patterns: Dict[str, List[Pattern]] = {}
        self.keywords = [k.lower() for k in (keywords or [])]
        
        # Compile patterns
        for category, pattern_list in patterns.items():
            self.patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in pattern_list
            ]
    
    def check(self, text: str) -> List[PolicyViolation]:
        violations = []
        
        # Check regex patterns
        for category, compiled_patterns in self.patterns.items():
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    violations.append(PolicyViolation(
                        policy_name=self.name,
                        violation_type=category,
                        matched_content=match.group(),
                        position=(match.start(), match.end())
                    ))
        
        # Check keywords
        text_lower = text.lower()
        for keyword in self.keywords:
            start = 0
            while True:
                pos = text_lower.find(keyword, start)
                if pos == -1:
                    break
                violations.append(PolicyViolation(
                    policy_name=self.name,
                    violation_type="keyword",
                    matched_content=text[pos:pos+len(keyword)],
                    position=(pos, pos + len(keyword))
                ))
                start = pos + 1
        
        return violations


class BlockAction(Action):
    """Block content if violations found"""
    
    def __init__(self, message: str = "Content blocked due to policy violation"):
        self.message = message
    
    def apply(self, text: str, violations: List[PolicyViolation]) -> str:
        if violations:
            categories = set(v.violation_type for v in violations)
            return f"{self.message} (detected: {', '.join(categories)})"
        return text


class AnonymizeAction(Action):
    """Replace violations with anonymized versions"""
    
    def __init__(self, replacement_map: Dict[str, str] = None):
        self.replacement_map = replacement_map or {
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "ssn": "[SSN]",
            "credit_card": "[CARD]",
            "address": "[ADDRESS]",
            "name": "[NAME]",
        }
    
    def apply(self, text: str, violations: List[PolicyViolation]) -> str:
        result = text
        # Sort by position descending to replace from end
        sorted_violations = sorted(violations, key=lambda v: v.position[0], reverse=True)
        
        for v in sorted_violations:
            replacement = self.replacement_map.get(v.violation_type, "[REDACTED]")
            result = result[:v.position[0]] + replacement + result[v.position[1]:]
        
        return result


class ReplaceAction(Action):
    """Replace all violations with a single placeholder"""
    
    def __init__(self, placeholder: str = "[REDACTED]"):
        self.placeholder = placeholder
    
    def apply(self, text: str, violations: List[PolicyViolation]) -> str:
        result = text
        sorted_violations = sorted(violations, key=lambda v: v.position[0], reverse=True)
        
        for v in sorted_violations:
            result = result[:v.position[0]] + self.placeholder + result[v.position[1]:]
        
        return result


class RaiseAction(Action):
    """Raise an exception on violations"""
    
    def __init__(self, message: str = "Policy violation detected"):
        self.message = message
    
    def apply(self, text: str, violations: List[PolicyViolation]) -> str:
        if violations:
            raise DisallowedOperation(self.message, violations)
        return text


@dataclass
class Policy:
    """
    A policy combines a rule with an action.
    
    Usage:
        from local_agent_framework.safety import Policy, PIIRule, AnonymizeAction
        
        policy = Policy(
            name="PII Protection",
            description="Anonymize personal information",
            rule=PIIRule(),
            action=AnonymizeAction()
        )
    """
    name: str
    description: str
    rule: Rule
    action: Action
    enabled: bool = True
    
    def check_and_apply(self, text: str) -> tuple:
        """
        Check text against policy and apply action.
        
        Returns:
            (processed_text, violations)
        """
        if not self.enabled:
            return text, []
        
        violations = self.rule.check(text)
        processed = self.action.apply(text, violations)
        return processed, violations


# Pre-built PII Rules
class PIIRule(RegexRule):
    """
    Rule for detecting Personally Identifiable Information.
    
    Detects: emails, phones, SSN, credit cards, addresses, etc.
    """
    
    DEFAULT_PATTERNS = {
        "email": [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ],
        "phone": [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            r'\b\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b',
            r'\b\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        ],
        "ssn": [
            r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'
        ],
        "credit_card": [
            r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',
            r'\b\d{16}\b'
        ],
        "ip_address": [
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        ]
    }
    
    def __init__(self, options: Dict[str, Any] = None):
        options = options or {}
        patterns = self.DEFAULT_PATTERNS.copy()
        
        # Merge custom patterns
        if "custom_patterns" in options:
            for category, pattern_list in options["custom_patterns"].items():
                if category in patterns:
                    patterns[category].extend(pattern_list)
                else:
                    patterns[category] = pattern_list
        
        keywords = options.get("custom_keywords", [])
        
        super().__init__(patterns=patterns, keywords=keywords, name="PIIRule")


# Pre-built Policies
PIIBlockPolicy = Policy(
    name="PII Block Policy",
    description="Blocks content containing PII",
    rule=PIIRule(),
    action=BlockAction()
)

PIIAnonymizePolicy = Policy(
    name="PII Anonymize Policy", 
    description="Anonymizes PII in content",
    rule=PIIRule(),
    action=AnonymizeAction()
)

PIIReplacePolicy = Policy(
    name="PII Replace Policy",
    description="Replaces PII with [PII_REDACTED]",
    rule=PIIRule(),
    action=ReplaceAction("[PII_REDACTED]")
)

PIIRaiseExceptionPolicy = Policy(
    name="PII Exception Policy",
    description="Raises exception on PII detection",
    rule=PIIRule(),
    action=RaiseAction("PII detected in content")
)


class SafetyEngine:
    """
    Central safety engine that manages multiple policies.
    
    Usage:
        engine = SafetyEngine()
        engine.add_policy(PIIAnonymizePolicy)
        engine.add_policy(custom_policy)
        
        # Check input
        safe_input, violations = engine.check_input("My email is test@example.com")
        
        # Check output  
        safe_output, violations = engine.check_output(agent_response)
    """
    
    def __init__(self, policies: List[Policy] = None):
        self.policies = policies or []
    
    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine"""
        self.policies.append(policy)
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a policy by name"""
        for i, p in enumerate(self.policies):
            if p.name == policy_name:
                self.policies.pop(i)
                return True
        return False
    
    def check(self, text: str) -> tuple:
        """
        Run text through all policies.
        
        Returns:
            (processed_text, all_violations)
        """
        all_violations = []
        current_text = text
        
        for policy in self.policies:
            current_text, violations = policy.check_and_apply(current_text)
            all_violations.extend(violations)
        
        return current_text, all_violations
    
    def check_input(self, text: str) -> tuple:
        """Check user input against policies"""
        return self.check(text)
    
    def check_output(self, text: str) -> tuple:
        """Check agent output against policies"""
        return self.check(text)
    
    def is_safe(self, text: str) -> bool:
        """Quick check if text has any violations"""
        _, violations = self.check(text)
        return len(violations) == 0
