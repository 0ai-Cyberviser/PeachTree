"""Tests for dataset notification system."""

from pathlib import Path


from peachtree.dataset_notifications import (
    DatasetEvent,
    DatasetNotificationSystem,
    EventType,
    Notification,
    NotificationChannel,
    NotificationRule,
    NotificationType,
)


def test_notification_rule_creation():
    """Test creating a notification rule."""
    rule = NotificationRule(
        rule_id="rule_001",
        event_type=EventType.DATASET_CREATED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
        recipients=["user@example.com"],
    )
    
    assert rule.rule_id == "rule_001"
    assert rule.event_type == EventType.DATASET_CREATED
    assert rule.notification_type == NotificationType.INFO
    assert len(rule.channels) == 2
    assert rule.enabled is True


def test_notification_rule_to_dict():
    """Test converting rule to dictionary."""
    rule = NotificationRule(
        rule_id="rule_001",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.LOG],
    )
    
    rule_dict = rule.to_dict()
    
    assert rule_dict["rule_id"] == "rule_001"
    assert rule_dict["event_type"] == "build_completed"
    assert rule_dict["notification_type"] == "success"
    assert rule_dict["channels"] == ["log"]


def test_notification_rule_from_dict():
    """Test creating rule from dictionary."""
    data = {
        "rule_id": "rule_002",
        "event_type": "quality_score_changed",
        "notification_type": "warning",
        "channels": ["email", "console"],
        "enabled": True,
        "recipients": ["admin@example.com"],
    }
    
    rule = NotificationRule.from_dict(data)
    
    assert rule.rule_id == "rule_002"
    assert rule.event_type == EventType.QUALITY_SCORE_CHANGED
    assert len(rule.channels) == 2
    assert rule.recipients == ["admin@example.com"]


def test_dataset_event_creation():
    """Test creating a dataset event."""
    event = DatasetEvent(
        event_id="event_001",
        event_type=EventType.DATASET_UPDATED,
        dataset_path="/data/test.jsonl",
        timestamp="2026-04-27T00:00:00Z",
        metadata={"records": 100},
    )
    
    assert event.event_id == "event_001"
    assert event.event_type == EventType.DATASET_UPDATED
    assert event.metadata["records"] == 100


def test_dataset_event_to_dict():
    """Test converting event to dictionary."""
    event = DatasetEvent(
        event_id="event_001",
        event_type=EventType.SYNC_COMPLETED,
        dataset_path="/data/test.jsonl",
        timestamp="2026-04-27T00:00:00Z",
    )
    
    event_dict = event.to_dict()
    
    assert event_dict["event_id"] == "event_001"
    assert event_dict["event_type"] == "sync_completed"
    assert event_dict["dataset_path"] == "/data/test.jsonl"


def test_notification_creation():
    """Test creating a notification."""
    event = DatasetEvent(
        event_id="event_001",
        event_type=EventType.BUILD_FAILED,
        dataset_path="/data/test.jsonl",
        timestamp="2026-04-27T00:00:00Z",
    )
    
    notification = Notification(
        notification_id="notif_001",
        notification_type=NotificationType.ERROR,
        event=event,
        channels=[NotificationChannel.EMAIL],
        recipients=["dev@example.com"],
        subject="Build Failed",
        message="Dataset build failed",
    )
    
    assert notification.notification_id == "notif_001"
    assert notification.notification_type == NotificationType.ERROR
    assert notification.sent is False


def test_create_notification_rule():
    """Test creating a rule with the notification system."""
    notifier = DatasetNotificationSystem()
    
    rule = notifier.create_rule(
        rule_id="build_alert",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.SLACK],
        recipients=["team@example.com"],
    )
    
    assert rule.rule_id == "build_alert"
    assert "build_alert" in notifier.rules


def test_enable_disable_rule():
    """Test enabling and disabling rules."""
    notifier = DatasetNotificationSystem()
    
    notifier.create_rule(
        rule_id="rule_001",
        event_type=EventType.DATASET_CREATED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
    )
    
    # Disable rule
    notifier.disable_rule("rule_001")
    assert notifier.rules["rule_001"].enabled is False
    
    # Enable rule
    notifier.enable_rule("rule_001")
    assert notifier.rules["rule_001"].enabled is True


def test_delete_rule():
    """Test deleting a rule."""
    notifier = DatasetNotificationSystem()
    
    notifier.create_rule(
        rule_id="rule_001",
        event_type=EventType.DATASET_DELETED,
        notification_type=NotificationType.WARNING,
        channels=[NotificationChannel.EMAIL],
    )
    
    assert "rule_001" in notifier.rules
    
    deleted = notifier.delete_rule("rule_001")
    assert deleted is True
    assert "rule_001" not in notifier.rules
    
    deleted = notifier.delete_rule("nonexistent")
    assert deleted is False


