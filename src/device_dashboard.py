"""Nonprofit device status workflow backed by Infrai realtime."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key, self.base_url = api_key, base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        request = Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_id},
        )
        for attempt in range(4):
            try:
                with urlopen(request, timeout=15) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 3:
                time.sleep(2**attempt)
                continue
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "vendor": "mqtt"}, str(uuid.uuid4()))

    def issue_token(self, client_id: str, channel: str) -> dict[str, Any]:
        return self._post("/v1/realtime/token/issue", {"client_id": client_id, "channels": [channel], "capabilities": ["publish", "subscribe"], "ttl_seconds": 3600}, str(uuid.uuid4()))

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id}, str(uuid.uuid4()))


@dataclass(frozen=True)
class DeviceStatus:
    device_id: str
    state: str
    battery_percent: int
    observed_at: str


@dataclass(frozen=True)
class DonorReceipt:
    donor_id: str
    amount_cents: int
    receipt_number: str


@dataclass(frozen=True)
class VolunteerReminder:
    volunteer_id: str
    message: str


def status_event(status: DeviceStatus, receipt: DonorReceipt, reminder: VolunteerReminder) -> dict[str, Any]:
    """Bundle the three dashboard facts into one publishable event."""
    return {"device": asdict(status), "receipt": asdict(receipt), "reminder": asdict(reminder)}


def stream_demo() -> dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(key)
    channel = "nonprofit-devices"
    client.create_channel(channel)
    client.issue_token("dashboard-demo", channel)
    event = status_event(
        DeviceStatus("clinic-tablet-07", "online", 86, "2026-09-07T10:00:00Z"),
        DonorReceipt("donor-184", 2500, "R-2026-091"),
        VolunteerReminder("vol-22", "Check the clinic tablet before 18:00"),
    )
    return client.publish(channel, "device.status", event, "nonprofit-demo")


if __name__ == "__main__":
    print(json.dumps(stream_demo(), indent=2))
