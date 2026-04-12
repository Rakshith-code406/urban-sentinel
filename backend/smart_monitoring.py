from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid


STATUS_ORDER = {"SAFE": 0, "WARNING": 1, "DANGER": 2, "CRITICAL": 3}
STATUS_TO_PRIORITY = {
    "SAFE": "Low",
    "WARNING": "Medium",
    "DANGER": "High",
    "CRITICAL": "Immediate",
}
STATUS_TO_MARKER = {
    "SAFE": {"color": "green", "blinking": False},
    "WARNING": {"color": "yellow", "blinking": False},
    "DANGER": {"color": "orange", "blinking": False},
    "CRITICAL": {"color": "red", "blinking": True},
}
LEGACY_STATUS = {
    "SAFE": "Safe",
    "WARNING": "Moderate",
    "DANGER": "Danger",
    "CRITICAL": "Danger",
}
DEFAULT_LOCATION_CATALOG = [
    {"id": 1, "name": "Bidarahalli", "lat": 13.0683, "lng": 77.7084},
    {"id": 2, "name": "KR Puram", "lat": 13.0080, "lng": 77.6957},
    {"id": 3, "name": "Whitefield", "lat": 12.9698, "lng": 77.7500},
    {"id": 4, "name": "Hebbal", "lat": 13.0358, "lng": 77.5970},
]
SENSOR_CONFIG = {
    "noise_level": {
        "label": "Noise Level",
        "unit": "dB",
        "direction": "high",
        "warning": 60,
        "danger": 75,
        "critical": 90,
        "history_key": "noise",
        "legacy_status_key": "noise_status",
    },
    "flood_level": {
        "label": "Flood Level",
        "unit": "%",
        "direction": "high",
        "warning": 60,
        "danger": 75,
        "critical": 90,
        "history_key": "flood",
        "legacy_status_key": "flood_status",
    },
    "bin_fill": {
        "label": "Waste Bin Fill",
        "unit": "%",
        "direction": "high",
        "warning": 60,
        "danger": 75,
        "critical": 90,
        "history_key": "waste",
        "legacy_status_key": "bin_status",
    },
    "light_percent": {
        "label": "Light Intensity",
        "unit": "%",
        "direction": "low",
        "warning": 40,
        "danger": 25,
        "critical": 10,
        "history_key": "light",
        "legacy_status_key": "light_status",
    },
}
SENSOR_RESET_DEFAULTS = {
    "noise_level": 42,
    "flood_level": 8,
    "bin_fill": 24,
    "light_percent": 74,
    "fire_smoke": 10,
}
STREET_LIGHT_DAY_THRESHOLD = 70
STREET_LIGHT_OPERATIONAL_MIN = 40
STREET_LIGHT_OPERATIONAL_MAX = 80
STREET_LIGHT_FAULT_LOW = 20
STREET_LIGHT_FAULT_HIGH = 95


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def format_relative_update(timestamp: Optional[str], now: Optional[datetime] = None) -> str:
    parsed = parse_iso(timestamp)
    if parsed is None:
        return "Live data temporarily unavailable"
    current = now or datetime.utcnow()
    diff = max(timedelta(0), current - parsed)
    minutes = int(diff.total_seconds() // 60)
    if minutes <= 0:
        return "Updated just now"
    if minutes == 1:
        return "Updated 1 min ago"
    if minutes < 60:
        return f"Updated {minutes} min ago"
    hours = int(minutes // 60)
    if hours == 1:
        return "Updated 1 hour ago"
    return f"Updated {hours} hours ago"


def normalize_location_key(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().lower().split())


def build_location_key(location: Optional[str], latitude: Optional[float] = None, longitude: Optional[float] = None) -> str:
    normalized_location = normalize_location_key(location)
    if normalized_location:
        return normalized_location
    if latitude is not None and longitude is not None:
        return f"{round(float(latitude), 4)},{round(float(longitude), 4)}"
    return "default"


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def smooth_value(previous: Optional[float], target: Optional[float], max_step: float, lower: float, upper: float) -> Optional[float]:
    if target is None:
        return previous
    if previous is None:
        return clamp(float(target), lower, upper)
    delta = float(target) - float(previous)
    if abs(delta) > max_step:
        target = float(previous) + (max_step if delta > 0 else -max_step)
    return clamp(float(target), lower, upper)


def get_trend(values: list[float]) -> str:
    if len(values) < 3:
        return "stable"
    diff = values[-1] - values[0]
    if diff > 5:
        return "rising"
    if diff < -5:
        return "falling"
    return "stable"


def build_status_label(status: str, sensor_label: str, *, is_light: bool = False) -> str:
    normalized = str(status or "SAFE").upper()
    if is_light:
        return sensor_label
    if normalized == "CRITICAL":
        return f"{sensor_label}: Critical"
    if normalized == "DANGER":
        return f"{sensor_label}: Danger"
    if normalized == "WARNING":
        return f"{sensor_label}: Attention"
    return f"{sensor_label}: Stable"


def classify_status(value: Optional[float], config: dict[str, Any]) -> str:
    if value is None:
        return "SAFE"
    warning = float(config["warning"])
    danger = float(config["danger"])
    critical = float(config["critical"])
    if config["direction"] == "low":
        if value <= critical:
            return "CRITICAL"
        if value <= danger:
            return "DANGER"
        if value <= warning:
            return "WARNING"
        return "SAFE"
    if value >= critical:
        return "CRITICAL"
    if value >= danger:
        return "DANGER"
    if value >= warning:
        return "WARNING"
    return "SAFE"


def predictive_status(current_status: str, value: Optional[float], trend: str, config: dict[str, Any]) -> str:
    if value is None or current_status != "SAFE" or trend != "rising":
        return current_status
    warning = float(config["warning"])
    if config["direction"] == "low":
        if value <= warning * 1.2:
            return "WARNING"
        return current_status
    if value >= warning * 0.8:
        return "WARNING"
    return current_status


def predict_in_five_minutes(values: list[float], current: Optional[float], config: dict[str, Any]) -> tuple[Optional[float], str]:
    if current is None:
        return None, "SAFE"
    if len(values) < 2:
        return current, classify_status(current, config)
    slope = (values[-1] - values[0]) / max(1, len(values) - 1)
    projection = current + slope * 5
    if config["direction"] == "low":
        projection = clamp(projection, 0, 100)
    else:
        projection = max(0, projection)
    return round(projection, 1), classify_status(projection, config)


def evaluate_street_light_status(value: Optional[float], previous_value: Optional[float]) -> tuple[str, str]:
    if value is None:
        return "SAFE", "Street light data syncing"

    is_day_time = value > STREET_LIGHT_DAY_THRESHOLD
    fluctuation = abs(value - previous_value) if previous_value is not None else 0
    if is_day_time:
        return "SAFE", "Day Time - Lights OFF"

    if value < STREET_LIGHT_FAULT_LOW or value > STREET_LIGHT_FAULT_HIGH or fluctuation >= 35:
        return "CRITICAL", "Fault Detected"

    if value < STREET_LIGHT_OPERATIONAL_MIN:
        return "WARNING", "Night Time - Lights ON"

    return "SAFE", "Night Time - Lights ON"


def max_status(statuses: list[str]) -> str:
    if not statuses:
        return "SAFE"
    return max(statuses, key=lambda item: STATUS_ORDER.get(item, 0))


def find_location_catalog_entry(location_name: Optional[str], latitude: Optional[float], longitude: Optional[float]) -> dict[str, Any]:
    desired_name = normalize_location_key(location_name)
    best = None
    best_distance = None
    for entry in DEFAULT_LOCATION_CATALOG:
        if desired_name and normalize_location_key(entry["name"]) == desired_name:
            return entry
        if latitude is None or longitude is None:
            continue
        distance = abs(entry["lat"] - float(latitude)) + abs(entry["lng"] - float(longitude))
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best = entry
    if best is not None and best_distance is not None and best_distance <= 0.25:
        return best
    return {
        "id": abs(hash(build_location_key(location_name, latitude, longitude))) % 100000,
        "name": location_name or "Monitored Zone",
        "lat": latitude if latitude is not None else DEFAULT_LOCATION_CATALOG[0]["lat"],
        "lng": longitude if longitude is not None else DEFAULT_LOCATION_CATALOG[0]["lng"],
    }


def build_history_window(sensor_history: list[dict[str, Any]], location_key: str) -> dict[str, list[float]]:
    history = {"noise": [], "flood": [], "waste": [], "light": []}
    for row in sensor_history:
        row_key = build_location_key(row.get("location"), safe_float(row.get("latitude")), safe_float(row.get("longitude")))
        if row_key != location_key:
            continue
        for sensor_id, config in SENSOR_CONFIG.items():
            value = safe_float(row.get(sensor_id))
            if value is None:
                continue
            bucket = history[config["history_key"]]
            bucket.append(value)
            if len(bucket) > 5:
                del bucket[0]
    return history


def derive_sensor_targets(entry: dict[str, Any], previous_entry: Optional[dict[str, Any]]) -> dict[str, float]:
    hour = parse_iso(entry.get("timestamp")).hour if parse_iso(entry.get("timestamp")) else datetime.utcnow().hour
    is_night = hour < 6 or hour >= 18
    rain = safe_float(entry.get("rain_percent")) or safe_float((previous_entry or {}).get("rain_percent")) or 0
    temperature = safe_float(entry.get("temperature")) or safe_float((previous_entry or {}).get("temperature")) or 26
    traffic = safe_float(entry.get("traffic_total")) or safe_float((previous_entry or {}).get("traffic_total")) or 6
    air_smoke = safe_float(entry.get("air_smoke")) or safe_float((previous_entry or {}).get("air_smoke")) or 35
    previous_noise = safe_float((previous_entry or {}).get("noise_level")) or SENSOR_RESET_DEFAULTS["noise_level"]
    previous_flood = safe_float((previous_entry or {}).get("flood_level")) or SENSOR_RESET_DEFAULTS["flood_level"]
    previous_waste = safe_float((previous_entry or {}).get("bin_fill")) or SENSOR_RESET_DEFAULTS["bin_fill"]
    previous_light = safe_float((previous_entry or {}).get("light_percent")) or SENSOR_RESET_DEFAULTS["light_percent"]
    previous_fire_smoke = safe_float((previous_entry or {}).get("fire_smoke")) or SENSOR_RESET_DEFAULTS["fire_smoke"]
    return {
        "noise_level": clamp(previous_noise * 0.65 + (36 + traffic * 1.8 + air_smoke * 0.05 + (6 if not is_night else -4)) * 0.35, 20, 120),
        "flood_level": clamp(previous_flood * 0.55 + (rain * 0.78 + max(0, temperature - 25) * 0.6) * 0.45, 0, 100),
        "bin_fill": clamp(previous_waste * 0.82 + (18 + max(0, temperature - 24) * 0.9 + (5 if 11 <= hour <= 21 else 1)) * 0.18, 0, 100),
        "light_percent": clamp(previous_light * 0.55 + ((22 if is_night else 78) - rain * 0.2) * 0.45, 0, 100),
        "fire_smoke": clamp(previous_fire_smoke * 0.7 + (air_smoke * 0.35 + max(0, temperature - 30) * 1.2) * 0.3, 0, 100),
    }


def apply_realism(entry: dict[str, Any], previous_entry: Optional[dict[str, Any]]) -> dict[str, Any]:
    next_entry = deepcopy(entry)
    targets = derive_sensor_targets(next_entry, previous_entry)
    ranges = {
        "noise_level": (0, 120, 8),
        "flood_level": (0, 100, 10),
        "bin_fill": (0, 100, 6),
        "light_percent": (0, 100, 12),
        "fire_smoke": (0, 100, 10),
    }
    for sensor_id, (lower, upper, max_step) in ranges.items():
        previous_value = safe_float((previous_entry or {}).get(sensor_id))
        incoming_value = safe_float(next_entry.get(sensor_id))
        target = incoming_value if incoming_value is not None else targets[sensor_id]
        smoothed = smooth_value(previous_value, target, max_step=max_step, lower=lower, upper=upper)
        if smoothed is None:
            continue
        if sensor_id in {"noise_level", "flood_level", "bin_fill", "light_percent"}:
            smoothed = round(smoothed, 1)
        next_entry[sensor_id] = int(round(smoothed)) if sensor_id != "light_percent" else round(smoothed, 1)
    return next_entry


def enrich_snapshot(entry: dict[str, Any], sensor_history: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot = deepcopy(entry)
    location_entry = find_location_catalog_entry(
        snapshot.get("location"),
        safe_float(snapshot.get("latitude")),
        safe_float(snapshot.get("longitude")),
    )
    snapshot["location"] = snapshot.get("location") or location_entry["name"]
    snapshot["latitude"] = safe_float(snapshot.get("latitude")) or location_entry["lat"]
    snapshot["longitude"] = safe_float(snapshot.get("longitude")) or location_entry["lng"]
    location_key = build_location_key(snapshot["location"], snapshot["latitude"], snapshot["longitude"])
    history = build_history_window(sensor_history, location_key)
    statuses = []
    sensor_details = {}

    for sensor_id, config in SENSOR_CONFIG.items():
        history_values = history[config["history_key"]]
        value = safe_float(snapshot.get(sensor_id))
        trend = get_trend(history_values)
        previous_value = history_values[-1] if history_values else None
        if sensor_id == "light_percent":
            status, display_label = evaluate_street_light_status(value, previous_value)
            predicted_value = None if value is None else round(clamp(value, 0, 100), 1)
            predicted_status = status
            predicted_label = display_label
            status_label = display_label
        else:
            raw_status = classify_status(value, config)
            status = predictive_status(raw_status, value, trend, config)
            predicted_value, predicted_status = predict_in_five_minutes(history_values, value, config)
            predicted_label = f"Predicted risk in 5 mins: {predicted_status.title()}"
            status_label = build_status_label(status, config["label"])
        statuses.append(status)
        sensor_details[sensor_id] = {
            "id": sensor_id,
            "label": config["label"],
            "unit": config["unit"],
            "value": value,
            "status": status,
            "status_label": status_label,
            "priority": STATUS_TO_PRIORITY[status],
            "trend": trend,
            "trend_label": {
                "rising": "Rising ↑",
                "falling": "Falling ↓",
                "stable": "Stable →",
            }[trend],
            "predicted_value_5_min": predicted_value,
            "predicted_status_5_min": predicted_status,
            "predicted_label": predicted_label,
            "history": history_values,
        }
        snapshot[config["legacy_status_key"]] = status_label
        snapshot[f"{sensor_id}_priority"] = STATUS_TO_PRIORITY[status]

    overall_status = max_status(statuses)
    snapshot["history"] = history
    snapshot["sensor_details"] = sensor_details
    snapshot["overall_status"] = overall_status
    snapshot["priority"] = STATUS_TO_PRIORITY[overall_status]
    snapshot["predicted_risk_5_min"] = max_status([item["predicted_status_5_min"] for item in sensor_details.values()])
    snapshot["legacy_severity"] = LEGACY_STATUS[overall_status]
    snapshot["last_updated_label"] = format_relative_update(snapshot.get("timestamp"))
    snapshot["marker"] = STATUS_TO_MARKER[overall_status]
    snapshot["location_meta"] = location_entry
    return snapshot


def build_location_collection(
    latest_sensor_data_by_location: dict[str, dict[str, Any]],
    sensor_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    locations = []
    seen = set()
    source_items = list(latest_sensor_data_by_location.items())
    if not source_items:
        for entry in DEFAULT_LOCATION_CATALOG:
            source_items.append(
                (
                    normalize_location_key(entry["name"]),
                    {
                        "location": entry["name"],
                        "latitude": entry["lat"],
                        "longitude": entry["lng"],
                        "timestamp": iso_now(),
                        **SENSOR_RESET_DEFAULTS,
                    },
                )
            )
    for _, raw_entry in source_items:
        enriched = enrich_snapshot(raw_entry, sensor_history)
        location_key = build_location_key(enriched.get("location"), enriched.get("latitude"), enriched.get("longitude"))
        if location_key in seen:
            continue
        seen.add(location_key)
        locations.append(
            {
                "id": enriched["location_meta"]["id"],
                "name": enriched["location_meta"]["name"],
                "lat": enriched["latitude"],
                "lng": enriched["longitude"],
                "severity": enriched["overall_status"],
                "priority": enriched["priority"],
                "predicted_risk_5_min": enriched["predicted_risk_5_min"],
                "marker_color": enriched["marker"]["color"],
                "marker_blinking": enriched["marker"]["blinking"],
                "last_updated": enriched.get("timestamp"),
                "last_updated_label": enriched["last_updated_label"],
                "sensors": enriched["sensor_details"],
            }
        )
    locations.sort(key=lambda item: STATUS_ORDER[item["severity"]], reverse=True)
    return locations


def build_alert_events(
    previous_snapshot: Optional[dict[str, Any]],
    current_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    events = []
    current_time = current_snapshot.get("timestamp") or iso_now()

    previous_overall = (previous_snapshot or {}).get("overall_status")
    if previous_overall and previous_overall != current_snapshot["overall_status"]:
        events.append(
            {
                "id": str(uuid.uuid4()),
                "kind": "system",
                "scope": "location",
                "sensor_id": "overall",
                "sensor_label": f"{current_snapshot.get('location', 'Location')} Overall Risk",
                "severity": current_snapshot["overall_status"].title(),
                "priority": current_snapshot["priority"],
                "status": "Open",
                "location": current_snapshot.get("location"),
                "latitude": current_snapshot.get("latitude"),
                "longitude": current_snapshot.get("longitude"),
                "note": f"Status changed from {previous_overall.title()} to {current_snapshot['overall_status'].title()}",
                "created_at": current_time,
                "updated_at": current_time,
            }
        )

    for sensor_id, detail in current_snapshot.get("sensor_details", {}).items():
        previous_detail = ((previous_snapshot or {}).get("sensor_details") or {}).get(sensor_id, {})
        previous_status = previous_detail.get("status")
        if previous_status == detail["status"]:
            continue
        if previous_status is None and detail["status"] == "SAFE":
            continue
        events.append(
            {
                "id": str(uuid.uuid4()),
                "kind": "system",
                "scope": "sensor",
                "sensor_id": sensor_id,
                "sensor_label": detail["label"],
                "severity": detail["status"].title(),
                "priority": detail["priority"],
                "status": "Open",
                "location": current_snapshot.get("location"),
                "latitude": current_snapshot.get("latitude"),
                "longitude": current_snapshot.get("longitude"),
                "value": detail["value"],
                "trend": detail["trend"],
                "predicted_status_5_min": detail["predicted_status_5_min"].title(),
                "note": (
                    f"{detail['label']} moved from {(previous_status or 'SAFE').title()} to {detail['status'].title()}"
                    if previous_status
                    else f"{detail['label']} entered {detail['status'].title()} state"
                ),
                "created_at": current_time,
                "updated_at": current_time,
            }
        )
    return events


def build_history_rows(
    sensor_history: list[dict[str, Any]],
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    desired_key = build_location_key(location, latitude, longitude) if (location or latitude is not None or longitude is not None) else None
    rows = sensor_history
    if desired_key:
        rows = [
            item
            for item in sensor_history
            if build_location_key(item.get("location"), safe_float(item.get("latitude")), safe_float(item.get("longitude"))) == desired_key
        ]
    sliced = rows[-limit:]
    return [enrich_snapshot(item, sensor_history) for item in sliced]


def build_live_payload(
    latest_sensor_data_by_location: dict[str, dict[str, Any]],
    sensor_history: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict[str, Any]:
    selected = None
    desired_key = build_location_key(location, latitude, longitude) if (location or latitude is not None or longitude is not None) else None
    if desired_key and desired_key in latest_sensor_data_by_location:
        selected = latest_sensor_data_by_location[desired_key]
    elif location:
        normalized = normalize_location_key(location)
        for item in latest_sensor_data_by_location.values():
            if normalize_location_key(item.get("location")) == normalized:
                selected = item
                break
    elif latest_sensor_data_by_location:
        selected = next(iter(latest_sensor_data_by_location.values()))

    if selected is None:
        seed = DEFAULT_LOCATION_CATALOG[0]
        selected = {
            "location": seed["name"],
            "latitude": seed["lat"],
            "longitude": seed["lng"],
            "timestamp": iso_now(),
            **SENSOR_RESET_DEFAULTS,
        }

    snapshot = enrich_snapshot(selected, sensor_history)
    return {
        "success": True,
        "snapshot": snapshot,
        "locations": build_location_collection(latest_sensor_data_by_location, sensor_history),
        "alerts": alerts[-25:][::-1],
        "meta": {
            "sensor_refresh_seconds": 10,
            "weather_refresh_seconds": 300,
            "alerts_mode": "polling_or_websocket_ready",
        },
    }


def apply_admin_action(
    alerts: list[dict[str, Any]],
    alert_id: str,
    assigned_department: Optional[str] = None,
    resolved: bool = False,
) -> Optional[dict[str, Any]]:
    for alert in alerts:
        if str(alert.get("id")) != str(alert_id):
            continue
        if assigned_department:
            alert["assigned_department"] = assigned_department
        if resolved:
            alert["status"] = "Resolved"
        alert["updated_at"] = iso_now()
        return alert
    return None


def force_reset_snapshot(
    latest_sensor_data_by_location: dict[str, dict[str, Any]],
    sensor_history: list[dict[str, Any]],
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict[str, Any]:
    desired_key = build_location_key(location, latitude, longitude)
    current = latest_sensor_data_by_location.get(desired_key, {})
    reset = {
        **current,
        "location": current.get("location") or location or "Monitored Zone",
        "latitude": safe_float(current.get("latitude")) or latitude,
        "longitude": safe_float(current.get("longitude")) or longitude,
        "timestamp": iso_now(),
        "noise_level": SENSOR_RESET_DEFAULTS["noise_level"],
        "flood_level": SENSOR_RESET_DEFAULTS["flood_level"],
        "bin_fill": SENSOR_RESET_DEFAULTS["bin_fill"],
        "light_percent": SENSOR_RESET_DEFAULTS["light_percent"],
        "fire_smoke": SENSOR_RESET_DEFAULTS["fire_smoke"],
    }
    latest_sensor_data_by_location[desired_key] = reset
    sensor_history.append(reset)
    return reset
