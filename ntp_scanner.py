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
import glob


DATA_FILE = "ntp_best_servers.json"
CHRONY_CONF_CANDIDATES = ("/etc/chrony/chrony.conf", "/etc/chrony.conf")
SERVER_RE = re.compile(r"^\s*#?\s*server\s+(\S+)", re.IGNORECASE)
CONFDIR_RE = re.compile(r"^\s*#?\s*confdir\s+(\S+)", re.IGNORECASE)
SOURCEDIR_RE = re.compile(r"^\s*#?\s*sourcedir\s+(\S+)", re.IGNORECASE)
IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
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


POOL_HOST_RE = re.compile(r"^(?:(\d+)\.)?([a-z0-9-]+)\.pool\.ntp\.org\.?$", re.IGNORECASE)


def pool_hostnames(hostname, expand_pool=True):
    """
    NTP pool DNS returns ~4 A records per name. Expand zone.pool.ntp.org into
    0–3.zone.pool.ntp.org (plus the zone itself) for many more unique peers.
    """
    if not expand_pool:
        return [hostname]
    m = POOL_HOST_RE.match(hostname)
    if not m or m.group(1) is not None:
        return [hostname]
    zone = m.group(2)
    return [hostname] + [f"{i}.{zone}.pool.ntp.org" for i in range(4)]


def get_ntp_ips(hostname="us.pool.ntp.org", tries=40, expand_pool=True):
    """Resolve pool hostname(s) repeatedly; rotate subdomains for more unique IPs."""
    hosts = pool_hostnames(hostname, expand_pool)
    ips = set()
    for i in range(tries):
        host = hosts[i % len(hosts)]
        try:
            addrs = socket.getaddrinfo(host, "123", family=socket.AF_INET)
            for addr in addrs:
                ips.add(addr[4][0])
        except OSError:
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


def run_chronyc(args):
    if not shutil.which("chronyc"):
        return None
    try:
        return subprocess.check_output(
            ["chronyc"] + args, stderr=subprocess.STDOUT, timeout=10
        ).decode(errors="ignore")
    except Exception:
        return None


def parse_chrony_sources(text):
    """Parse `chronyc -n sources` into {ip: {state, stratum, reach, sample, ...}}."""
    sources = {}
    for line in text.splitlines():
        if not line or line.startswith("MS ") or line.startswith("==="):
            continue
        m = re.match(
            r"^(?P<state>\S+)\s+(?P<name>\S+)\s+"
            r"(?P<stratum>\d+)\s+(?P<poll>\d+)\s+(?P<reach>\d+)\s+(?P<last_rx>\d+)\s+"
            r"(?P<sample>.+)$",
            line,
        )
        if m:
            sources[m.group("name")] = m.groupdict()
    return sources


def find_chrony_conf_file():
    for path in CHRONY_CONF_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


def chrony_conf_files(conf_path=None):
    """Collect main chrony.conf plus active confdir/sourcedir snippets."""
    main = conf_path or find_chrony_conf_file()
    if not main:
        return []
    files = [main]
    extra_dirs = []
    try:
        with open(main, "r") as f:
            for line in f:
                if line.lstrip().startswith("#"):
                    continue
                m = CONFDIR_RE.match(line) or SOURCEDIR_RE.match(line)
                if m:
                    extra_dirs.append(m.group(1))
    except OSError:
        return files
    for directory in extra_dirs:
        files.extend(sorted(glob.glob(os.path.join(directory, "*.conf"))))
    return files


def parse_chrony_conf_excluded_ips(conf_path=None):
    """IPs from server lines in chrony config (including commented-out lines)."""
    excluded_ips = set()
    hostnames = set()
    for path in chrony_conf_files(conf_path):
        try:
            with open(path, "r") as f:
                for line in f:
                    m = SERVER_RE.match(line)
                    if not m:
                        continue
                    host = m.group(1).split("#")[0].strip()
                    if IPV4_RE.match(host):
                        excluded_ips.add(host)
                    else:
                        hostnames.add(host)
        except OSError:
            continue
    for host in hostnames:
        try:
            addrs = socket.getaddrinfo(host, "123", family=socket.AF_INET)
            for addr in addrs:
                excluded_ips.add(addr[4][0])
        except OSError:
            pass
    return excluded_ips


def parse_chrony_sourcestats(text):
    """Parse `chronyc -n sourcestats` into {name_or_ip: {offset, std_dev, ...}}."""
    stats = {}
    for line in text.splitlines():
        if not line or line.startswith("Name/") or line.startswith("==="):
            continue
        m = re.match(
            r"^(?P<name>\S+)\s+(?P<np>\d+)\s+(?P<nr>\d+)\s+(?P<span>\d+)\s+"
            r"(?P<freq>[\d.+-]+)\s+(?P<skew>[\d.+-]+)\s+(?P<offset>\S+)\s+(?P<stddev>\S+)",
            line,
        )
        if m:
            stats[m.group("name")] = m.groupdict()
    return stats


def sorted_measured(best_results):
    measured = {ip: d for ip, d in best_results.items() if d.get("rtt") is not None}
    return sorted(
        measured.items(),
        key=lambda x: (x[1]["rtt"] or 999, x[1]["hops"] or 999),
    )


