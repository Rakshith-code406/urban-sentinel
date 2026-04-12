from __future__ import annotations

import math
import random
import threading
import time
from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


SEVERITY_MESSAGES = {
    "SAFE": {
        "current_situation": "Stable conditions",
        "public_update": "System operating normally",
        "priority_band": "Stable conditions",
        "command_guidance": "Conditions are within a healthy range. Keep monitoring and maintain the current response posture.",
    },
    "MODERATE": {
        "current_situation": "Needs attention",
        "public_update": "Monitoring closely",
        "priority_band": "Needs attention",
        "command_guidance": "Conditions need attention. Keep the field team alert and continue close monitoring.",
    },
    "DANGER": {
        "current_situation": "Immediate response required",
        "public_update": "Action required immediately",
        "priority_band": "Immediate response required",
        "command_guidance": "Immediate response is required. Escalate this sensor state and dispatch mitigation as soon as possible.",
    },
}

RANGE_CONFIG = {
    "5min": {"minutes": 5, "bucket_minutes": 1, "label": "Last 5 Minutes", "legacy": "5m"},
    "30min": {"minutes": 30, "bucket_minutes": 5, "label": "Last 30 Minutes", "legacy": "30m"},
    "1day": {"minutes": 24 * 60, "bucket_minutes": 60, "label": "Last 24 Hours", "legacy": "1d"},
}

