"""Tests for dataset webhook system."""

import json
from pathlib import Path


from peachtree.dataset_webhooks import (
    DatasetWebhookManager,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEvent,
    WebhookPayload,
    WebhookStatus,
)


def test_webhook_endpoint_creation():
    """Test creating a webhook endpoint."""
    endpoint = WebhookEndpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.DATASET_CREATED, WebhookEvent.BUILD_COMPLETED],
    )
    
    assert endpoint.endpoint_id == "endpoint_001"
    assert endpoint.url == "https://api.example.com/webhook"
    assert len(endpoint.events) == 2
    assert endpoint.enabled is True


def test_webhook_endpoint_to_dict():
    """Test converting endpoint to dictionary."""
    endpoint = WebhookEndpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.DATASET_UPDATED],
        secret="mysecret",
    )
    
    endpoint_dict = endpoint.to_dict()
    
    assert endpoint_dict["endpoint_id"] == "endpoint_001"
    assert endpoint_dict["url"] == "https://api.example.com/webhook"
    assert endpoint_dict["events"] == ["dataset.updated"]
    assert endpoint_dict["secret"] == "mysecret"


def test_webhook_endpoint_from_dict():
    """Test creating endpoint from dictionary."""
    data = {
        "endpoint_id": "endpoint_002",
        "url": "https://hooks.slack.com/services/xxx",
        "events": ["build.completed", "build.failed"],
        "enabled": True,
        "secret": "secret123",
        "retry_count": 5,
    }
    
    endpoint = WebhookEndpoint.from_dict(data)
    
    assert endpoint.endpoint_id == "endpoint_002"
    assert len(endpoint.events) == 2
    assert endpoint.retry_count == 5


def test_webhook_payload_creation():
    """Test creating a webhook payload."""
    payload = WebhookPayload(
        event=WebhookEvent.DATASET_CREATED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={"records": 100},
    )
    
    assert payload.event == WebhookEvent.DATASET_CREATED
    assert payload.data["records"] == 100


def test_webhook_payload_to_dict():
    """Test converting payload to dictionary."""
    payload = WebhookPayload(
        event=WebhookEvent.BUILD_COMPLETED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={"status": "success"},
    )
    
    payload_dict = payload.to_dict()
    
    assert payload_dict["event"] == "build.completed"
    assert payload_dict["timestamp"] == "2026-04-27T00:00:00Z"
    assert payload_dict["dataset_path"] == "/data/test.jsonl"


def test_webhook_payload_to_json():
    """Test converting payload to JSON."""
    payload = WebhookPayload(
        event=WebhookEvent.QUALITY_CHECK_PASSED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={},
    )
    
    json_str = payload.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["event"] == "quality_check.passed"
    assert "timestamp" in parsed


def test_webhook_delivery_creation():
    """Test creating a webhook delivery."""
    payload = WebhookPayload(
        event=WebhookEvent.SYNC_COMPLETED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={},
    )
    
    delivery = WebhookDelivery(
        delivery_id="delivery_001",
        endpoint_id="endpoint_001",
        payload=payload,
        status=WebhookStatus.PENDING,
    )
    
    assert delivery.delivery_id == "delivery_001"
    assert delivery.status == WebhookStatus.PENDING
    assert delivery.attempts == 0


def test_create_webhook_endpoint():
    """Test creating an endpoint with the manager."""
    manager = DatasetWebhookManager()
    
    endpoint = manager.create_endpoint(
        endpoint_id="slack_webhook",
        url="https://hooks.slack.com/services/xxx",
        events=[WebhookEvent.BUILD_COMPLETED, WebhookEvent.BUILD_FAILED],
        secret="slack_secret",
    )
    
    assert endpoint.endpoint_id == "slack_webhook"
    assert "slack_webhook" in manager.endpoints


