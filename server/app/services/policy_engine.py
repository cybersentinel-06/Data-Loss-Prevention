"""
Policy Engine Service
Loads, validates, and evaluates YAML-based DLP policies
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import re
import structlog
from datetime import datetime

logger = structlog.get_logger()


class PolicyEngine:
    """
    DLP Policy Engine

    Loads policies from YAML files and evaluates events against them.
    Supports:
    - Pattern matching (regex)
    - Field-based conditions
    - Multiple actions (alert, block, quarantine, notify)
    - Policy priorities
    - Policy groups
    """

    def __init__(self, policies_directory: str = "/etc/cybersentinel/policies"):
        self.policies_directory = Path(policies_directory)
        self.policies: List[Dict[str, Any]] = []
        self.compiled_patterns: Dict[str, re.Pattern] = {}

    def load_policies(self) -> None:
        """
        Load all policy files from the policies directory
        """
        if not self.policies_directory.exists():
            logger.warning(
                "Policies directory does not exist",
                path=str(self.policies_directory)
            )
            return

        # Find all YAML files
        policy_files = list(self.policies_directory.glob("*.yml")) + \
                      list(self.policies_directory.glob("*.yaml"))

        if not policy_files:
            logger.warning(
                "No policy files found",
                path=str(self.policies_directory)
            )
            return

        loaded_count = 0
        for policy_file in policy_files:
            try:
                with open(policy_file, 'r') as f:
                    policy_data = yaml.safe_load(f)

                if not policy_data:
                    continue

                # Validate and load policy
                if self._validate_policy(policy_data):
                    self.policies.append(policy_data)
                    self._compile_policy_patterns(policy_data)
                    loaded_count += 1

                    logger.info(
                        "Policy loaded",
                        policy_id=policy_data.get("policy", {}).get("id"),
                        policy_name=policy_data.get("policy", {}).get("name"),
                        file=policy_file.name
                    )
                else:
                    logger.error(
                        "Invalid policy file",
                        file=policy_file.name
                    )

            except Exception as e:
                logger.error(
                    "Failed to load policy",
                    file=policy_file.name,
                    error=str(e)
                )

        # Sort policies by priority (if specified)
        self.policies.sort(
            key=lambda p: p.get("policy", {}).get("priority", 100)
        )

        logger.info(
            "Policies loaded",
            total=loaded_count,
            directory=str(self.policies_directory)
        )

    def _validate_policy(self, policy_data: Dict[str, Any]) -> bool:
        """
        Validate policy structure

        Required fields:
        - policy.id
        - policy.name
        - policy.rules (list with at least one rule)
        """
        if "policy" not in policy_data:
            logger.error("Missing 'policy' key")
            return False

        policy = policy_data["policy"]

        # Check required fields
        required_fields = ["id", "name", "rules"]
        for field in required_fields:
            if field not in policy:
                logger.error(f"Missing required field: policy.{field}")
                return False

        # Check rules structure
        rules = policy.get("rules", [])
        if not isinstance(rules, list) or len(rules) == 0:
            logger.error("Policy must have at least one rule")
            return False

        # Validate each rule
        for idx, rule in enumerate(rules):
            if "id" not in rule:
                logger.error(f"Rule {idx} missing 'id'")
                return False

            if "conditions" not in rule:
                logger.error(f"Rule {rule.get('id')} missing 'conditions'")
                return False

            if "actions" not in rule:
                logger.error(f"Rule {rule.get('id')} missing 'actions'")
                return False

        return True

    def _compile_policy_patterns(self, policy_data: Dict[str, Any]) -> None:
        """
        Pre-compile regex patterns for better performance
        """
        policy = policy_data.get("policy", {})
        policy_id = policy.get("id")

        for rule in policy.get("rules", []):
            rule_id = rule.get("id")

            for condition in rule.get("conditions", []):
                if condition.get("operator") == "regex":
                    pattern = condition.get("value")
                    if pattern:
                        try:
                            compiled = re.compile(pattern)
                            key = f"{policy_id}:{rule_id}:{pattern}"
                            self.compiled_patterns[key] = compiled
                        except re.error as e:
                            logger.error(
                                "Invalid regex pattern",
                                policy_id=policy_id,
                                rule_id=rule_id,
                                pattern=pattern,
                                error=str(e)
                            )

    async def evaluate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate an event against all loaded policies

        Returns the event with policy evaluation results added
        """
        if not self.policies:
            logger.debug("No policies loaded, skipping evaluation")
            return event

        matched_policies = []

        for policy_data in self.policies:
            policy = policy_data.get("policy", {})

            # Check if policy is enabled
            if not policy.get("enabled", True):
                continue

            # Evaluate rules
            for rule in policy.get("rules", []):
                if await self._evaluate_rule(event, rule, policy):
                    # Rule matched!
                    matched_policies.append({
                        "policy_id": policy.get("id"),
                        "policy_name": policy.get("name"),
                        "rule_id": rule.get("id"),
                        "rule_name": rule.get("name"),
                        "severity": policy.get("severity", "medium"),
                        "actions": rule.get("actions", [])
                    })

                    logger.info(
                        "Policy rule matched",
                        event_id=event.get("event_id"),
                        policy=policy.get("name"),
                        rule=rule.get("name")
                    )

                    # Execute actions
                    event = await self._execute_rule_actions(event, rule, policy)

                    # If policy says stop on match, break
                    if policy.get("stop_on_match", False):
                        break

        # Add policy evaluation results to event
        if matched_policies:
            event["policy"] = matched_policies[0]  # Primary policy
            event["policies_matched"] = matched_policies
            event["policy_evaluated_at"] = datetime.utcnow().isoformat()

        return event

    async def _evaluate_rule(
        self,
        event: Dict[str, Any],
        rule: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a single rule against an event

        Returns True if all conditions match
        """
        conditions = rule.get("conditions", [])

        if not conditions:
            return False

        # All conditions must match (AND logic)
        for condition in conditions:
            if not await self._evaluate_condition(event, condition, policy):
                return False

        return True

    async def _evaluate_condition(
        self,
        event: Dict[str, Any],
        condition: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a single condition

        Supports operators:
        - equals
        - not_equals
        - contains
        - regex
        - greater_than
        - less_than
        - in
        - exists
        """
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not field or not operator:
            return False

        # Get field value from event (supports nested fields like "agent.id")
        event_value = self._get_nested_field(event, field)

        # Evaluate based on operator
        if operator == "equals":
            return event_value == value

        elif operator == "not_equals":
            return event_value != value

        elif operator == "contains":
            if isinstance(event_value, str) and isinstance(value, str):
                return value in event_value
            elif isinstance(event_value, list):
                return value in event_value
            return False

        elif operator == "regex":
            if not isinstance(event_value, str):
                return False

            # Use pre-compiled pattern if available
            policy_id = policy.get("id")
            rule_id = condition.get("rule_id", "")
            key = f"{policy_id}:{rule_id}:{value}"

            if key in self.compiled_patterns:
                pattern = self.compiled_patterns[key]
            else:
                try:
                    pattern = re.compile(value)
                except re.error:
                    return False

            return bool(pattern.search(event_value))

        elif operator == "greater_than":
            try:
                return float(event_value) > float(value)
            except (ValueError, TypeError):
                return False

        elif operator == "less_than":
            try:
                return float(event_value) < float(value)
            except (ValueError, TypeError):
                return False

        elif operator == "greater_equal":
            try:
                return float(event_value) >= float(value)
            except (ValueError, TypeError):
                return False

        elif operator == "less_equal":
            try:
                return float(event_value) <= float(value)
            except (ValueError, TypeError):
                return False

        elif operator == "in":
            if not isinstance(value, list):
                return False
            return event_value in value

        elif operator == "exists":
            return event_value is not None

        elif operator == "not_exists":
            return event_value is None

        elif operator == "luhn_check":
            # Special validator for credit card numbers
            if not isinstance(event_value, str):
                return False
            return self._luhn_check(event_value)

        else:
            logger.warning(
                "Unknown operator",
                operator=operator,
                field=field
            )
            return False

    def _get_nested_field(self, event: Dict[str, Any], field_path: str) -> Any:
        """
        Get nested field from event using dot notation

        Example: "agent.id" returns event["agent"]["id"]
        """
        parts = field_path.split(".")
        value = event

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _luhn_check(self, card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm
        """
        # Remove spaces and dashes
        card_number = card_number.replace(" ", "").replace("-", "")

        # Check if all digits
        if not card_number.isdigit():
            return False

        # Luhn algorithm
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))

        return checksum % 10 == 0

    async def _execute_rule_actions(
        self,
        event: Dict[str, Any],
        rule: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute actions specified in the rule

        Actions:
        - alert: Generate alert
        - block: Block the action
        - quarantine: Quarantine the file
        - notify: Send notifications
        - log: Log the event (always done)
        """
        actions = rule.get("actions", [])

        for action in actions:
            action_type = action.get("type")

            if action_type == "alert":
                event = await self._action_alert(event, action, policy)

            elif action_type == "block":
                event = await self._action_block(event, action, policy)

            elif action_type == "quarantine":
                event = await self._action_quarantine(event, action, policy)

            elif action_type == "notify":
                event = await self._action_notify(event, action, policy)

            elif action_type == "log":
                # Always logged anyway
                pass

            else:
                logger.warning(
                    "Unknown action type",
                    action_type=action_type,
                    rule=rule.get("id")
                )

        return event

    async def _action_alert(
        self,
        event: Dict[str, Any],
        action: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate alert for the event
        """
        severity = action.get("severity") or policy.get("severity", "medium")
        message = action.get("message", f"Policy violation: {policy.get('name')}")

        event.setdefault("alert", {})
        event["alert"] = {
            "id": f"alert-{event.get('event_id')}",
            "title": f"DLP Policy Violation: {policy.get('name')}",
            "description": message,
            "severity": severity,
            "status": "new",
            "acknowledged": False
        }

        logger.info(
            "Alert generated",
            event_id=event.get("event_id"),
            severity=severity,
            policy=policy.get("name")
        )

        return event

    async def _action_block(
        self,
        event: Dict[str, Any],
        action: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Block the action
        """
        if action.get("enabled", True):
            event["blocked"] = True
            event["block_reason"] = action.get("message", f"Blocked by policy: {policy.get('name')}")

            logger.warning(
                "Action blocked",
                event_id=event.get("event_id"),
                policy=policy.get("name")
            )

        return event

    async def _action_quarantine(
        self,
        event: Dict[str, Any],
        action: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quarantine file (if file event)
        """
        if action.get("enabled", True) and "file" in event:
            event["quarantined"] = True
            event["quarantine_path"] = action.get("destination", "/var/quarantine/cybersentinel")
            event["quarantine_reason"] = f"Quarantined by policy: {policy.get('name')}"

            logger.warning(
                "File quarantined",
                event_id=event.get("event_id"),
                file_path=event.get("file", {}).get("path"),
                policy=policy.get("name")
            )

        return event

    async def _action_notify(
        self,
        event: Dict[str, Any],
        action: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notifications (email, Slack, webhook, etc.)
        """
        channels = action.get("channels", [])

        # Add to event metadata for notification service to handle
        event.setdefault("notifications", [])
        event["notifications"].append({
            "channels": channels,
            "message": action.get("message", f"Policy violation: {policy.get('name')}"),
            "policy": policy.get("name")
        })

        logger.info(
            "Notification scheduled",
            event_id=event.get("event_id"),
            channels=channels,
            policy=policy.get("name")
        )

        return event

    def reload_policies(self) -> None:
        """
        Reload all policies from disk
        """
        logger.info("Reloading policies")
        self.policies = []
        self.compiled_patterns = {}
        self.load_policies()

    def get_policy_by_id(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get policy by ID
        """
        for policy_data in self.policies:
            if policy_data.get("policy", {}).get("id") == policy_id:
                return policy_data
        return None

    def get_all_policies(self) -> List[Dict[str, Any]]:
        """
        Get all loaded policies
        """
        return [p.get("policy") for p in self.policies]


# Singleton instance
_policy_engine = None


def get_policy_engine() -> PolicyEngine:
    """
    Get singleton instance of PolicyEngine
    """
    global _policy_engine

    if _policy_engine is None:
        _policy_engine = PolicyEngine()
        _policy_engine.load_policies()

    return _policy_engine
