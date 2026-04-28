"""Webhook integration for dataset events."""

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class WebhookEvent(Enum):
    """Types of webhook events."""
    
    DATASET_CREATED = "dataset.created"
    DATASET_UPDATED = "dataset.updated"
    DATASET_DELETED = "dataset.deleted"
    BUILD_STARTED = "build.started"
    BUILD_COMPLETED = "build.completed"
    BUILD_FAILED = "build.failed"
    QUALITY_CHECK_PASSED = "quality_check.passed"
    QUALITY_CHECK_FAILED = "quality_check.failed"
    COMPLIANCE_PASSED = "compliance.passed"
    COMPLIANCE_FAILED = "compliance.failed"
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"
    ALL = "*"


class WebhookStatus(Enum):
    """Status of webhook delivery."""
    
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookEndpoint:
    """A webhook endpoint configuration."""
    
    endpoint_id: str
    url: str
    events: List[WebhookEvent]
    enabled: bool = True
    secret: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "endpoint_id": self.endpoint_id,
            "url": self.url,
            "events": [e.value for e in self.events],
            "enabled": self.enabled,
            "secret": self.secret,
            "headers": self.headers,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookEndpoint":
        """Create from dictionary."""
        return cls(
            endpoint_id=data["endpoint_id"],
            url=data["url"],
            events=[WebhookEvent(e) for e in data["events"]],
            enabled=data.get("enabled", True),
            secret=data.get("secret"),
            headers=data.get("headers", {}),
            retry_count=data.get("retry_count", 3),
            timeout_seconds=data.get("timeout_seconds", 30),
        )


@dataclass
class WebhookPayload:
    """Payload sent to webhook endpoint."""
    
    event: WebhookEvent
    timestamp: str
    dataset_path: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event": self.event.value,
            "timestamp": self.timestamp,
            "dataset_path": self.dataset_path,
            "data": self.data,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    
    delivery_id: str
    endpoint_id: str
    payload: WebhookPayload
    status: WebhookStatus
    attempts: int = 0
    last_attempt: Optional[str] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "delivery_id": self.delivery_id,
            "endpoint_id": self.endpoint_id,
            "payload": self.payload.to_dict(),
            "status": self.status.value,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "error": self.error,
        }