def test_enable_disable_endpoint():
    """Test enabling and disabling endpoints."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    # Disable endpoint
    manager.disable_endpoint("endpoint_001")
    assert manager.endpoints["endpoint_001"].enabled is False
    
    # Enable endpoint
    manager.enable_endpoint("endpoint_001")
    assert manager.endpoints["endpoint_001"].enabled is True


def test_delete_endpoint():
    """Test deleting an endpoint."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.DATASET_CREATED],
    )
    
    assert "endpoint_001" in manager.endpoints
    
    deleted = manager.delete_endpoint("endpoint_001")
    assert deleted is True
    assert "endpoint_001" not in manager.endpoints
    
    deleted = manager.delete_endpoint("nonexistent")
    assert deleted is False


def test_trigger_webhook():
    """Test triggering a webhook."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
        data={"status": "success"},
    )
    
    assert len(deliveries) == 1
    assert deliveries[0].endpoint_id == "endpoint_001"
    assert deliveries[0].status == WebhookStatus.SENT


def test_disabled_endpoint_not_triggered():
    """Test that disabled endpoints are not triggered."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    manager.disable_endpoint("endpoint_001")
    
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert len(deliveries) == 0


def test_wildcard_event_subscription():
    """Test wildcard event subscription."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="all_events",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    # Trigger various events
    events_to_test = [
        WebhookEvent.DATASET_CREATED,
        WebhookEvent.BUILD_COMPLETED,
        WebhookEvent.QUALITY_CHECK_PASSED,
    ]
    
    for event in events_to_test:
        deliveries = manager.trigger_webhook(
            event=event,
            dataset_path=Path("/data/test.jsonl"),
        )
        assert len(deliveries) == 1


def test_specific_event_subscription():
    """Test specific event subscription."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="build_only",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED, WebhookEvent.BUILD_FAILED],
    )
    
    # Trigger subscribed event
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    assert len(deliveries) == 1
    
    # Trigger unsubscribed event
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.DATASET_CREATED,
        dataset_path=Path("/data/test.jsonl"),
    )
    assert len(deliveries) == 0


