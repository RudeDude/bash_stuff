#!/usr/bin/env python3
"""
NTP Pool Scanner – Ubuntu Optimized (Fixed hop count + leaderboard)
Now reliably shows the leaderboard even if some hops are N/A.
"""

import socket
import subprocess
import re
import time
import argparse
import shutil


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
    """Try ICMP traceroute, then fall back to UDP. Returns hop count or None."""
    for use_icmp in [True, False]:
        try:
            cmd = ["traceroute", "-n", "-q", "1", "-m", str(max_hops), "-w", "2"]
            if use_icmp:
                cmd.append("-I")
            cmd.append(ip)

            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, timeout=35
            ).decode("utf-8", errors="ignore")

            # Best: line that contains the target IP
            pattern = r"^\s*(\d+)\s+.*?" + re.escape(ip)
            match = re.search(pattern, output, re.MULTILINE)
            if match:
                return int(match.group(1))

            # Fallback: last hop number shown (works even if final probe is blocked)
            hop_matches = re.findall(r"^\s*(\d+)", output, re.MULTILINE)
            if hop_matches:
                return int(hop_matches[-1])

        except Exception:
            continue  # try the other method (ICMP ↔ UDP)
    return None


def main():
    parser = argparse.ArgumentParser(description="NTP closest server finder – Ubuntu fixed")
    parser.add_argument("--hostname", default="us.pool.ntp.org", help="NTP pool hostname")
    parser.add_argument("--sleep", type=int, default=15, help="Sleep between cycles (seconds)")
    parser.add_argument("--pings", type=int, default=3, help="Pings per IP")
    args = parser.parse_args()

    if not shutil.which("traceroute"):
        print("❌ 'traceroute' command not found.")
        print("   Install it with: sudo apt update && sudo apt install traceroute -y")
        return

    print(f"🚀 NTP Scanner started for {args.hostname}")
    print(f"   Sleep: {args.sleep}s | Pings: {args.pings}")
    print("   Press Ctrl+C to stop.\n")

    best_results = {}  # ip → {'rtt': float, 'hops': int|None, 'seen': int}

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

                # Store result as long as we have RTT (hops optional)
                if rtt is not None:
                    if ip not in best_results or rtt < best_results[ip]["rtt"]:
                        best_results[ip] = {
                            "rtt": rtt,
                            "hops": hops,
                            "seen": 1
                        }
                    else:
                        best_results[ip]["seen"] += 1

            # Show leaderboard (works even if some hops are N/A)
            if best_results:
                sorted_best = sorted(
                    best_results.items(),
                    key=lambda x: (x[1]["rtt"], x[1]["hops"] or 999)
                )
                print("\n🏆 Top 10 best NTP servers so far (by RTT, then hops):")
                for rank, (ip, data) in enumerate(sorted_best[:10], 1):
                    hops_display = str(data["hops"]) if data["hops"] is not None else "N/A"
                    print(f"   {rank:2d}. {ip:15} | RTT: {data['rtt']:6.1f} ms | "
                          f"Hops: {hops_display:>3} | Seen: {data['seen']}×")
            else:
                print("   (No successful RTT measurements yet)")

            print(f"   Sleeping {args.sleep} seconds before next cycle...\n")
            time.sleep(args.sleep)

    except KeyboardInterrupt:
        print("\n\n✅ Stopped by user. Happy time-syncing! ⏰")


if __name__ == "__main__":
    main()

