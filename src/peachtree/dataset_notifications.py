"""Dataset notification system for events and alerts."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


class NotificationType(Enum):
    """Types of notifications."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of dataset events."""
    
    DATASET_CREATED = "dataset_created"
    DATASET_UPDATED = "dataset_updated"
    DATASET_DELETED = "dataset_deleted"
    QUALITY_SCORE_CHANGED = "quality_score_changed"
    COMPLIANCE_CHECK_FAILED = "compliance_check_failed"
    BUILD_COMPLETED = "build_completed"
    BUILD_FAILED = "build_failed"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    CUSTOM_EVENT = "custom_event"


class NotificationChannel(Enum):
    """Channels for sending notifications."""
    
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"
    CONSOLE = "console"
    SMS = "sms"


@dataclass
class NotificationRule:
    """A rule for triggering notifications."""
    
    rule_id: str
    event_type: EventType
    notification_type: NotificationType
    channels: List[NotificationChannel]
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)
    template: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "event_type": self.event_type.value,
            "notification_type": self.notification_type.value,
            "channels": [c.value for c in self.channels],
            "enabled": self.enabled,
            "conditions": self.conditions,
            "recipients": self.recipients,
            "template": self.template,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationRule":
        """Create from dictionary."""
        return cls(
            rule_id=data["rule_id"],
            event_type=EventType(data["event_type"]),
            notification_type=NotificationType(data["notification_type"]),
            channels=[NotificationChannel(c) for c in data["channels"]],
            enabled=data.get("enabled", True),
            conditions=data.get("conditions", {}),
            recipients=data.get("recipients", []),
            template=data.get("template"),
        )


@dataclass
class DatasetEvent:
    """An event that occurred on a dataset."""
    
    event_id: str
    event_type: EventType
    dataset_path: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "dataset_path": self.dataset_path,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class Notification:
    """A notification to be sent."""
    
    notification_id: str
    notification_type: NotificationType
    event: DatasetEvent
    channels: List[NotificationChannel]
    recipients: List[str]
    subject: str
    message: str
    sent: bool = False
    sent_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type.value,
            "event": self.event.to_dict(),
            "channels": [c.value for c in self.channels],
            "recipients": self.recipients,
            "subject": self.subject,
            "message": self.message,
            "sent": self.sent,
            "sent_at": self.sent_at,
        }