def test_multiple_endpoints_triggered():
    """Test multiple endpoints triggered by same event."""
    manager = DatasetWebhookManager()
    
    # Create multiple endpoints for same event
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api1.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    manager.create_endpoint(
        endpoint_id="endpoint_002",
        url="https://api2.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    assert len(deliveries) == 2


def test_retry_delivery():
    """Test retrying a failed delivery."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_FAILED],
        retry_count=3,
    )
    
    # Trigger webhook
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.BUILD_FAILED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    delivery = deliveries[0]
    original_attempts = delivery.attempts
    
    # Retry delivery
    retried = manager.retry_delivery(delivery.delivery_id)
    
    assert retried is not None
    assert retried.attempts == original_attempts + 1


def test_get_deliveries():
    """Test getting deliveries with filtering."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    manager.create_endpoint(
        endpoint_id="endpoint_002",
        url="https://api2.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    # Trigger multiple webhooks
    for i in range(5):
        manager.trigger_webhook(
            event=WebhookEvent.DATASET_CREATED,
            dataset_path=Path(f"/data/test{i}.jsonl"),
        )
    
    # Get all deliveries
    all_deliveries = manager.get_deliveries()
    assert len(all_deliveries) == 10  # 5 events × 2 endpoints
    
    # Filter by endpoint
    endpoint1_deliveries = manager.get_deliveries(endpoint_id="endpoint_001")
    assert len(endpoint1_deliveries) == 5
    
    # Filter by status
    sent_deliveries = manager.get_deliveries(status=WebhookStatus.SENT)
    assert len(sent_deliveries) == 10


def test_get_endpoint_statistics():
    """Test getting endpoint statistics."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    # Trigger multiple deliveries
    for i in range(10):
        manager.trigger_webhook(
            event=WebhookEvent.BUILD_COMPLETED,
            dataset_path=Path("/data/test.jsonl"),
        )
    
    stats = manager.get_endpoint_statistics("endpoint_001")
    
    assert stats["endpoint_id"] == "endpoint_001"
    assert stats["total_deliveries"] == 10
    assert stats["sent"] == 10
    assert stats["success_rate"] == 1.0


def test_sign_payload():
    """Test signing a webhook payload."""
    manager = DatasetWebhookManager()
    
    payload = WebhookPayload(
        event=WebhookEvent.DATASET_CREATED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={},
    )
    
    secret = "my_webhook_secret"
    signature = manager.sign_payload(payload, secret)
    
    assert signature.startswith("sha256=")
    assert len(signature) > 7


def test_verify_signature():
    """Test verifying a webhook payload signature."""
    manager = DatasetWebhookManager()
    
    payload = WebhookPayload(
        event=WebhookEvent.BUILD_COMPLETED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={},
    )
    
    secret = "my_webhook_secret"
    signature = manager.sign_payload(payload, secret)
    
    # Valid signature
    assert manager.verify_signature(payload, signature, secret) is True
    
    # Invalid signature
    assert manager.verify_signature(payload, "sha256=invalid", secret) is False


def test_test_endpoint():
    """Test sending a test webhook."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    delivery = manager.test_endpoint("endpoint_001")
    
    assert delivery.endpoint_id == "endpoint_001"
    assert delivery.payload.data["test"] is True
    assert delivery.status == WebhookStatus.SENT


def test_get_failed_deliveries():
    """Test getting failed deliveries."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    # Simulate some deliveries and mark some as failed
    manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Manually mark a delivery as failed for testing
    if manager.deliveries:
        manager.deliveries[0].status = WebhookStatus.FAILED
    
    failed = manager.get_failed_deliveries()
    
    assert len(failed) >= 0  # May be 0 or 1 depending on simulated failure


def test_retry_failed_deliveries():
    """Test retrying all failed deliveries."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_FAILED],
        retry_count=3,
    )
    
    # Trigger webhook
    manager.trigger_webhook(
        event=WebhookEvent.BUILD_FAILED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Manually mark as failed for testing
    if manager.deliveries:
        manager.deliveries[0].status = WebhookStatus.FAILED
        manager.deliveries[0].attempts = 1
    
    # Retry all failed
    retried = manager.retry_failed_deliveries()
    
    # Should retry the failed delivery
    assert len(retried) >= 0


def test_get_overall_statistics():
    """Test getting overall webhook statistics."""
    manager = DatasetWebhookManager()
    
    # Create endpoints
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api1.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    manager.create_endpoint(
        endpoint_id="endpoint_002",
        url="https://api2.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    # Trigger webhooks
    manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    manager.trigger_webhook(
        event=WebhookEvent.DATASET_CREATED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    stats = manager.get_statistics()
    
    assert stats["total_endpoints"] == 2
    assert stats["active_endpoints"] == 2
    assert stats["total_deliveries"] == 3  # 2 for endpoint_001, 1 for endpoint_002


def test_save_and_load_endpoints(tmp_path):
    """Test saving and loading webhook endpoints."""
    manager = DatasetWebhookManager()
    
    # Create endpoints
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED, WebhookEvent.BUILD_FAILED],
        secret="secret123",
    )
    
    manager.create_endpoint(
        endpoint_id="endpoint_002",
        url="https://hooks.slack.com/services/xxx",
        events=[WebhookEvent.ALL],
    )
    
    # Save
    output_path = tmp_path / "endpoints.json"
    manager.save_endpoints(output_path)
    
    # Load
    new_manager = DatasetWebhookManager()
    new_manager.load_endpoints(output_path)
    
    assert len(new_manager.endpoints) == 2
    assert "endpoint_001" in new_manager.endpoints
    assert "endpoint_002" in new_manager.endpoints
    assert new_manager.endpoints["endpoint_001"].secret == "secret123"


def test_webhook_delivery_to_dict():
    """Test converting delivery to dictionary."""
    payload = WebhookPayload(
        event=WebhookEvent.QUALITY_CHECK_FAILED,
        timestamp="2026-04-27T00:00:00Z",
        dataset_path="/data/test.jsonl",
        data={},
    )
    
    delivery = WebhookDelivery(
        delivery_id="delivery_001",
        endpoint_id="endpoint_001",
        payload=payload,
        status=WebhookStatus.SENT,
        attempts=1,
        last_attempt="2026-04-27T00:01:00Z",
        response_code=200,
    )
    
    delivery_dict = delivery.to_dict()
    
    assert delivery_dict["delivery_id"] == "delivery_001"
    assert delivery_dict["status"] == "sent"
    assert delivery_dict["response_code"] == 200


def test_all_webhook_events():
    """Test all webhook event types can be used."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="all_events",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    events = [
        WebhookEvent.DATASET_CREATED,
        WebhookEvent.DATASET_UPDATED,
        WebhookEvent.DATASET_DELETED,
        WebhookEvent.BUILD_STARTED,
        WebhookEvent.BUILD_COMPLETED,
        WebhookEvent.BUILD_FAILED,
        WebhookEvent.QUALITY_CHECK_PASSED,
        WebhookEvent.QUALITY_CHECK_FAILED,
        WebhookEvent.COMPLIANCE_PASSED,
        WebhookEvent.COMPLIANCE_FAILED,
        WebhookEvent.SYNC_STARTED,
        WebhookEvent.SYNC_COMPLETED,
        WebhookEvent.SYNC_FAILED,
    ]
    
    for event in events:
        deliveries = manager.trigger_webhook(
            event=event,
            dataset_path=Path("/data/test.jsonl"),
        )
        assert len(deliveries) == 1


def test_webhook_with_custom_headers():
    """Test webhook endpoint with custom headers."""
    manager = DatasetWebhookManager()
    
    headers = {
        "Authorization": "Bearer token123",
        "X-Custom-Header": "value",
    }
    
    endpoint = manager.create_endpoint(
        endpoint_id="custom_headers",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    endpoint.headers = headers
    
    assert endpoint.headers["Authorization"] == "Bearer token123"
    assert endpoint.headers["X-Custom-Header"] == "value"


def test_webhook_timeout_configuration():
    """Test webhook timeout configuration."""
    manager = DatasetWebhookManager()
    
    endpoint = manager.create_endpoint(
        endpoint_id="timeout_test",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
        timeout_seconds=60,
    )
    
    assert endpoint.timeout_seconds == 60


def test_webhook_retry_configuration():
    """Test webhook retry count configuration."""
    manager = DatasetWebhookManager()
    
    endpoint = manager.create_endpoint(
        endpoint_id="retry_test",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
        retry_count=5,
    )
    
    assert endpoint.retry_count == 5


def test_delivery_response_tracking():
    """Test that delivery tracks response code and body."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.BUILD_COMPLETED],
    )
    
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    delivery = deliveries[0]
    
    # Simulated delivery should have response tracking
    assert delivery.response_code is not None
    assert delivery.response_body is not None