def test_emit_event():
    """Test emitting an event."""
    notifier = DatasetNotificationSystem()
    
    event = notifier.emit_event(
        event_type=EventType.DATASET_CREATED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"records": 100},
    )
    
    assert event.event_type == EventType.DATASET_CREATED
    assert event.dataset_path == "/data/test.jsonl"
    assert event in notifier.events


def test_event_triggers_matching_rule():
    """Test that an event triggers matching rules."""
    notifier = DatasetNotificationSystem()
    
    # Create rule
    notifier.create_rule(
        rule_id="quality_alert",
        event_type=EventType.QUALITY_SCORE_CHANGED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
    )
    
    # Emit matching event
    event = notifier.emit_event(
        event_type=EventType.QUALITY_SCORE_CHANGED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"score": 85.5},
    )
    
    # Should have created a notification
    assert len(notifier.notifications) == 1
    assert notifier.notifications[0].event.event_id == event.event_id


def test_disabled_rule_not_triggered():
    """Test that disabled rules are not triggered."""
    notifier = DatasetNotificationSystem()
    
    # Create and disable rule
    notifier.create_rule(
        rule_id="disabled_rule",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.LOG],
    )
    notifier.disable_rule("disabled_rule")
    
    # Emit matching event
    notifier.emit_event(
        event_type=EventType.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Should not have created a notification
    assert len(notifier.notifications) == 0


def test_condition_dataset_path_pattern():
    """Test conditions with dataset path pattern."""
    notifier = DatasetNotificationSystem()
    
    # Create rule with path condition
    notifier.create_rule(
        rule_id="prod_only",
        event_type=EventType.DATASET_UPDATED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
        conditions={"dataset_path_pattern": "/prod/"},
    )
    
    # Emit event with matching path
    notifier.emit_event(
        event_type=EventType.DATASET_UPDATED,
        dataset_path=Path("/prod/dataset.jsonl"),
    )
    
    assert len(notifier.notifications) == 1
    
    # Emit event with non-matching path
    notifier.emit_event(
        event_type=EventType.DATASET_UPDATED,
        dataset_path=Path("/dev/dataset.jsonl"),
    )
    
    # Still only 1 notification
    assert len(notifier.notifications) == 1


def test_condition_metadata():
    """Test conditions with metadata matching."""
    notifier = DatasetNotificationSystem()
    
    # Create rule with metadata condition
    notifier.create_rule(
        rule_id="high_quality",
        event_type=EventType.QUALITY_SCORE_CHANGED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.LOG],
        conditions={"metadata": {"status": "excellent"}},
    )
    
    # Emit event with matching metadata
    notifier.emit_event(
        event_type=EventType.QUALITY_SCORE_CHANGED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"status": "excellent"},
    )
    
    assert len(notifier.notifications) == 1
    
    # Emit event with non-matching metadata
    notifier.emit_event(
        event_type=EventType.QUALITY_SCORE_CHANGED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"status": "good"},
    )
    
    # Still only 1 notification
    assert len(notifier.notifications) == 1


def test_condition_threshold():
    """Test conditions with threshold values."""
    notifier = DatasetNotificationSystem()
    
    # Create rule with threshold condition
    notifier.create_rule(
        rule_id="low_quality_alert",
        event_type=EventType.QUALITY_SCORE_CHANGED,
        notification_type=NotificationType.WARNING,
        channels=[NotificationChannel.EMAIL],
        conditions={
            "threshold": {
                "metric": "quality_score",
                "operator": "<",
                "value": 70.0,
            }
        },
    )
    
    # Emit event below threshold (should trigger)
    notifier.emit_event(
        event_type=EventType.QUALITY_SCORE_CHANGED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"quality_score": 65.0},
    )
    
    assert len(notifier.notifications) == 1
    
    # Emit event above threshold (should not trigger)
    notifier.emit_event(
        event_type=EventType.QUALITY_SCORE_CHANGED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"quality_score": 85.0},
    )
    
    # Still only 1 notification
    assert len(notifier.notifications) == 1


