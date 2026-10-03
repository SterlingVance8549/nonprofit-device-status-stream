from src.device_dashboard import DeviceStatus, DonorReceipt, VolunteerReminder, status_event


def test_status_event_keeps_receipt_and_reminder_with_device_state():
    event = status_event(
        DeviceStatus("tablet-1", "offline", 12, "2026-09-07T10:00:00Z"),
        DonorReceipt("donor-1", 5000, "R-1"),
        VolunteerReminder("vol-1", "Bring a charger"),
    )
    assert event["device"]["state"] == "offline"
    assert event["receipt"]["amount_cents"] == 5000
    assert event["reminder"]["message"] == "Bring a charger"