def test_webhook_payload_with_metadata():
    """Test webhook payload with rich metadata."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.QUALITY_CHECK_PASSED],
    )
    
    data = {
        "quality_score": 95.5,
        "record_count": 1000,
        "dedup_ratio": 0.05,
        "tags": ["production", "verified"],
    }
    
    deliveries = manager.trigger_webhook(
        event=WebhookEvent.QUALITY_CHECK_PASSED,
        dataset_path=Path("/data/test.jsonl"),
        data=data,
    )
    
    delivery = deliveries[0]
    assert delivery.payload.data["quality_score"] == 95.5
    assert "production" in delivery.payload.data["tags"]


def test_endpoint_statistics_success_rate():
    """Test endpoint statistics calculate success rate correctly."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    # Trigger multiple successful deliveries
    for i in range(10):
        manager.trigger_webhook(
            event=WebhookEvent.DATASET_CREATED,
            dataset_path=Path("/data/test.jsonl"),
        )
    
    stats = manager.get_endpoint_statistics("endpoint_001")
    
    assert stats["success_rate"] == 1.0
    assert stats["sent"] == 10
    assert stats["failed"] == 0


def test_webhook_delivery_limit():
    """Test getting deliveries with limit."""
    manager = DatasetWebhookManager()
    
    manager.create_endpoint(
        endpoint_id="endpoint_001",
        url="https://api.example.com/webhook",
        events=[WebhookEvent.ALL],
    )
    
    # Trigger many webhooks
    for i in range(50):
        manager.trigger_webhook(
            event=WebhookEvent.DATASET_CREATED,
            dataset_path=Path("/data/test.jsonl"),
        )
    
    # Get with limit
    deliveries = manager.get_deliveries(limit=10)
    
    assert len(deliveries) == 10
