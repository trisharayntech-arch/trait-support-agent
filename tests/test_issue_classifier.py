from services.issue_classifier import classify_issue


def test_billing_issue():
    result = classify_issue("I was charged twice for my order")

    assert result.category == "billing_refund"
    assert result.priority == "high"
    assert result.assigned_team == "Billing & Refunds"


def test_delivery_issue():
    result = classify_issue("Where is my order? It is late")

    assert result.category == "order_delivery"
    assert result.priority == "high"
    assert result.assigned_team == "Orders & Logistics"


def test_technical_issue():
    result = classify_issue("The app is not working")

    assert result.category == "technical_support"
    assert result.priority == "medium"
    assert result.assigned_team == "Technical Support"


def test_urgent_issue():
    result = classify_issue("This is urgent, my account was hacked")

    assert result.priority == "urgent"


def test_general_issue():
    result = classify_issue("Tell me about your services")

    assert result.category == "general"
    assert result.assigned_team == "General Support"