def test_custom_template():
    """Test notification with custom message template."""
    notifier = DatasetNotificationSystem()
    
    template = "Dataset {dataset_path} event: {event_type} at {timestamp}"
    
    notifier.create_rule(
        rule_id="custom_msg",
        event_type=EventType.DATASET_CREATED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
        template=template,
    )
    
    notifier.emit_event(
        event_type=EventType.DATASET_CREATED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    notification = notifier.notifications[0]
    assert "/data/test.jsonl" in notification.message
    assert "dataset_created" in notification.message


def test_notification_with_multiple_channels():
    """Test notification sent to multiple channels."""
    notifier = DatasetNotificationSystem()
    
    notifier.create_rule(
        rule_id="multi_channel",
        event_type=EventType.BUILD_FAILED,
        notification_type=NotificationType.CRITICAL,
        channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.SMS,
        ],
        recipients=["team@example.com"],
    )
    
    notifier.emit_event(
        event_type=EventType.BUILD_FAILED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    notification = notifier.notifications[0]
    assert len(notification.channels) == 3
    assert notification.sent is True


def test_get_events():
    """Test getting events with filtering."""
    notifier = DatasetNotificationSystem()
    
    # Emit multiple events
    for i in range(5):
        notifier.emit_event(
            event_type=EventType.DATASET_UPDATED,
            dataset_path=Path(f"/data/test{i}.jsonl"),
        )
    
    for i in range(3):
        notifier.emit_event(
            event_type=EventType.QUALITY_SCORE_CHANGED,
            dataset_path=Path(f"/data/test{i}.jsonl"),
        )
    
    # Get all events
    all_events = notifier.get_events()
    assert len(all_events) == 8
    
    # Filter by event type
    updated_events = notifier.get_events(event_type=EventType.DATASET_UPDATED)
    assert len(updated_events) == 5
    
    # Filter by dataset path
    test0_events = notifier.get_events(dataset_path="test0")
    assert len(test0_events) == 2


def test_get_events_with_limit():
    """Test getting events with limit."""
    notifier = DatasetNotificationSystem()
    
    # Emit many events
    for i in range(20):
        notifier.emit_event(
            event_type=EventType.DATASET_CREATED,
            dataset_path=Path(f"/data/test{i}.jsonl"),
        )
    
    # Get with limit
    events = notifier.get_events(limit=5)
    assert len(events) == 5


def test_get_notifications():
    """Test getting notifications with filtering."""
    notifier = DatasetNotificationSystem()
    
    # Create rules for different types
    notifier.create_rule(
        rule_id="info_rule",
        event_type=EventType.DATASET_CREATED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
    )
    
    notifier.create_rule(
        rule_id="warning_rule",
        event_type=EventType.QUALITY_SCORE_CHANGED,
        notification_type=NotificationType.WARNING,
        channels=[NotificationChannel.EMAIL],
    )
    
    # Emit events
    for i in range(3):
        notifier.emit_event(
            event_type=EventType.DATASET_CREATED,
            dataset_path=Path(f"/data/test{i}.jsonl"),
        )
    
    for i in range(2):
        notifier.emit_event(
            event_type=EventType.QUALITY_SCORE_CHANGED,
            dataset_path=Path(f"/data/test{i}.jsonl"),
        )
    
    # Get all notifications
    all_notifications = notifier.get_notifications()
    assert len(all_notifications) == 5
    
    # Filter by type
    info_notifications = notifier.get_notifications(
        notification_type=NotificationType.INFO
    )
    assert len(info_notifications) == 3


def test_get_statistics():
    """Test getting notification system statistics."""
    notifier = DatasetNotificationSystem()
    
    # Create rules
    notifier.create_rule(
        rule_id="rule1",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.LOG],
    )
    
    notifier.create_rule(
        rule_id="rule2",
        event_type=EventType.BUILD_FAILED,
        notification_type=NotificationType.ERROR,
        channels=[NotificationChannel.EMAIL],
    )
    
    # Emit events
    for i in range(5):
        notifier.emit_event(
            event_type=EventType.BUILD_COMPLETED,
            dataset_path=Path("/data/test.jsonl"),
        )
    
    for i in range(2):
        notifier.emit_event(
            event_type=EventType.BUILD_FAILED,
            dataset_path=Path("/data/test.jsonl"),
        )
    
    stats = notifier.get_statistics()
    
    assert stats["total_events"] == 7
    assert stats["total_notifications"] == 7
    assert stats["sent_notifications"] == 7
    assert stats["active_rules"] == 2
    assert stats["total_rules"] == 2


def test_save_and_load_rules(tmp_path):
    """Test saving and loading notification rules."""
    notifier = DatasetNotificationSystem()
    
    # Create rules
    notifier.create_rule(
        rule_id="rule1",
        event_type=EventType.DATASET_CREATED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
        recipients=["user@example.com"],
    )
    
    notifier.create_rule(
        rule_id="rule2",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.SLACK],
    )
    
    # Save
    output_path = tmp_path / "rules.json"
    notifier.save_rules(output_path)
    
    # Load
    new_notifier = DatasetNotificationSystem()
    new_notifier.load_rules(output_path)
    
    assert len(new_notifier.rules) == 2
    assert "rule1" in new_notifier.rules
    assert "rule2" in new_notifier.rules
    assert new_notifier.rules["rule1"].event_type == EventType.DATASET_CREATED


