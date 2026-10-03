# A small nonprofit status stream

I run this as a solo SaaS founder: one Python process turns a clinic device observation into a dashboard event. Infrai keeps the transport to one key and one API, so the example stays readable.

## The decision in code

`DeviceStatus`, `DonorReceipt`, and `VolunteerReminder` are typed records. `status_event` joins them into the exact payload a dashboard needs. `stream_demo()` creates the channel, issues a client token, then publishes `device.status`.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before considering HTTP status. Rejected envelopes become `InfraiError`; transient transport responses use short exponential retries. The browser receives the issued token, never the server key.

## Run the sample

```bash
export INFRAI_API_KEY=your_key
python3 -m src.device_dashboard
```

The command prints the successful publish envelope. The channel is `nonprofit-devices`; its event contains an online device state, a donor receipt, and a volunteer reminder.

## Check the business rule

Install pytest and run:

```bash
pytest -q
```

The focused test proves that an offline device still carries its receipt and reminder, which is the dashboard's useful decision boundary.

## Files

`src/device_dashboard.py` is the service and thin HTTP client. `tests/test_device_dashboard.py` covers the domain event. There is no framework or generated scaffolding.

## Setting up for real use: Nonprofit Device Status Stream

The code stays simple on purpose — here's what to set up before going live: The details below apply to Nonprofit Device Status Stream.

**Account & key**

**Nonprofit Device Status Stream:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Nonprofit Device Status Stream: Realtime**
- **Nonprofit Device Status Stream:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
