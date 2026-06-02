#!/usr/bin/env python3
"""
NTP Pool Scanner – Ubuntu Optimized + Persistent Data
Saves accumulated best servers across runs (ntp_best_servers.json)
"""

import socket
import subprocess
import re
import time
import argparse
import shutil
import json
import os


DATA_FILE = "ntp_best_servers.json"
MAX_TESTS_PER_IP = 10
MAX_HOPS = 64
NTP_PORT = 123


def load_results(filename=DATA_FILE):
    """Load previously saved best results from JSON."""
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} previously measured servers from {filename}")
        return data
    except Exception as e:
        print(f"⚠️  Could not load {filename} (starting fresh): {e}")
        return {}


def save_results(best_results, filename=DATA_FILE):
    """Save current best results to JSON."""
    try:
        with open(filename, "w") as f:
            json.dump(best_results, f, indent=2)
    except Exception:
        print(f"⚠️  Could not save to {filename} (data still in memory)")


def get_ntp_ips(hostname="us.pool.ntp.org", tries=8):
    """Resolve the pool multiple times for fresh IPs."""
    ips = set()
    for _ in range(tries):
        try:
            addrs = socket.getaddrinfo(hostname, "123", family=socket.AF_INET)
            for addr in addrs:
                ips.add(addr[4][0])
        except Exception:
            pass
    return list(ips)


def get_test_count(entry):
    """How many times this IP has been measured (persisted across runs)."""
    return int(entry.get("tests", entry.get("seen", 0)))


def ensure_ip_entry(best_results, ip):
    if ip not in best_results:
        best_results[ip] = {"rtt": None, "hops": None, "seen": 0, "tests": 0}
    elif "tests" not in best_results[ip]:
        best_results[ip]["tests"] = get_test_count(best_results[ip])


def needs_ntp_fallback(rtt, hops, max_hops=MAX_HOPS):
    """Ping failed and traceroute hit the hop limit without reaching the host."""
    return rtt is None and hops is not None and hops >= max_hops


def measure_ntp_rtt(ip, timeout=3.0):
    """
    Estimate round-trip delay with one NTP client request (UDP port 123).
    A single 48-byte packet is standard client behavior and is gentle on servers.
    """
    packet = b"\x1b" + 47 * b"\0"  # NTPv4 client mode (LI=0, VN=4, Mode=3)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            t0 = time.perf_counter()
            sock.sendto(packet, (ip, NTP_PORT))
            sock.recvfrom(1024)
            t1 = time.perf_counter()
            return (t1 - t0) * 1000.0
    except Exception:
        pass

    if shutil.which("ntpdate"):
        try:
            out = subprocess.check_output(
                ["ntpdate", "-q", ip],
                stderr=subprocess.STDOUT,
                timeout=timeout + 2,
            ).decode(errors="ignore")
            m = re.search(r"\+\/\- ([\d.]+)", out)
            if m:
                return float(m.group(1)) * 1000.0
        except Exception:
            pass
    return None


def measure_rtt(ip, count=3):
    """Ping and return average RTT in ms."""
    try:
        cmd = ["ping", "-c", str(count), "-W", "2", ip]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=12).decode()
        match = re.search(r"rtt min/avg/max/mdev = .*?/(.*?)/", output)
        if match:
            return float(match.group(1))
        times = re.findall(r"time=([\d.]+) ms", output)
        return sum(float(t) for t in times) / len(times) if times else None
    except Exception:
        return None


def measure_hops(ip, max_hops=MAX_HOPS):
    """Try ICMP traceroute, then fall back to UDP."""
    for use_icmp in [True, False]:
        try:
            cmd = ["traceroute", "-n", "-q", "1", "-m", str(max_hops), "-w", "2"]
            if use_icmp:
                cmd.append("-I")
            cmd.append(ip)

            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, timeout=35
            ).decode("utf-8", errors="ignore")

            # Best: line containing target IP
            pattern = r"^\s*(\d+)\s+.*?" + re.escape(ip)
            match = re.search(pattern, output, re.MULTILINE)
            if match:
                return int(match.group(1))

            # Fallback: last hop shown
            hop_matches = re.findall(r"^\s*(\d+)", output, re.MULTILINE)
            if hop_matches:
                return int(hop_matches[-1])

        except Exception:
            continue
    return None


