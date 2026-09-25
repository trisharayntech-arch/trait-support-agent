"""
Rule-based issue classifier for the TRAIT AI Customer Support Agent.

Classifies customer messages into a support category, priority,
and responsible support team.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IssueClassification:
    category: str
    priority: str
    assigned_team: str


CATEGORY_RULES = {
    "billing_refund": {
        "keywords": [
            "refund",
            "refunds",
            "charged twice",
            "double charged",
            "payment failed",
            "payment issue",
            "billing",
            "invoice",
            "money deducted",
            "money debited",
            "transaction",
        ],
        "team": "Billing & Refunds",
    },
    "order_delivery": {
        "keywords": [
            "order",
            "delivery",
            "delivered",
            "shipping",
            "shipment",
            "where is my order",
            "late delivery",
            "order status",
            "tracking",
            "package",
        ],
        "team": "Orders & Logistics",
    },
    "technical_support": {
        "keywords": [
            "not working",
            "error",
            "bug",
            "crash",
            "broken",
            "login",
            "password",
            "app issue",
            "technical",
            "website issue",
        ],
        "team": "Technical Support",
    },
    "account": {
        "keywords": [
            "account",
            "profile",
            "sign up",
            "signup",
            "register",
            "registration",
            "change email",
            "change phone",
        ],
        "team": "Account Support",
    },
    "complaint": {
        "keywords": [
            "complaint",
            "complain",
            "unhappy",
            "disappointed",
            "bad service",
            "poor service",
            "terrible service",
        ],
        "team": "Customer Relations",
    },
}


URGENT_KEYWORDS = [
    "urgent",
    "emergency",
    "immediately",
    "asap",
    "fraud",
    "stolen",
    "unauthorized",
    "security breach",
]


HIGH_PRIORITY_KEYWORDS = [
    "charged twice",
    "money deducted",
    "account hacked",
    "cannot access",
    "can't access",
    "not received",
    "very late",
    "late delivery",
    "delivery is late",
    "order is late",
    "order delayed",
    "delayed delivery",
    "complaint",
]


def classify_issue(message: str) -> IssueClassification:
    """
    Classify a customer support message.

    The classifier is deterministic so it can be tested
    without requiring an external LLM/API call.
    """
    text = message.lower().strip()

    if not text:
        return IssueClassification(
            category="general",
            priority="low",
            assigned_team="General Support",
        )

    matched_category = "general"
    assigned_team = "General Support"
    best_match_count = 0

    for category, rule in CATEGORY_RULES.items():
        match_count = sum(
            1 for keyword in rule["keywords"] if keyword in text
        )

        if match_count > best_match_count:
            best_match_count = match_count
            matched_category = category
            assigned_team = rule["team"]

    if any(keyword in text for keyword in URGENT_KEYWORDS):
        priority = "urgent"

    elif (
        any(keyword in text for keyword in HIGH_PRIORITY_KEYWORDS)
        or (
            matched_category == "order_delivery"
            and any(
                keyword in text
                for keyword in ["late", "delayed", "not arrived", "missing"]
            )
        )
    ):
        priority = "high"

    elif matched_category == "general":
        priority = "low"

    else:
        priority = "medium"

    return IssueClassification(
        category=matched_category,
        priority=priority,
        assigned_team=assigned_team,
    )