class DatasetNotificationSystem:
    """System for managing dataset notifications."""
    
    def __init__(self):
        """Initialize the notification system."""
        self.rules: Dict[str, NotificationRule] = {}
        self.events: List[DatasetEvent] = []
        self.notifications: List[Notification] = []
        self.channel_handlers: Dict[NotificationChannel, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default notification handlers."""
        self.channel_handlers[NotificationChannel.LOG] = self._send_log
        self.channel_handlers[NotificationChannel.CONSOLE] = self._send_console
        self.channel_handlers[NotificationChannel.EMAIL] = self._send_email
        self.channel_handlers[NotificationChannel.SLACK] = self._send_slack
        self.channel_handlers[NotificationChannel.WEBHOOK] = self._send_webhook
        self.channel_handlers[NotificationChannel.SMS] = self._send_sms
    
    def create_rule(
        self,
        rule_id: str,
        event_type: EventType,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        recipients: Optional[List[str]] = None,
        conditions: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None,
    ) -> NotificationRule:
        """Create a notification rule."""
        rule = NotificationRule(
            rule_id=rule_id,
            event_type=event_type,
            notification_type=notification_type,
            channels=channels,
            recipients=recipients or [],
            conditions=conditions or {},
            template=template,
        )
        
        self.rules[rule_id] = rule
        return rule
    
    def enable_rule(self, rule_id: str) -> None:
        """Enable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str) -> None:
        """Disable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def emit_event(
        self,
        event_type: EventType,
        dataset_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DatasetEvent:
        """Emit an event."""
        event_id = f"event_{datetime.utcnow().timestamp()}"
        
        event = DatasetEvent(
            event_id=event_id,
            event_type=event_type,
            dataset_path=str(dataset_path),
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {},
        )
        
        self.events.append(event)
        
        # Process matching rules
        self._process_event(event)
        
        return event
    
    def _process_event(self, event: DatasetEvent) -> None:
        """Process an event and trigger matching rules."""
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if rule.event_type != event.event_type:
                continue
            
            # Check conditions
            if not self._check_conditions(event, rule.conditions):
                continue
            
            # Create and send notification
            self._create_notification(event, rule)
    
    def _check_conditions(
        self,
        event: DatasetEvent,
        conditions: Dict[str, Any],
    ) -> bool:
        """Check if event matches rule conditions."""
        if not conditions:
            return True
        
        # Check dataset path pattern
        if "dataset_path_pattern" in conditions:
            pattern = conditions["dataset_path_pattern"]
            if pattern not in event.dataset_path:
                return False
        
        # Check metadata conditions
        if "metadata" in conditions:
            for key, value in conditions["metadata"].items():
                if event.metadata.get(key) != value:
                    return False
        
        # Check threshold conditions
        if "threshold" in conditions:
            threshold = conditions["threshold"]
            metric_key = threshold.get("metric")
            operator = threshold.get("operator", ">")
            threshold_value = threshold.get("value")
            
            if metric_key and metric_key in event.metadata:
                metric_value = event.metadata[metric_key]
                
                if operator == ">" and metric_value <= threshold_value:
                    return False
                elif operator == ">=" and metric_value < threshold_value:
                    return False
                elif operator == "<" and metric_value >= threshold_value:
                    return False
                elif operator == "<=" and metric_value > threshold_value:
                    return False
                elif operator == "==" and metric_value != threshold_value:
                    return False
        
        return True
    
    def _create_notification(
        self,
        event: DatasetEvent,
        rule: NotificationRule,
    ) -> Notification:
        """Create a notification from an event and rule."""
        notification_id = f"notif_{datetime.utcnow().timestamp()}"
        
        # Format message
        if rule.template:
            message = self._format_template(rule.template, event)
        else:
            message = self._format_default_message(event)
        
        subject = f"[{rule.notification_type.value.upper()}] {event.event_type.value}"
        
        notification = Notification(
            notification_id=notification_id,
            notification_type=rule.notification_type,
            event=event,
            channels=rule.channels,
            recipients=rule.recipients,
            subject=subject,
            message=message,
        )
        
        self.notifications.append(notification)
        
        # Send notification
        self._send_notification(notification)
        
        return notification
    
    def _format_template(self, template: str, event: DatasetEvent) -> str:
        """Format a notification template."""
        # Simple template substitution
        message = template
        message = message.replace("{event_type}", event.event_type.value)
        message = message.replace("{dataset_path}", event.dataset_path)
        message = message.replace("{timestamp}", event.timestamp)
        
        # Replace metadata placeholders
        for key, value in event.metadata.items():
            message = message.replace(f"{{metadata.{key}}}", str(value))
        
        return message
    
    def _format_default_message(self, event: DatasetEvent) -> str:
        """Format a default notification message."""
        lines = [
            f"Event: {event.event_type.value}",
            f"Dataset: {event.dataset_path}",
            f"Time: {event.timestamp}",
        ]
        
        if event.metadata:
            lines.append("\nMetadata:")
            for key, value in event.metadata.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def _send_notification(self, notification: Notification) -> None:
        """Send a notification through all channels."""
        for channel in notification.channels:
            handler = self.channel_handlers.get(channel)
            if handler:
                try:
                    handler(notification)
                except Exception as e:
                    # Log error but don't fail
                    print(f"Failed to send notification via {channel.value}: {e}")
        
        notification.sent = True
        notification.sent_at = datetime.utcnow().isoformat() + "Z"
    
    def _send_log(self, notification: Notification) -> None:
        """Send notification to log."""
        # Simulated log handler
        pass
    
    def _send_console(self, notification: Notification) -> None:
        """Send notification to console."""
        # Simulated console handler
        print(f"[NOTIFICATION] {notification.subject}")
        print(notification.message)
    
    def _send_email(self, notification: Notification) -> None:
        """Send notification via email."""
        # Simulated email handler
        pass
    
    def _send_slack(self, notification: Notification) -> None:
        """Send notification to Slack."""
        # Simulated Slack handler
        pass
    
    def _send_webhook(self, notification: Notification) -> None:
        """Send notification via webhook."""
        # Simulated webhook handler
        pass
    
    def _send_sms(self, notification: Notification) -> None:
        """Send notification via SMS."""
        # Simulated SMS handler
        pass
    
    def get_events(
        self,
        event_type: Optional[EventType] = None,
        dataset_path: Optional[str] = None,
        limit: int = 100,
    ) -> List[DatasetEvent]:
        """Get events with optional filtering."""
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if dataset_path:
            events = [e for e in events if dataset_path in e.dataset_path]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_notifications(
        self,
        notification_type: Optional[NotificationType] = None,
        sent: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Notification]:
        """Get notifications with optional filtering."""
        notifications = self.notifications
        
        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]
        
        if sent is not None:
            notifications = [n for n in notifications if n.sent == sent]
        
        # Sort by event timestamp descending
        notifications.sort(key=lambda n: n.event.timestamp, reverse=True)
        
        return notifications[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics."""
        total_events = len(self.events)
        total_notifications = len(self.notifications)
        sent_notifications = len([n for n in self.notifications if n.sent])
        
        events_by_type = {}
        for event in self.events:
            event_type = event.event_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        notifications_by_type = {}
        for notification in self.notifications:
            notif_type = notification.notification_type.value
            notifications_by_type[notif_type] = notifications_by_type.get(notif_type, 0) + 1
        
        return {
            "total_events": total_events,
            "total_notifications": total_notifications,
            "sent_notifications": sent_notifications,
            "pending_notifications": total_notifications - sent_notifications,
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_rules": len(self.rules),
            "events_by_type": events_by_type,
            "notifications_by_type": notifications_by_type,
        }
    
    def save_rules(self, output_path: Path) -> None:
        """Save notification rules to file."""
        data = {
            "rules": [rule.to_dict() for rule in self.rules.values()],
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    
    def load_rules(self, input_path: Path) -> None:
        """Load notification rules from file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        
        self.rules.clear()
        for rule_data in data["rules"]:
            rule = NotificationRule.from_dict(rule_data)
            self.rules[rule.rule_id] = rule
