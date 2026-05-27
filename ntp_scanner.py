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


def measure_hops(ip, max_hops=64):
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
                print(f"   {ip:15} → ", end="")
                rtt = measure_rtt(ip, args.pings)
                hops = measure_hops(ip)

                rtt_str = f"{rtt:.1f}ms" if rtt is not None else "N/A"
                hops_str = str(hops) if hops is not None else "N/A"
                print(f" RTT: {rtt_str:>6} | Hops: {hops_str:>3}")

                if rtt is not None:
                    if ip not in best_results or rtt < best_results[ip]["rtt"]:
                        best_results[ip] = {
                            "rtt": rtt,
                            "hops": hops,
                            "seen": 1
                        }
                    else:
                        best_results[ip]["seen"] += 1

            # Save after every cycle
            save_results(best_results)

            # Show leaderboard
            if best_results:
                sorted_best = sorted(
                    best_results.items(),
                    key=lambda x: (x[1]["hops"], x[1]["rtt"] or 999)
#                    key=lambda x: (x[1]["rtt"], x[1]["hops"] or 999)
                )
                print("\n🏆 Top 20 best NTP servers so far (by RTT, then hops):")
                for rank, (ip, data) in enumerate(sorted_best[:20], 1):
                    hops_display = str(data["hops"]) if data["hops"] is not None else "N/A"
                    print(f"   {rank:2d}. {ip:15} | RTT: {data['rtt']:6.1f} ms | "
                          f"Hops: {hops_display:>3} | Seen: {data['seen']}×")
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

