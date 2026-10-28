"""Optional MQTT events. Never in the data path, never a reason to fail.

ARCHITECTURE.md, corrected 2026-10-24: "MQTT is not in the data path and must
not become a dependency of it... If the broker is absent or unreachable, the
bridge must keep working and lose nothing. Publishing is a side effect of
ingest, never a step in it."

So this module is built to be absent:

  * nothing starts unless `MQTT_HOST` is set, and `paho-mqtt` is imported only
    then -- a minimal install needs neither the broker nor the library;
  * `connect_async` + `loop_start`, so a dead broker costs no wall time in a
    pass and reconnects on its own;
  * every call is wrapped. A publish that raises must not lose a trip that is
    already durable in the spool, so the exception is logged once and dropped.

`accord-bridge.service` therefore has no `mosquitto.service` in `After=`. A
service that cannot start without a broker has made the broker load-bearing.
"""
import json
import logging
import os
from urllib.parse import urlparse

LOG = logging.getLogger("accord-bridge")


def broker_from_env(env=os.environ):
    """Same shape as ir-bridge's, so one `/etc/*.env` convention covers both."""
    if not env.get("MQTT_HOST"):
        return None
    url = urlparse(env["MQTT_HOST"])
    return dict(host=url.hostname or "127.0.0.1", port=url.port or 1883,
                username=env.get("MQTT_USERNAME") or url.username or None,
                password=env.get("MQTT_PASSWORD") or url.password or None)


class Events:
    """A publisher that is allowed to do nothing at all."""

    def __init__(self, broker, prefix="accord"):
        self.prefix = prefix
        self.client = None
        if not broker:
            return
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            # Deliberately not fatal: MQTT_HOST set without the library is a
            # host-setup oversight, not a reason to stop ingesting a drive.
            LOG.warning("MQTT_HOST is set but paho-mqtt is not installed; "
                        "events disabled, ingest unaffected")
            return
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                 client_id="accord-bridge")
            if broker["username"]:
                client.username_pw_set(broker["username"], broker["password"])
            client.will_set(f"{prefix}/bridge/availability", "offline", retain=True)
            client.reconnect_delay_set(min_delay=1, max_delay=30)
            client.connect_async(broker["host"], broker["port"], keepalive=60)
            client.loop_start()
            self.client = client
            LOG.info("MQTT events -> %s:%d prefix=%s",
                     broker["host"], broker["port"], prefix)
        except Exception as exc:                        # noqa: BLE001 -- see above
            LOG.warning("MQTT disabled (%s); ingest unaffected", exc)

    def publish(self, topic, payload, retain=False):
        if self.client is None:
            return
        try:
            self.client.publish(f"{self.prefix}/{topic}",
                                payload if isinstance(payload, (str, bytes))
                                else json.dumps(payload, separators=(",", ":")),
                                retain=retain)
        except Exception as exc:                        # noqa: BLE001
            LOG.warning("MQTT publish %s failed: %s", topic, exc)

    def online(self):
        self.publish("bridge/availability", "online", retain=True)

    def trip(self, packet):
        """One event per NEW trip, carrying what a dashboard would want.

        Miles and pulses only -- no odometer. The odometer is the database's
        answer, computed from anchors it owns, and a second one published from
        here would be a second source of truth for the number this project is
        most careful about.
        """
        self.publish("trip", {
            "trip_id": packet["trip_id"],
            "started_at": packet["started_at"],
            "ended_at": packet["ended_at"],
            "miles": packet["vss"]["miles"],
            "pulses": packet["vss"]["pulse_count_trip"],
            "max_mph": packet["vss"].get("max_mph"),
            "max_rpm": (packet.get("tach") or {}).get("max_rpm"),
            "close_reason": packet.get("close_reason"),
            "warnings": packet.get("warnings") or [],
        })

    def status(self, summary):
        self.publish("bridge/status", {
            "errors": summary["errors"],
            "spooled": summary["spooled"],
            "files": summary["files"],
        }, retain=True)

    def stop(self):
        if self.client is None:
            return
        try:
            self.client.publish(f"{self.prefix}/bridge/availability", "offline",
                                retain=True).wait_for_publish(timeout=2)
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as exc:                        # noqa: BLE001
            LOG.warning("MQTT shutdown: %s", exc)
