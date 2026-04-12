import argparse
import os
import re
import socket
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ModuleNotFoundError:
    serial = None

try:
    import requests
except ModuleNotFoundError:
    requests = None

DEFAULT_BAUD_RATE = 115200
DEFAULT_API_URL = "http://127.0.0.1:8000/iot/data"
DEFAULT_LOG_URL = "http://127.0.0.1:8000/iot/log"
DEFAULT_PUSH_INTERVAL = 10

# Keep parser state for section-aware fields like Status and Distance.
prev_section = ""


def find_wokwi_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Found port: {port.device} - {port.description}")
        desc = (port.description or "").lower()
        if "wokwi" in desc or "uart" in desc:
            return port.device
    if ports:
        return ports[0].device
    return None


def list_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports detected.")
        return
    print("Detected serial ports:")
    for port in ports:
        print(f"- {port.device}: {port.description}")


def parse_host_port(value):
    parts = value.rsplit(":", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("TCP endpoint must be in host:port format")
    host = parts[0].strip()
    if not host:
        raise argparse.ArgumentTypeError("TCP host cannot be empty")
    try:
        port = int(parts[1].strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("TCP port must be a number") from exc
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError("TCP port must be between 1 and 65535")
    return host, port


def parse_line(line, data):
    line = line.strip()
    line_upper = line.upper()
    current_section = prev_section.upper()

    def field_value(label):
        pattern = rf"^{re.escape(label)}\s*:\s*(.+)$"
        match = re.search(pattern, line, flags=re.IGNORECASE)
        return match.group(1).strip() if match else None

    def first_int(text):
        match = re.search(r"-?\d+", text or "")
        return int(match.group()) if match else None

    def first_float(text):
        match = re.search(r"-?\d+(?:\.\d+)?", text or "")
        return float(match.group()) if match else None
    distance_val = field_value("Distance")
    if distance_val and "CM" in line_upper:
        parsed = first_float(distance_val)
        if parsed is not None:
            if "FLOOD" in prev_section:
                data["flood_distance"] = parsed
            elif "BIN" in prev_section or "WASTE" in prev_section:
                data["bin_distance"] = parsed

    level_val = field_value("Level")
    if level_val and "%" in level_val:
        parsed = first_int(level_val)
        if parsed is not None:
            data["flood_level"] = parsed
    if level_val and "DB" in level_val.upper():
        parsed = first_int(level_val)
        if parsed is not None:
            data["noise_level"] = parsed

    smoke_val = field_value("Smoke")
    if smoke_val and "%" in smoke_val:
        parsed = first_int(smoke_val)
        if parsed is not None:
            if "FIRE" in prev_section:
                data["fire_smoke"] = parsed
            else:
                data["air_smoke"] = parsed

    temp_val = field_value("Temp")
    if temp_val and "C" in temp_val.upper():
        parsed = first_float(temp_val)
        if parsed is not None:
            # Only the dedicated temperature section should drive the dashboard
            # temperature card. Some other sections print helper temperatures too.
            if "TEMP" in current_section or "HUMIDITY" in current_section:
                data["temperature"] = parsed

    humidity_val = field_value("Humidity")
    if humidity_val and "%" in humidity_val:
        parsed = first_float(humidity_val)
        if parsed is not None:
            data["humidity"] = parsed

    lane1_val = field_value("Lane 1")
    if lane1_val is not None:
        parsed = first_int(lane1_val)
        if parsed is not None:
            data["traffic_lane1"] = parsed

    lane2_val = field_value("Lane 2")
    if lane2_val is not None:
        parsed = first_int(lane2_val)
        if parsed is not None:
            data["traffic_lane2"] = parsed

    total_val = field_value("Total")
    if total_val is not None:
        parsed = first_int(total_val)
        if parsed is not None:
            data["traffic_total"] = parsed

    light_val = field_value("Light")
    if light_val and "%" in light_val:
        parsed = first_int(light_val)
        if parsed is not None:
            data["light_percent"] = parsed

    fill_val = field_value("Fill")
    if fill_val and "%" in fill_val:
        parsed = first_int(fill_val)
        if parsed is not None:
            data["bin_fill"] = parsed

    rain_val = field_value("Rain")
    if rain_val and "%" in rain_val:
        parsed = first_int(rain_val)
        if parsed is not None:
            data["rain_percent"] = parsed

    spot_a_val = field_value("Spot A")
    if spot_a_val is not None:
        data["parking_a"] = spot_a_val

    spot_b_val = field_value("Spot B")
    if spot_b_val is not None:
        data["parking_b"] = spot_b_val

    available_val = field_value("Available")
    if available_val is not None:
        parsed = first_int(available_val)
        if parsed is not None:
            data["parking_available"] = parsed

    status_val = field_value("Status")
    if status_val is not None:
        if "FLOOD" in prev_section or "WATER" in prev_section:
            data["flood_status"] = status_val
        elif "AIR" in prev_section:
            data["air_status"] = status_val
        elif "TEMP" in prev_section or "HUMIDITY" in prev_section:
            data["temp_status"] = status_val
        elif "TRAFFIC" in prev_section:
            data["traffic_status"] = status_val
        elif "NOISE" in prev_section:
            data["noise_status"] = status_val
        elif "STREET" in prev_section or "LIGHT" in prev_section:
            data["light_status"] = status_val
        elif "WASTE" in prev_section or "BIN" in prev_section:
            data["bin_status"] = status_val
        elif "RAIN" in prev_section:
            data["rain_status"] = status_val
        elif "FIRE" in prev_section or "SMOKE" in prev_section:
            data["fire_status"] = status_val
        elif "PARKING" in prev_section:
            data["parking_status"] = status_val

    return data


def send_data_to_backend(data, api_url):
    print("\n Sending data to backend...")
    try:
        response = requests.post(api_url, json=data, timeout=5)
        if response.status_code == 200:
            print(" Data sent successfully!")
        else:
            print(f" Backend error: {response.status_code} - {response.text}")
    except Exception as exc:
        print(f" Could not reach backend: {exc}")
    print("\nWaiting for next report...\n")


def send_line_to_backend(line, log_url):
    try:
        requests.post(log_url, json={"line": line}, timeout=3)
    except Exception:
        pass


def maybe_auto_send(data, api_url, last_sent_at, push_interval):
    if push_interval <= 0:
        return last_sent_at
    if not data:
        return last_sent_at
    # Structured Wokwi reports include an explicit END OF REPORT marker.
    # Avoid posting partial snapshots mid-report because they can momentarily
    # desync frontend cards when only some sections have arrived.
    required_report_fields = (
        "temperature",
        "humidity",
        "air_smoke",
        "rain_percent",
        "traffic_total",
        "noise_level",
        "light_percent",
        "bin_fill",
    )
    if not any(key in data for key in required_report_fields):
        return last_sent_at
    if sum(1 for key in required_report_fields if key in data) < 6:
        return last_sent_at
    now = time.time()
    if now - last_sent_at >= push_interval:
        send_data_to_backend(data, api_url)
        return now
    return last_sent_at


def process_line(line, data, api_url, log_url):
    global prev_section

    line = line.strip()
    if not line:
        return data, False

    print(f"  >> {line}")
    send_line_to_backend(line, log_url)

    for keyword in [
        "FLOOD", "WATER", "AIR QUALITY", "TEMPERATURE",
        "TRAFFIC", "NOISE", "STREET", "WASTE", "RAIN",
        "FIRE", "PARKING",
    ]:
        if keyword in line.upper():
            prev_section = line.upper()
            break

    data = parse_line(line, data)

    if "END OF REPORT" in line.upper():
        send_data_to_backend(data, api_url)
        return {}, True

    return data, False


def run_stdin_mode(api_url, log_url, push_interval):
    print("Reading sensor lines from stdin...")
    print("Tip: pipe Wokwi/bridge logs into this process.")
    data = {}
    last_sent_at = 0.0
    try:
        for line in sys.stdin:
            data, was_sent = process_line(line, data, api_url, log_url)
            if was_sent:
                last_sent_at = time.time()
            else:
                last_sent_at = maybe_auto_send(data, api_url, last_sent_at, push_interval)
    except KeyboardInterrupt:
        pass
    print("\nStopped by user.")


def run_tcp_mode(api_url, log_url, tcp_endpoint, push_interval):
    host, tcp_port = parse_host_port(tcp_endpoint)
    print(f"TCP endpoint: {host}:{tcp_port}")
    while True:
        try:
            with socket.create_connection((host, tcp_port), timeout=10) as sock:
                print("Connected! Listening for sensor data...")
                reader = sock.makefile("r", encoding="utf-8", errors="ignore")
                data = {}
                last_sent_at = 0.0
                while True:
                    line = reader.readline()
                    if not line:
                        raise ConnectionError("TCP stream closed")
                    data, was_sent = process_line(line, data, api_url, log_url)
                    if was_sent:
                        last_sent_at = time.time()
                    else:
                        last_sent_at = maybe_auto_send(data, api_url, last_sent_at, push_interval)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as exc:
            if isinstance(exc, ConnectionRefusedError) or getattr(exc, "winerror", None) == 10061:
                print(f"TCP source disconnected: {exc}")
                print("No TCP producer is running on that host:port.")
                print("Use --source stdin for Wokwi simulator mode, or start your TCP bridge first.")
                break
            print(f"TCP source disconnected: {exc}")
            print("Retrying in 3 seconds...")
            time.sleep(3)


def run_tcp_server_mode(api_url, log_url, listen_endpoint, push_interval):
    host, tcp_port = parse_host_port(listen_endpoint)
    print(f"TCP server listening on {host}:{tcp_port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((host, tcp_port))
        server_sock.listen(5)
        while True:
            try:
                client_sock, addr = server_sock.accept()
                with client_sock:
                    print(f"TCP client connected: {addr[0]}:{addr[1]}")
                    reader = client_sock.makefile("r", encoding="utf-8", errors="ignore")
                    data = {}
                    last_sent_at = 0.0
                    while True:
                        line = reader.readline()
                        if not line:
                            print("TCP client disconnected.")
                            break
                        data, was_sent = process_line(line, data, api_url, log_url)
                        if was_sent:
                            last_sent_at = time.time()
                        else:
                            last_sent_at = maybe_auto_send(data, api_url, last_sent_at, push_interval)
            except KeyboardInterrupt:
                print("\nStopped by user.")
                break


def run_serial_mode(api_url, log_url, baud, manual_port, push_interval):
    if serial is None:
        print("Missing dependency: pyserial")
        print("Install with: pip install pyserial")
        return

    print(f"Baud rate: {baud}")
    port = manual_port
    if not port:
        print("Looking for Wokwi serial port...")
        port = find_wokwi_port()

    if not port:
        print("No serial port found! Make sure device/bridge is running.")
        print("Tip: run with --source stdin or --source tcp for simulator mode.")
        print("Tip: run with --port COMx if auto-detect cannot find the device.")
        print("Tip: for Wokwi forwarding use --port rfc2217://127.0.0.1:4000")
        return

    print(f"Connecting to port: {port}")
    while True:
        try:
            if "://" in port:
                ser = serial.serial_for_url(port, baudrate=baud, timeout=2)
            else:
                ser = serial.Serial(port, baud, timeout=2)

            with ser:
                print("Connected! Listening for sensor data...")
                data = {}
                last_sent_at = 0.0
                while True:
                    raw = ser.readline()
                    try:
                        line = raw.decode("utf-8", errors="ignore")
                    except Exception:
                        continue
                    data, was_sent = process_line(line, data, api_url, log_url)
                    if was_sent:
                        last_sent_at = time.time()
                    else:
                        last_sent_at = maybe_auto_send(data, api_url, last_sent_at, push_interval)
        except serial.SerialException as exc:
            print(f"Serial disconnected: {exc}")
            print("Retrying in 3 seconds...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break


def main():
    if requests is None:
        print("Missing dependency: requests")
        print("Install with: pip install requests")
        return

    parser = argparse.ArgumentParser(description="Urban Sentinel serial-to-API bridge")
    parser.add_argument(
        "--source",
        choices=["serial", "stdin", "tcp", "tcp-server"],
        default=os.getenv("IOT_SOURCE", "serial"),
        help="Input source mode",
    )
    parser.add_argument("--port", default=os.getenv("SERIAL_PORT"), help="Serial port (example: COM5)")
    parser.add_argument("--baud", type=int, default=int(os.getenv("SERIAL_BAUD", DEFAULT_BAUD_RATE)))
    parser.add_argument("--api-url", default=os.getenv("IOT_API_URL", DEFAULT_API_URL))
    parser.add_argument("--log-url", default=os.getenv("IOT_LOG_URL", DEFAULT_LOG_URL))
    parser.add_argument(
        "--push-interval",
        type=int,
        default=int(os.getenv("IOT_PUSH_INTERVAL", DEFAULT_PUSH_INTERVAL)),
        help="Auto-post interval in seconds (0 disables interval posts)",
    )
    parser.add_argument(
        "--tcp",
        default=os.getenv("IOT_TCP", "127.0.0.1:9010"),
        help="TCP endpoint for --source tcp (host:port)",
    )
    parser.add_argument(
        "--listen",
        default=os.getenv("IOT_LISTEN", "0.0.0.0:9010"),
        help="TCP listen endpoint for --source tcp-server (host:port)",
    )
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    args = parser.parse_args()

    if args.list_ports:
        if serial is None:
            print("pyserial is not installed; cannot enumerate serial ports.")
            print("Install with: pip install pyserial")
            return
        list_ports()
        return

    print("Urban Sentinel Serial Reader")
    print(f"Source mode: {args.source}")
    print(f"API endpoint: {args.api_url}")
    print(f"Log endpoint: {args.log_url}")
    print(f"Auto push interval: {args.push_interval}s")

    if args.source == "stdin":
        run_stdin_mode(args.api_url, args.log_url, args.push_interval)
    elif args.source == "tcp":
        run_tcp_mode(args.api_url, args.log_url, args.tcp, args.push_interval)
    elif args.source == "tcp-server":
        run_tcp_server_mode(args.api_url, args.log_url, args.listen, args.push_interval)
    else:
        run_serial_mode(args.api_url, args.log_url, args.baud, args.port, args.push_interval)


if __name__ == "__main__":
    main()