def print_top_servers(best_results, n=20):
    ranked = sorted_measured(best_results)
    if not ranked:
        print("   (No successful RTT measurements yet)")
        return
    print(f"\n🏆 Top {n} best NTP servers so far (by RTT, then hops):")
    for rank, (ip, data) in enumerate(ranked[:n], 1):
        hops_display = str(data["hops"]) if data["hops"] is not None else "N/A"
        method = data.get("rtt_method", "ping")
        tests = get_test_count(data)
        print(
            f"   {rank:2d}. {ip:15} | RTT: {data['rtt']:6.1f} ms ({method}) | "
            f"Hops: {hops_display:>3} | Seen: {data['seen']}× | Tests: {tests}"
        )


def print_shutdown_chrony_report(best_results):
    """Compare scanner results with active chrony sources on exit."""
    print_top_servers(best_results, 20)

    sources_text = run_chronyc(["-n", "sources"])
    if not sources_text:
        print("\n⚠️  chronyc unavailable; skipping chrony comparison.")
        return

    sources = parse_chrony_sources(sources_text)
#    stats = parse_chrony_sourcestats(run_chronyc(["-n", "sourcestats"]) or "")
    measured = dict(sorted_measured(best_results))
    chrony_ips = set(sources)

    overlap = [ip for ip in chrony_ips if ip in measured]
    if overlap:
        print("\n⏱️  Chrony sources in scanner results (clock stats + scanner RTT):")
        for ip in sorted(overlap, key=lambda i: measured[i]["rtt"]):
            src = sources[ip]
            #st = stats.get(ip, {})
            data = measured[ip]
            state = src.get("state", "?")
            sample = src.get("sample", "N/A")
            method = data.get("rtt_method", "ping")
            print(f"   {ip:15} [{state}]  scanner RTT: {data['rtt']:.1f} ms ({method})")
            print(f"      sources: stratum {src.get('stratum')} | reach {src.get('reach')} | {sample}")
#            if st:
#                print(
#                    f"      sourcestats: offset {st.get('offset')} | std dev {st.get('stddev')} | "
#                    f"freq {st.get('freq')} ppm | skew {st.get('skew')} ppm | "
#                    f"span {st.get('span')}s (NP {st.get('np')}, NR {st.get('nr')})"
#                )
#            else:
#                print("      sourcestats: (no entry)")
    else:
        print("\n   (No chrony sources overlap with scanner results)")

    conf_excluded = parse_chrony_conf_excluded_ips()
    excluded_ips = chrony_ips | conf_excluded
    unused = [(ip, d) for ip, d in sorted_measured(best_results) if ip not in excluded_ips]
    conf_note = ""
    if conf_excluded:
        conf_note = f" ({len(conf_excluded)} from chrony.conf, incl. commented)"
    print(f"\n💡 Top 8 scanner RTTs not used by chrony{conf_note}:")
    if not unused:
        print("   (none — remaining scanner hits are active or listed in chrony.conf)")
        return
    for rank, (ip, data) in enumerate(unused[:8], 1):
        hops_display = str(data["hops"]) if data["hops"] is not None else "N/A"
        method = data.get("rtt_method", "ping")
        print(
            f"   {rank}. {ip:15} | RTT: {data['rtt']:6.1f} ms ({method}) | Hops: {hops_display:>3}"
        )


def main():
    parser = argparse.ArgumentParser(description="NTP closest server finder – persistent data")
    parser.add_argument("--hostname", default="us.pool.ntp.org", help="NTP pool hostname")
    parser.add_argument(
        "--resolve-tries",
        type=int,
        default=40,
        help="DNS lookups per cycle (rotates pool subdomains 0–3)",
    )
    parser.add_argument(
        "--no-pool-expand",
        action="store_true",
        help="Only resolve --hostname (no 0–3.pool subdomain expansion)",
    )
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

    pool_hosts = pool_hostnames(args.hostname, expand_pool=not args.no_pool_expand)
    print(f"🚀 NTP Scanner started for {args.hostname}")
    print(
        f"   Resolve: {args.resolve_tries} lookups across {len(pool_hosts)} name(s) | "
        f"Pings: {args.pings} | Persistent file: {DATA_FILE}"
    )
    if len(pool_hosts) > 1:
        print(f"   Pool names: {', '.join(pool_hosts)}")
    print("   Press Ctrl+C to stop.\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"─── Iteration {iteration} ───")

            ips = get_ntp_ips(
                args.hostname,
                tries=args.resolve_tries,
                expand_pool=not args.no_pool_expand,
            )
            pollable = sum(
                1
                for ip in ips
                if get_test_count(best_results.get(ip, {})) < MAX_TESTS_PER_IP
            )
            print(
                f"   Resolved {len(ips)} unique IP(s) "
                f"({pollable} still under {MAX_TESTS_PER_IP} tests)"
            )

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

            print_top_servers(best_results, 20)

            print(f"   💾 Saved {len(best_results)} entries to {DATA_FILE}")
            print(f"   Sleeping {args.sleep} seconds before next cycle...\n")
            time.sleep(args.sleep)

    except KeyboardInterrupt:
        save_results(best_results)
        print("\n\n✅ Stopped by user. Data saved!")
        print_shutdown_chrony_report(best_results)
        print("Happy time-syncing! ⏰")


if __name__ == "__main__":
    main()