REPORT_RANGE_ALIASES = {
    "5m": "5min",
    "5min": "5min",
    "30m": "30min",
    "30min": "30min",
    "1d": "1day",
    "1day": "1day",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def severity_to_title(value: str) -> str:
    mapping = {"SAFE": "Safe", "MODERATE": "Moderate", "DANGER": "Danger"}
    return mapping.get(str(value or "SAFE").upper(), "Safe")


def compare_trend(current: float, previous: float, *, invert: bool = False, parking: bool = False) -> str:
    delta = float(current) - float(previous)
    if abs(delta) < 0.01:
        return "Stable"
    if parking:
        return "Opening up" if delta > 0 else "Filling up"
    if invert:
        return "Falling" if delta > 0 else "Rising"
    return "Rising" if delta > 0 else "Falling"


class CentralSensorEngine:
    def __init__(self, interval_seconds: int = 2) -> None:
        self.interval_seconds = max(2, int(interval_seconds))
        self.lock = threading.Lock()
        self.random = random.Random(20260411)
        self.thread: Optional[threading.Thread] = None
        self.history: deque[dict[str, Any]] = deque(maxlen=50_000)
        self.snapshot_history: deque[dict[str, Any]] = deque(maxlen=50_000)
        self.report_cache: dict[str, dict[str, Any]] = {}
        self.locations = [
            {"id": 1, "name": "Bidarahalli", "latitude": 13.0683, "longitude": 77.7084},
        ]
        self.state = {
            "traffic": 10,
            "fire": 5,
            "parking": [0, 1],
            "street_light": 80,
            "waste_bin": 28,
        }
        self.latest_snapshot: Optional[dict[str, Any]] = None
        self._seed_history_locked()

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return

        def _run() -> None:
            while True:
                try:
                    self.tick()
                except Exception:
                    pass
                time.sleep(self.interval_seconds)

        self.thread = threading.Thread(target=_run, daemon=True, name="central-sensor-engine")
        self.thread.start()

    def _seed_history_locked(self) -> None:
        base_time = utc_now() - timedelta(hours=24)
        for minute in range(24 * 60):
            timestamp = base_time + timedelta(minutes=minute)
            self._advance_state_locked(timestamp, allow_fire_reset=True)
            snapshot = self._build_snapshot_locked(timestamp)
            self.snapshot_history.append(snapshot)
            self.history.append(self._to_history_row(snapshot))
        self.latest_snapshot = deepcopy(self.snapshot_history[-1]) if self.snapshot_history else None
        self._rebuild_reports_locked()

    def tick(self) -> dict[str, Any]:
        with self.lock:
            timestamp = utc_now()
            self._advance_state_locked(timestamp, allow_fire_reset=True)
            snapshot = self._build_snapshot_locked(timestamp)
            self.latest_snapshot = deepcopy(snapshot)
            self.snapshot_history.append(snapshot)
            self.history.append(self._to_history_row(snapshot))
            self._rebuild_reports_locked()
            return deepcopy(snapshot)

    def ingest_external(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            traffic = payload.get("traffic_total", payload.get("traffic"))
            fire = payload.get("fire_smoke", payload.get("fire"))
            light = payload.get("light_percent", payload.get("street_light"))
            parking_a = payload.get("parking_a")
            parking_b = payload.get("parking_b")
            parking_available = payload.get("parking_available")

            if traffic is not None:
                self.state["traffic"] = int(clamp(float(traffic), 0, 60))
            if fire is not None:
                self.state["fire"] = int(clamp(float(fire), 0, 100))
            if light is not None:
                self.state["street_light"] = int(clamp(float(light), 0, 100))
            if parking_a is not None or parking_b is not None or parking_available is not None:
                self.state["parking"] = self._normalize_parking_state(parking_a, parking_b, parking_available)

            timestamp = utc_now()
            snapshot = self._build_snapshot_locked(timestamp)
            self.latest_snapshot = deepcopy(snapshot)
            self.snapshot_history.append(snapshot)
            self.history.append(self._to_history_row(snapshot))
            self._rebuild_reports_locked()
            return deepcopy(snapshot)

    def reset(self) -> dict[str, Any]:
        with self.lock:
            self.state = {
                "traffic": 10,
                "fire": 5,
                "parking": [0, 1],
                "street_light": 80,
                "waste_bin": 28,
            }
            timestamp = utc_now()
            snapshot = self._build_snapshot_locked(timestamp)
            self.latest_snapshot = deepcopy(snapshot)
            self.snapshot_history.append(snapshot)
            self.history.append(self._to_history_row(snapshot))
            self._rebuild_reports_locked()
            return deepcopy(snapshot)

    def get_snapshot(self) -> dict[str, Any]:
        with self.lock:
            if self.latest_snapshot is None:
                self.latest_snapshot = self._build_snapshot_locked(utc_now())
            return deepcopy(self.latest_snapshot)

    def get_history(self, limit: int = 2000, hours: Optional[int] = None) -> list[dict[str, Any]]:
        with self.lock:
            rows = list(self.history)
            if hours is not None:
                cutoff = utc_now() - timedelta(hours=max(1, int(hours)))
                rows = [row for row in rows if self._parse_iso(row["timestamp"]) >= cutoff]
            safe_limit = max(1, min(int(limit), len(rows) if rows else 1))
            return deepcopy(rows[-safe_limit:])

    def get_live_payload(self) -> dict[str, Any]:
        snapshot = self.get_snapshot()
        return {
            "success": True,
            "status": "success",
            "source": "central_sensor_engine",
            "snapshot": snapshot,
            "locations": [self._location_payload(snapshot)],
            "alerts": [],
            "meta": {
                "sensor_refresh_seconds": self.interval_seconds,
                "reports_precomputed": True,
            },
        }

    def get_reports(self, range_key: str) -> dict[str, Any]:
        normalized = REPORT_RANGE_ALIASES.get(str(range_key or "").strip().lower())
        if not normalized:
            raise ValueError("range must be one of 5min, 30min, or 1day")
        with self.lock:
            return deepcopy(self.report_cache[normalized])

    def get_environment_payload(self) -> dict[str, Any]:
        snapshot = self.get_snapshot()
        return {
            "temperature": snapshot["temperature"],
            "humidity": snapshot["humidity"],
            "air_quality": snapshot["air_status"],
            "air_status": snapshot["air_status"],
            "air_smoke": snapshot["air_smoke"],
            "rain_intensity": snapshot["rain_status"],
            "rain_status": snapshot["rain_status"],
            "rain_percent": snapshot["rain_percent"],
            "temp_status": snapshot["temp_status"],
            "timestamp": snapshot["timestamp"],
            "last_updated": snapshot["last_updated"],
            "location": {
                "label": snapshot["location"],
                "latitude": snapshot["latitude"],
                "longitude": snapshot["longitude"],
            },
        }

    def get_environment_summary_payload(self) -> dict[str, Any]:
        snapshot = self.get_snapshot()
        return {
            "temperature": {"live_value": snapshot["temperature"], "status": snapshot["temp_status"]},
            "air": {"live_value": snapshot["air_smoke"], "status": snapshot["air_status"]},
            "humidity": {"live_value": snapshot["humidity"], "status": snapshot["humidity_status"]},
            "rain": {"live_value": snapshot["rain_percent"], "status": snapshot["rain_status"]},
            "timestamp": snapshot["timestamp"],
            "last_updated": snapshot["last_updated"],
            "location": {
                "label": snapshot["location"],
                "latitude": snapshot["latitude"],
                "longitude": snapshot["longitude"],
            },
        }

    def _advance_state_locked(self, timestamp: datetime, *, allow_fire_reset: bool) -> None:
        traffic_step = self.random.randint(-2, 2)
        self.state["traffic"] = int(clamp(self.state["traffic"] + traffic_step, 2, 48))

        fire_step = self.random.choice([0, 1, 1, 2])
        if allow_fire_reset and self.state["fire"] >= 92:
            fire_step = -self.random.choice([2, 3, 4])
        self.state["fire"] = int(clamp(self.state["fire"] + fire_step, 0, 100))

        self._advance_parking_locked()
        self._advance_street_light_locked(timestamp)
        self._advance_waste_bin_locked()

    def _advance_parking_locked(self) -> None:
        occupied_bias = clamp(self.state["traffic"] / 50, 0.05, 0.9)
        next_parking = list(self.state["parking"])
        slot_index = self.random.randrange(len(next_parking))
        slot_value = next_parking[slot_index]
        if slot_value == 1:
            if self.random.random() < (0.08 + (1 - occupied_bias) * 0.08):
                next_parking[slot_index] = 0
        else:
            if self.random.random() < (0.07 + occupied_bias * 0.18):
                next_parking[slot_index] = 1
        self.state["parking"] = next_parking

    def _advance_street_light_locked(self, timestamp: datetime) -> None:
        hour = timestamp.astimezone(timezone.utc).hour
        day_cycle = math.sin(((hour + timestamp.minute / 60) - 6) / 24 * 2 * math.pi)
        target = 55 + day_cycle * 30
        target += math.sin(timestamp.timestamp() / 3600) * 4
        step = clamp(target - self.state["street_light"], -3, 3)
        jitter = self.random.choice([-1, 0, 1])
        self.state["street_light"] = int(clamp(self.state["street_light"] + step + jitter, 5, 98))

    def _advance_waste_bin_locked(self) -> None:
        delta = self.random.choice([0, 1, 1, 2]) if self.state["traffic"] >= 18 else self.random.choice([0, 0, 1])
        if self.state["waste_bin"] >= 92:
            delta = -self.random.choice([8, 10, 12])
        self.state["waste_bin"] = int(clamp(self.state["waste_bin"] + delta, 8, 98))

    def _build_snapshot_locked(self, timestamp: datetime) -> dict[str, Any]:
        traffic = int(self.state["traffic"])
        fire = int(self.state["fire"])
        parking = list(self.state["parking"])
        street_light = int(self.state["street_light"])
        waste_bin = int(self.state["waste_bin"])
        location = self.locations[0]
        previous = self.latest_snapshot or {}

        traffic_lane1 = max(0, traffic // 2)
        traffic_lane2 = max(0, traffic - traffic_lane1)
        parking_available = parking.count(0)
        hour_fraction = timestamp.hour + timestamp.minute / 60
        temperature = round(clamp(28 + math.sin((hour_fraction - 6) / 24 * 2 * math.pi) * 6, 18, 40), 1)
        humidity = round(clamp(62 + math.sin((hour_fraction + 3) / 24 * 2 * math.pi) * 14, 35, 90), 1)
        rain_percent = int(round(clamp(28 + math.sin(timestamp.timestamp() / 5400) * 24, 0, 100)))
        flood_level = int(round(clamp(rain_percent * 0.55, 0, 100)))
        noise_level = int(round(clamp(34 + traffic * 1.7, 30, 110)))
        air_smoke = int(round(clamp(8 + fire * 0.85, 0, 100)))

        sensor_details = {
            "traffic_total": self._build_traffic_detail(traffic, previous),
            "fire_smoke": self._build_fire_detail(fire, previous),
            "parking_available": self._build_parking_detail(parking_available, previous),
            "light_percent": self._build_light_detail(street_light, previous),
            "noise_level": self._build_noise_detail(noise_level, previous),
            "flood_level": self._build_flood_detail(flood_level, previous),
            "bin_fill": self._build_bin_detail(waste_bin, previous),
        }

        snapshot = {
            "location": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timestamp": timestamp.isoformat(),
            "last_updated": timestamp.isoformat(),
            "traffic": traffic,
            "fire": fire,
            "parking": parking,
            "street_light": street_light,
            "traffic_lane1": traffic_lane1,
            "traffic_lane2": traffic_lane2,
            "traffic_total": traffic,
            "fire_smoke": fire,
            "parking_a": "AVAILABLE" if parking[0] == 0 else "OCCUPIED",
            "parking_b": "AVAILABLE" if parking[1] == 0 else "OCCUPIED",
            "parking_available": parking_available,
            "light_percent": street_light,
            "noise_level": noise_level,
            "flood_level": flood_level,
            "bin_fill": waste_bin,
            "temperature": temperature,
            "humidity": humidity,
            "air_smoke": air_smoke,
            "rain_percent": rain_percent,
            "traffic_status": sensor_details["traffic_total"]["status_label"],
            "fire_status": sensor_details["fire_smoke"]["status_label"],
            "parking_status": sensor_details["parking_available"]["status_label"],
            "light_status": sensor_details["light_percent"]["status_label"],
            "noise_status": sensor_details["noise_level"]["status_label"],
            "flood_status": sensor_details["flood_level"]["status_label"],
            "bin_status": sensor_details["bin_fill"]["status_label"],
            "air_status": self._air_status(air_smoke),
            "rain_status": self._rain_status(rain_percent),
            "temp_status": self._temp_status(temperature),
            "humidity_status": self._humidity_status(humidity),
            "sensor_details": sensor_details,
            "overall_status": self._overall_status(sensor_details),
        }
        return snapshot

    def _base_detail(
        self,
        *,
        sensor_id: str,
        label: str,
        value: float,
        unit: str,
        severity: str,
        trend: str,
    ) -> dict[str, Any]:
        copy = SEVERITY_MESSAGES[severity]
        return {
            "id": sensor_id,
            "label": label,
            "value": value,
            "unit": unit,
            "severity": severity_to_title(severity),
            "status": severity,
            "status_label": copy["current_situation"],
            "current_situation": copy["current_situation"],
            "public_update": copy["public_update"],
            "priority_band": copy["priority_band"],
            "command_guidance": copy["command_guidance"],
            "trend": trend,
            "trend_label": trend,
        }

    def _build_traffic_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "SAFE" if value <= 20 else "MODERATE" if value <= 34 else "DANGER"
        previous_value = float(previous.get("traffic_total", value))
        detail = self._base_detail(
            sensor_id="traffic_total",
            label="Traffic Density",
            value=value,
            unit="veh",
            severity=severity,
            trend=compare_trend(value, previous_value),
        )
        return detail

    def _build_fire_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "SAFE" if value < 30 else "MODERATE" if value < 70 else "DANGER"
        previous_value = float(previous.get("fire_smoke", value))
        return self._base_detail(
            sensor_id="fire_smoke",
            label="Fire Smoke",
            value=value,
            unit="%",
            severity=severity,
            trend=compare_trend(value, previous_value),
        )

    def _build_parking_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "SAFE" if value == 2 else "MODERATE" if value == 1 else "DANGER"
        previous_value = float(previous.get("parking_available", value))
        return self._base_detail(
            sensor_id="parking_available",
            label="Parking Availability",
            value=value,
            unit="slots",
            severity=severity,
            trend=compare_trend(value, previous_value, parking=True),
        )

    def _build_light_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "DANGER" if value < 40 else "SAFE" if value <= 80 else "MODERATE"
        previous_value = float(previous.get("light_percent", value))
        return self._base_detail(
            sensor_id="light_percent",
            label="Street Light System",
            value=value,
            unit="%",
            severity=severity,
            trend=compare_trend(value, previous_value),
        )

    def _build_noise_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "SAFE" if value < 65 else "MODERATE" if value < 85 else "DANGER"
        previous_value = float(previous.get("noise_level", value))
        return self._base_detail(
            sensor_id="noise_level",
            label="Noise Level",
            value=value,
            unit="dB",
            severity=severity,
            trend=compare_trend(value, previous_value),
        )

    def _build_flood_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "SAFE" if value < 35 else "MODERATE" if value < 70 else "DANGER"
        previous_value = float(previous.get("flood_level", value))
        return self._base_detail(
            sensor_id="flood_level",
            label="Flood Level",
            value=value,
            unit="%",
            severity=severity,
            trend=compare_trend(value, previous_value),
        )

    def _build_bin_detail(self, value: int, previous: dict[str, Any]) -> dict[str, Any]:
        severity = "SAFE" if value < 65 else "MODERATE" if value < 90 else "DANGER"
        previous_value = float(previous.get("bin_fill", value))
        return self._base_detail(
            sensor_id="bin_fill",
            label="Waste Bin Fill",
            value=value,
            unit="%",
            severity=severity,
            trend=compare_trend(value, previous_value),
        )

    def _overall_status(self, details: dict[str, dict[str, Any]]) -> str:
        if any(item["status"] == "DANGER" for item in details.values()):
            return "DANGER"
        if any(item["status"] == "MODERATE" for item in details.values()):
            return "MODERATE"
        return "SAFE"

    def _location_payload(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": 1,
            "name": snapshot["location"],
            "lat": snapshot["latitude"],
            "lng": snapshot["longitude"],
            "severity": severity_to_title(snapshot["overall_status"]),
            "priority": SEVERITY_MESSAGES[snapshot["overall_status"]]["priority_band"],
            "last_updated": snapshot["timestamp"],
            "sensors": snapshot["sensor_details"],
        }

    def _rebuild_reports_locked(self) -> None:
        snapshots = list(self.snapshot_history)
        for range_key, config in RANGE_CONFIG.items():
            self.report_cache[range_key] = self._build_report_locked(range_key, config, snapshots)

    def _build_report_locked(self, range_key: str, config: dict[str, Any], snapshots: list[dict[str, Any]]) -> dict[str, Any]:
        now = utc_now()
        window_start = now - timedelta(minutes=config["minutes"])
        rows = [row for row in snapshots if self._parse_iso(row["timestamp"]) >= window_start]
        buckets = self._bucketize(rows, config["bucket_minutes"], now, config["minutes"])
        latest = buckets[-1] if buckets else {"danger_count": 0, "moderate_count": 0, "safe_count": 0, "incident_count": 0}
        danger = int(latest["danger_count"])
        moderate = int(latest["moderate_count"])
        safe = int(latest["safe_count"])
        all_samples = int(latest["incident_count"])
        system_status = "Active Alerts" if danger else "Monitoring Advisory" if moderate else "Stable"
        payload = {
            "range": range_key,
            "range_key": config["legacy"],
            "window_label": config["label"],
            "bucket_minutes": config["bucket_minutes"],
            "count": all_samples,
            "total_samples": moderate + safe,
            "all_samples": all_samples,
            "critical_incidents": danger,
            "danger_incidents": danger,
            "moderate_incidents": moderate,
            "safe_incidents": safe,
            "monitored_sensor_total": 7,
            "system_status": system_status,
            "window_start": window_start.isoformat(),
            "window_end": now.isoformat(),
            "data": buckets,
        }
        return payload

    def _bucketize(self, rows: list[dict[str, Any]], bucket_minutes: int, now: datetime, total_minutes: int) -> list[dict[str, Any]]:
        bucket_count = max(1, total_minutes // bucket_minutes)
        buckets: list[dict[str, Any]] = []
        rows_by_bucket: dict[int, dict[str, Any]] = {}

        for row in rows:
            parsed = self._parse_iso(row["timestamp"])
            delta_minutes = max(0, int((now - parsed).total_seconds() // 60))
            bucket_index = bucket_count - 1 - min(bucket_count - 1, delta_minutes // bucket_minutes)
            rows_by_bucket[bucket_index] = row

        previous_counts = {"danger_count": 0, "moderate_count": 0, "safe_count": 7, "incident_count": 7}
        for index in range(bucket_count):
            bucket_end = now - timedelta(minutes=(bucket_count - index - 1) * bucket_minutes)
            row = rows_by_bucket.get(index)
            if row is None:
                counts = previous_counts.copy()
            else:
                counts = self._summary_counts(row)
                previous_counts = counts.copy()
            buckets.append(
                {
                    "timestamp": bucket_end.isoformat(),
                    **counts,
                }
            )
        return buckets

    def _summary_counts(self, snapshot: dict[str, Any]) -> dict[str, int]:
        danger = 0
        moderate = 0
        safe = 0
        for detail in snapshot.get("sensor_details", {}).values():
            status = str(detail.get("status") or "SAFE").upper()
            if status == "DANGER":
                danger += 1
            elif status == "MODERATE":
                moderate += 1
            else:
                safe += 1
        total = danger + moderate + safe
        return {
            "danger_count": danger,
            "moderate_count": moderate,
            "safe_count": safe,
            "incident_count": total,
        }

    def _to_history_row(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        row = deepcopy(snapshot)
        row.pop("sensor_details", None)
        row.pop("overall_status", None)
        return row

    def _normalize_parking_state(self, parking_a: Any, parking_b: Any, parking_available: Any) -> list[int]:
        def normalize_slot(value: Any) -> Optional[int]:
            normalized = str(value or "").strip().lower()
            if not normalized:
                return None
            if "available" in normalized or normalized == "0":
                return 0
            return 1

        slot_a = normalize_slot(parking_a)
        slot_b = normalize_slot(parking_b)
        if slot_a is not None and slot_b is not None:
            return [slot_a, slot_b]
        if parking_available is not None:
            available = int(clamp(float(parking_available), 0, 2))
            return [0 if index < available else 1 for index in range(2)]
        return list(self.state["parking"])

    def _air_status(self, value: int) -> str:
        if value < 30:
            return "Good"
        if value < 70:
            return "Moderate"
        return "Hazardous"

    def _rain_status(self, value: int) -> str:
        if value < 30:
            return "Low"
        if value < 70:
            return "Moderate"
        return "Heavy"

    def _temp_status(self, value: float) -> str:
        if value < 20:
            return "Cool"
        if value < 33:
            return "Normal"
        return "Hot"

    def _humidity_status(self, value: float) -> str:
        if value < 45:
            return "Dry"
        if value < 70:
            return "Comfortable"
        return "Humid"

    def _parse_iso(self, value: str) -> datetime:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