def test_notification_to_dict():
    """Test converting notification to dictionary."""
    event = DatasetEvent(
        event_id="event_001",
        event_type=EventType.SYNC_COMPLETED,
        dataset_path="/data/test.jsonl",
        timestamp="2026-04-27T00:00:00Z",
    )
    
    notification = Notification(
        notification_id="notif_001",
        notification_type=NotificationType.SUCCESS,
        event=event,
        channels=[NotificationChannel.EMAIL],
        recipients=["user@example.com"],
        subject="Sync Complete",
        message="Dataset sync completed successfully",
        sent=True,
        sent_at="2026-04-27T00:01:00Z",
    )
    
    notif_dict = notification.to_dict()
    
    assert notif_dict["notification_id"] == "notif_001"
    assert notif_dict["notification_type"] == "success"
    assert notif_dict["sent"] is True
    assert notif_dict["subject"] == "Sync Complete"


def test_all_event_types():
    """Test all event types can be used."""
    notifier = DatasetNotificationSystem()
    
    event_types = [
        EventType.DATASET_CREATED,
        EventType.DATASET_UPDATED,
        EventType.DATASET_DELETED,
        EventType.QUALITY_SCORE_CHANGED,
        EventType.COMPLIANCE_CHECK_FAILED,
        EventType.BUILD_COMPLETED,
        EventType.BUILD_FAILED,
        EventType.SYNC_COMPLETED,
        EventType.SYNC_FAILED,
        EventType.BACKUP_COMPLETED,
        EventType.BACKUP_FAILED,
        EventType.THRESHOLD_EXCEEDED,
    ]
    
    for event_type in event_types:
        event = notifier.emit_event(
            event_type=event_type,
            dataset_path=Path("/data/test.jsonl"),
        )
        assert event.event_type == event_type


def test_all_notification_types():
    """Test all notification types can be used."""
    notifier = DatasetNotificationSystem()
    
    notification_types = [
        NotificationType.INFO,
        NotificationType.WARNING,
        NotificationType.ERROR,
        NotificationType.SUCCESS,
        NotificationType.CRITICAL,
    ]
    
    for i, notification_type in enumerate(notification_types):
        notifier.create_rule(
            rule_id=f"rule_{i}",
            event_type=EventType.DATASET_CREATED,
            notification_type=notification_type,
            channels=[NotificationChannel.LOG],
        )
        
        assert notifier.rules[f"rule_{i}"].notification_type == notification_type


def test_all_channels():
    """Test all notification channels can be used."""
    notifier = DatasetNotificationSystem()
    
    channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.SLACK,
        NotificationChannel.WEBHOOK,
        NotificationChannel.LOG,
        NotificationChannel.CONSOLE,
        NotificationChannel.SMS,
    ]
    
    rule = notifier.create_rule(
        rule_id="all_channels",
        event_type=EventType.BUILD_FAILED,
        notification_type=NotificationType.CRITICAL,
        channels=channels,
    )
    
    assert len(rule.channels) == 6


def test_multiple_rules_same_event():
    """Test multiple rules can trigger on same event."""
    notifier = DatasetNotificationSystem()
    
    # Create multiple rules for same event
    notifier.create_rule(
        rule_id="log_rule",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.LOG],
    )
    
    notifier.create_rule(
        rule_id="email_rule",
        event_type=EventType.BUILD_COMPLETED,
        notification_type=NotificationType.SUCCESS,
        channels=[NotificationChannel.EMAIL],
    )
    
    # Emit event
    notifier.emit_event(
        event_type=EventType.BUILD_COMPLETED,
        dataset_path=Path("/data/test.jsonl"),
    )
    
    # Should have 2 notifications
    assert len(notifier.notifications) == 2


def test_threshold_operators():
    """Test all threshold comparison operators."""
    notifier = DatasetNotificationSystem()
    
    operators = [">", ">=", "<", "<=", "=="]
    
    for i, operator in enumerate(operators):
        notifier.create_rule(
            rule_id=f"threshold_{i}",
            event_type=EventType.QUALITY_SCORE_CHANGED,
            notification_type=NotificationType.WARNING,
            channels=[NotificationChannel.LOG],
            conditions={
                "threshold": {
                    "metric": "score",
                    "operator": operator,
                    "value": 75.0,
                }
            },
        )
    
    # Test > operator (rule_0)
    notifier.emit_event(
        event_type=EventType.QUALITY_SCORE_CHANGED,
        dataset_path=Path("/data/test.jsonl"),
        metadata={"score": 80.0},
    )
    
    # Should trigger rule_0 (> 75.0) and rule_1 (>= 75.0)
    assert len([n for n in notifier.notifications if "threshold_0" in n.notification_id or "threshold_1" in n.notification_id]) >= 1