class DatasetWebhookManager:
    """Manager for dataset webhooks."""
    
    def __init__(self):
        """Initialize the webhook manager."""
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: List[WebhookDelivery] = []
    
    def create_endpoint(
        self,
        endpoint_id: str,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 3,
        timeout_seconds: int = 30,
    ) -> WebhookEndpoint:
        """Create a webhook endpoint."""
        endpoint = WebhookEndpoint(
            endpoint_id=endpoint_id,
            url=url,
            events=events,
            secret=secret,
            headers=headers or {},
            retry_count=retry_count,
            timeout_seconds=timeout_seconds,
        )
        
        self.endpoints[endpoint_id] = endpoint
        return endpoint
    
    def enable_endpoint(self, endpoint_id: str) -> None:
        """Enable an endpoint."""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].enabled = True
    
    def disable_endpoint(self, endpoint_id: str) -> None:
        """Disable an endpoint."""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].enabled = False
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an endpoint."""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False
    
    def trigger_webhook(
        self,
        event: WebhookEvent,
        dataset_path: Path,
        data: Optional[Dict[str, Any]] = None,
    ) -> List[WebhookDelivery]:
        """Trigger webhooks for an event."""
        payload = WebhookPayload(
            event=event,
            timestamp=datetime.utcnow().isoformat() + "Z",
            dataset_path=str(dataset_path),
            data=data or {},
        )
        
        deliveries = []
        
        for endpoint in self.endpoints.values():
            if not endpoint.enabled:
                continue
            
            # Check if endpoint subscribes to this event
            if not self._endpoint_subscribes(endpoint, event):
                continue
            
            # Create and send delivery
            delivery = self._create_delivery(endpoint, payload)
            self._send_delivery(endpoint, delivery)
            deliveries.append(delivery)
        
        return deliveries
    
    def _endpoint_subscribes(
        self,
        endpoint: WebhookEndpoint,
        event: WebhookEvent,
    ) -> bool:
        """Check if endpoint subscribes to an event."""
        # Check for wildcard subscription
        if WebhookEvent.ALL in endpoint.events:
            return True
        
        # Check for specific event subscription
        return event in endpoint.events
    
    def _create_delivery(
        self,
        endpoint: WebhookEndpoint,
        payload: WebhookPayload,
    ) -> WebhookDelivery:
        """Create a webhook delivery."""
        delivery_id = f"delivery_{datetime.utcnow().timestamp()}"
        
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            endpoint_id=endpoint.endpoint_id,
            payload=payload,
            status=WebhookStatus.PENDING,
        )
        
        self.deliveries.append(delivery)
        return delivery
    
    def _send_delivery(
        self,
        endpoint: WebhookEndpoint,
        delivery: WebhookDelivery,
    ) -> None:
        """Send a webhook delivery."""
        # Simulated webhook sending
        delivery.attempts += 1
        delivery.last_attempt = datetime.utcnow().isoformat() + "Z"
        
        try:
            # In a real implementation, this would make an HTTP request
            # For now, simulate success
            delivery.status = WebhookStatus.SENT
            delivery.response_code = 200
            delivery.response_body = '{"status": "received"}'
        
        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error = str(e)
    
    def retry_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Retry a failed delivery."""
        delivery = next(
            (d for d in self.deliveries if d.delivery_id == delivery_id),
            None,
        )
        
        if not delivery:
            return None
        
        endpoint = self.endpoints.get(delivery.endpoint_id)
        if not endpoint:
            return None
        
        if delivery.attempts >= endpoint.retry_count:
            return None
        
        delivery.status = WebhookStatus.RETRYING
        self._send_delivery(endpoint, delivery)
        
        return delivery
    
    def get_deliveries(
        self,
        endpoint_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        """Get webhook deliveries with optional filtering."""
        deliveries = self.deliveries
        
        if endpoint_id:
            deliveries = [d for d in deliveries if d.endpoint_id == endpoint_id]
        
        if status:
            deliveries = [d for d in deliveries if d.status == status]
        
        # Sort by last attempt descending
        deliveries.sort(
            key=lambda d: d.last_attempt or "",
            reverse=True,
        )
        
        return deliveries[:limit]
    
    def get_endpoint_statistics(self, endpoint_id: str) -> Dict[str, Any]:
        """Get statistics for an endpoint."""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        endpoint = self.endpoints[endpoint_id]
        deliveries = [d for d in self.deliveries if d.endpoint_id == endpoint_id]
        
        total_deliveries = len(deliveries)
        sent = len([d for d in deliveries if d.status == WebhookStatus.SENT])
        failed = len([d for d in deliveries if d.status == WebhookStatus.FAILED])
        pending = len([d for d in deliveries if d.status == WebhookStatus.PENDING])
        retrying = len([d for d in deliveries if d.status == WebhookStatus.RETRYING])
        
        success_rate = sent / max(total_deliveries, 1)
        
        return {
            "endpoint_id": endpoint_id,
            "url": endpoint.url,
            "enabled": endpoint.enabled,
            "total_deliveries": total_deliveries,
            "sent": sent,
            "failed": failed,
            "pending": pending,
            "retrying": retrying,
            "success_rate": success_rate,
        }
    
    def sign_payload(self, payload: WebhookPayload, secret: str) -> str:
        """Generate HMAC signature for payload."""
        payload_json = payload.to_json()
        signature = hmac.new(
            secret.encode("utf-8"),
            payload_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def verify_signature(
        self,
        payload: WebhookPayload,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify HMAC signature for payload."""
        expected_signature = self.sign_payload(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    def test_endpoint(self, endpoint_id: str) -> WebhookDelivery:
        """Send a test webhook to an endpoint."""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        endpoint = self.endpoints[endpoint_id]
        
        # Create test payload
        test_payload = WebhookPayload(
            event=WebhookEvent.ALL,
            timestamp=datetime.utcnow().isoformat() + "Z",
            dataset_path="/test/dataset.jsonl",
            data={"test": True, "message": "This is a test webhook"},
        )
        
        # Create and send delivery
        delivery = self._create_delivery(endpoint, test_payload)
        self._send_delivery(endpoint, delivery)
        
        return delivery
    
    def get_failed_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get all failed deliveries."""
        return self.get_deliveries(status=WebhookStatus.FAILED, limit=limit)
    
    def retry_failed_deliveries(self) -> List[WebhookDelivery]:
        """Retry all failed deliveries."""
        failed = self.get_failed_deliveries()
        retried = []
        
        for delivery in failed:
            endpoint = self.endpoints.get(delivery.endpoint_id)
            if not endpoint:
                continue
            
            if delivery.attempts < endpoint.retry_count:
                result = self.retry_delivery(delivery.delivery_id)
                if result:
                    retried.append(result)
        
        return retried
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall webhook statistics."""
        total_endpoints = len(self.endpoints)
        active_endpoints = len([e for e in self.endpoints.values() if e.enabled])
        total_deliveries = len(self.deliveries)
        
        sent = len([d for d in self.deliveries if d.status == WebhookStatus.SENT])
        failed = len([d for d in self.deliveries if d.status == WebhookStatus.FAILED])
        pending = len([d for d in self.deliveries if d.status == WebhookStatus.PENDING])
        retrying = len([d for d in self.deliveries if d.status == WebhookStatus.RETRYING])
        
        success_rate = sent / max(total_deliveries, 1)
        
        deliveries_by_event = {}
        for delivery in self.deliveries:
            event = delivery.payload.event.value
            deliveries_by_event[event] = deliveries_by_event.get(event, 0) + 1
        
        return {
            "total_endpoints": total_endpoints,
            "active_endpoints": active_endpoints,
            "total_deliveries": total_deliveries,
            "sent": sent,
            "failed": failed,
            "pending": pending,
            "retrying": retrying,
            "success_rate": success_rate,
            "deliveries_by_event": deliveries_by_event,
        }
    
    def save_endpoints(self, output_path: Path) -> None:
        """Save webhook endpoints to file."""
        data = {
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints.values()],
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    
    def load_endpoints(self, input_path: Path) -> None:
        """Load webhook endpoints from file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        
        self.endpoints.clear()
        for endpoint_data in data["endpoints"]:
            endpoint = WebhookEndpoint.from_dict(endpoint_data)
            self.endpoints[endpoint.endpoint_id] = endpoint
