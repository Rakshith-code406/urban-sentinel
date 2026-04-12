import argparse
import socket
import sys
import time


def parse_host_port(value: str):
    parts = value.rsplit(":", 1)
    if len(parts) != 2:
        raise ValueError("Endpoint must be host:port")
    host = parts[0].strip()
    port = int(parts[1].strip())
    if not host or port < 1 or port > 65535:
        raise ValueError("Invalid endpoint")
    return host, port


def connect(host: str, port: int):
    while True:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.settimeout(None)
            print(f"[stdin_to_tcp] Connected to {host}:{port}")
            return sock
        except Exception as exc:
            print(f"[stdin_to_tcp] Connect failed: {exc}. Retrying in 2s...")
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="Forward stdin lines to TCP socket")
    parser.add_argument("--tcp", default="127.0.0.1:9010", help="TCP endpoint host:port")
    args = parser.parse_args()

    host, port = parse_host_port(args.tcp)
    sock = connect(host, port)

    try:
        for raw_line in sys.stdin:
            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            payload = f"{line}\n".encode("utf-8", errors="ignore")
            while True:
                try:
                    sock.sendall(payload)
                    break
                except Exception:
                    try:
                        sock.close()
                    except Exception:
                        pass
                    sock = connect(host, port)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