def main():
    parser = argparse.ArgumentParser(description="NTP closest server finder – persistent data")
    parser.add_argument("--hostname", default="us.pool.ntp.org", help="NTP pool hostname")
    parser.add_argument("--sleep", type=int, default=15, help="Sleep between cycles (seconds)")
    parser.add_argument("--pings", type=int, default=3, help="Pings per IP")
    parser.add_argument("--reset", action="store_true", help="Clear saved data and start fresh")
    args = parser.parse_args()

    if not shutil.which("traceroute"):
        print("❌ 'traceroute' command not found.")
        print("   Install it with: sudo apt update && sudo apt install traceroute -y")
        return

    # Load or reset persistent data
    if args.reset and os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        print("🗑️  Reset: previous saved data cleared.")
    best_results = load_results()

    print(f"🚀 NTP Scanner started for {args.hostname}")
    print(f"   Sleep: {args.sleep}s | Pings: {args.pings} | Persistent file: {DATA_FILE}")
    print("   Press Ctrl+C to stop.\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"─── Iteration {iteration} ───")

            ips = get_ntp_ips(args.hostname)
            print(f"   Resolved {len(ips)} unique IP(s)")

            for ip in ips:
                ensure_ip_entry(best_results, ip)
                if get_test_count(best_results[ip]) >= MAX_TESTS_PER_IP:
                    print(f"   {ip:15} → skipped (tested {MAX_TESTS_PER_IP}+ times)")
                    continue

                print(f"   {ip:15} → ", end="")
                best_results[ip]["tests"] = get_test_count(best_results[ip]) + 1

                rtt = measure_rtt(ip, args.pings)
                hops = measure_hops(ip)
                rtt_method = "ping"

                if needs_ntp_fallback(rtt, hops):
                    ntp_rtt = measure_ntp_rtt(ip)
                    if ntp_rtt is not None:
                        rtt = ntp_rtt
                        rtt_method = "ntp"

                rtt_str = f"{rtt:.1f}ms" if rtt is not None else "N/A"
                hops_str = str(hops) if hops is not None else "N/A"
                method_str = f" [{rtt_method}]" if rtt is not None else ""
                print(f" RTT: {rtt_str:>6}{method_str} | Hops: {hops_str:>3}")

                if rtt is not None:
                    entry = best_results[ip]
                    prev = entry.get("rtt")
                    if prev is None or rtt < prev:
                        entry["rtt"] = rtt
                        entry["hops"] = hops
                        entry["rtt_method"] = rtt_method
                        entry["seen"] = 1
                    else:
                        entry["seen"] = entry.get("seen", 0) + 1
                    if hops is not None and entry.get("hops") is None:
                        entry["hops"] = hops

            # Save after every cycle
            save_results(best_results)

            # Show leaderboard
            measured = {ip: d for ip, d in best_results.items() if d.get("rtt") is not None}
            if measured:
                sorted_best = sorted(
                    measured.items(),
                    key=lambda x: (x[1]["hops"] or 999, x[1]["rtt"] or 999),
                )
                print("\n🏆 Top 20 best NTP servers so far (by hops, then RTT):")
                for rank, (ip, data) in enumerate(sorted_best[:20], 1):
                    hops_display = str(data["hops"]) if data["hops"] is not None else "N/A"
                    method = data.get("rtt_method", "ping")
                    tests = get_test_count(data)
                    print(
                        f"   {rank:2d}. {ip:15} | RTT: {data['rtt']:6.1f} ms ({method}) | "
                        f"Hops: {hops_display:>3} | Seen: {data['seen']}× | Tests: {tests}"
                    )
            else:
                print("   (No successful RTT measurements yet)")

            print(f"   💾 Saved {len(best_results)} entries to {DATA_FILE}")
            print(f"   Sleeping {args.sleep} seconds before next cycle...\n")
            time.sleep(args.sleep)

    except KeyboardInterrupt:
        save_results(best_results)  # final save on exit
        print("\n\n✅ Stopped by user. Data saved! Happy time-syncing! ⏰")


if __name__ == "__main__":
    main()

