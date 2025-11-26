"""
DYGSOM Fraud API - Performance Profiling Script

This script profiles the fraud scoring endpoint to identify performance bottlenecks.
Uses cProfile for detailed function-level profiling and generates comprehensive reports.

Usage:
    # Profile a single request
    python performance/profiling/profile_api.py --requests 1

    # Profile 100 requests (realistic load)
    python performance/profiling/profile_api.py --requests 100

    # Profile with custom host
    python performance/profiling/profile_api.py --host http://localhost:3000 --requests 50

    # Generate detailed report with call graph
    python performance/profiling/profile_api.py --requests 100 --detailed

Output:
    - performance/profiling/results/profile_<timestamp>.prof (raw profile data)
    - performance/profiling/results/profile_<timestamp>.txt (human-readable report)
    - performance/profiling/results/hotspots_<timestamp>.txt (top bottlenecks)

Requirements:
    pip install requests snakeviz gprof2dot graphviz
"""

import argparse
import cProfile
import io
import json
import os
import pstats
import random
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import requests


# ============================================================================
# Configuration
# ============================================================================

API_KEY = "dygsom_test_api_key_change_me"
DEFAULT_HOST = "http://localhost:3000"
RESULTS_DIR = Path(__file__).parent / "results"


# ============================================================================
# Test Data Generation
# ============================================================================

def generate_transaction_data() -> Dict[str, Any]:
    """
    Generate realistic transaction data for profiling.

    Returns:
        Dictionary with transaction fields
    """
    return {
        "transaction_id": f"prof-{int(datetime.utcnow().timestamp() * 1000)}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}",
        "customer_email": f"{''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 15)))}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'example.com'])}",
        "customer_ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "amount": round(random.uniform(10.0, 5000.0), 2),
        "currency": random.choice(["USD", "EUR", "PEN", "GBP"]),
        "merchant_id": f"merchant-{random.randint(1, 100)}",
        "card_bin": random.choice(["424242", "400000", "510000", "340000", "370000"]),
        "device_id": f"device-{random.randint(1000, 9999)}",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# API Client
# ============================================================================

class FraudAPIClient:
    """Client for making requests to the Fraud API."""

    def __init__(self, host: str, api_key: str):
        """
        Initialize the API client.

        Args:
            host: Base URL of the API
            api_key: API key for authentication
        """
        self.host = host.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        self.session = requests.Session()

    def score_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a transaction for fraud.

        Args:
            transaction_data: Transaction fields

        Returns:
            API response with fraud score

        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.host}/api/v1/fraud/score"
        response = self.session.post(url, json=transaction_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the session."""
        self.session.close()


# ============================================================================
# Profiling Functions
# ============================================================================

def profile_single_request(client: FraudAPIClient) -> Dict[str, Any]:
    """
    Profile a single fraud scoring request.

    Args:
        client: Fraud API client

    Returns:
        API response
    """
    transaction_data = generate_transaction_data()
    return client.score_transaction(transaction_data)


def profile_multiple_requests(client: FraudAPIClient, num_requests: int) -> List[Dict[str, Any]]:
    """
    Profile multiple fraud scoring requests.

    Args:
        client: Fraud API client
        num_requests: Number of requests to make

    Returns:
        List of API responses
    """
    results = []
    for _ in range(num_requests):
        try:
            result = profile_single_request(client)
            results.append(result)
        except Exception as e:
            print(f"❌ Request failed: {e}", file=sys.stderr)
    return results


# ============================================================================
# Report Generation
# ============================================================================

def generate_profile_report(profile: pstats.Stats, output_file: Path) -> None:
    """
    Generate a human-readable profiling report.

    Args:
        profile: pstats.Stats object
        output_file: Path to save the report
    """
    with open(output_file, 'w') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("DYGSOM Fraud API - Performance Profile Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        f.write("=" * 80 + "\n\n")

        # Redirect stdout to file
        stream = io.StringIO()
        ps = pstats.Stats(profile.stats, stream=stream)

        # Sort by cumulative time
        stream.write("\n" + "=" * 80 + "\n")
        stream.write("TOP 30 FUNCTIONS BY CUMULATIVE TIME\n")
        stream.write("=" * 80 + "\n")
        ps.sort_stats('cumulative')
        ps.print_stats(30)

        # Sort by total time
        stream.write("\n" + "=" * 80 + "\n")
        stream.write("TOP 30 FUNCTIONS BY TOTAL TIME\n")
        stream.write("=" * 80 + "\n")
        ps.sort_stats('tottime')
        ps.print_stats(30)

        # Sort by number of calls
        stream.write("\n" + "=" * 80 + "\n")
        stream.write("TOP 30 MOST CALLED FUNCTIONS\n")
        stream.write("=" * 80 + "\n")
        ps.sort_stats('ncalls')
        ps.print_stats(30)

        # Write callers
        stream.write("\n" + "=" * 80 + "\n")
        stream.write("CALLER/CALLEE RELATIONSHIPS (TOP 20)\n")
        stream.write("=" * 80 + "\n")
        ps.sort_stats('cumulative')
        ps.print_callers(20)

        # Write to file
        f.write(stream.getvalue())

    print(f"✓ Profile report saved to: {output_file}")


def generate_hotspots_report(profile: pstats.Stats, output_file: Path) -> None:
    """
    Generate a focused report on performance hotspots.

    Args:
        profile: pstats.Stats object
        output_file: Path to save the report
    """
    with open(output_file, 'w') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("PERFORMANCE HOTSPOTS - Top Bottlenecks\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        f.write("=" * 80 + "\n\n")

        # Get stats
        stats = profile.stats
        total_time = sum(stat[2] for stat in stats.values())

        # Find hotspots (functions taking >1% of total time)
        hotspots = []
        for func, (cc, nc, tt, ct, callers) in stats.items():
            if tt > total_time * 0.01:  # >1% of total time
                filename, line, func_name = func
                # Filter out stdlib and site-packages
                if 'site-packages' not in filename and '/usr/' not in filename:
                    hotspots.append({
                        'function': f"{filename}:{line}({func_name})",
                        'total_time': tt,
                        'cumulative_time': ct,
                        'calls': nc,
                        'time_per_call': tt / nc if nc > 0 else 0,
                        'pct_total': (tt / total_time) * 100
                    })

        # Sort by total time
        hotspots.sort(key=lambda x: x['total_time'], reverse=True)

        # Write hotspots
        f.write(f"Total profiled time: {total_time:.3f}s\n")
        f.write(f"Hotspot threshold: >{total_time * 0.01:.3f}s (1% of total)\n\n")

        f.write("-" * 80 + "\n")
        f.write(f"{'Function':<50} {'Time (s)':<12} {'% Total':<10} {'Calls':<10}\n")
        f.write("-" * 80 + "\n")

        for hotspot in hotspots:
            f.write(
                f"{hotspot['function'][:50]:<50} "
                f"{hotspot['total_time']:<12.3f} "
                f"{hotspot['pct_total']:<10.2f} "
                f"{hotspot['calls']:<10}\n"
            )

        f.write("-" * 80 + "\n\n")

        # Recommendations
        f.write("=" * 80 + "\n")
        f.write("OPTIMIZATION RECOMMENDATIONS\n")
        f.write("=" * 80 + "\n\n")

        for i, hotspot in enumerate(hotspots[:5], 1):
            f.write(f"{i}. {hotspot['function']}\n")
            f.write(f"   Time: {hotspot['total_time']:.3f}s ({hotspot['pct_total']:.2f}% of total)\n")
            f.write(f"   Calls: {hotspot['calls']}\n")
            f.write(f"   Avg: {hotspot['time_per_call']:.6f}s per call\n")

            # Generate recommendation
            if hotspot['time_per_call'] > 0.01:
                f.write(f"   ⚠️  HIGH LATENCY: Each call takes >{hotspot['time_per_call']*1000:.2f}ms\n")
                f.write("   Action: Profile this function individually, optimize algorithm\n")
            elif hotspot['calls'] > 1000:
                f.write(f"   ⚠️  HIGH CALL COUNT: Called {hotspot['calls']} times\n")
                f.write("   Action: Consider caching, memoization, or batch operations\n")
            else:
                f.write("   Action: Review implementation for optimization opportunities\n")

            f.write("\n")

    print(f"✓ Hotspots report saved to: {output_file}")


def generate_summary_report(
    num_requests: int,
    responses: List[Dict[str, Any]],
    profile_time: float,
    output_file: Path
) -> None:
    """
    Generate a summary report with high-level metrics.

    Args:
        num_requests: Number of requests made
        responses: API responses
        profile_time: Total profiling time
        output_file: Path to save the report
    """
    with open(output_file, 'w') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("PROFILING SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        f.write("=" * 80 + "\n\n")

        # Metrics
        successful_requests = len(responses)
        failed_requests = num_requests - successful_requests
        avg_time = profile_time / num_requests if num_requests > 0 else 0
        throughput = num_requests / profile_time if profile_time > 0 else 0

        f.write(f"Total Requests:       {num_requests}\n")
        f.write(f"Successful:           {successful_requests}\n")
        f.write(f"Failed:               {failed_requests}\n")
        f.write(f"Total Time:           {profile_time:.3f}s\n")
        f.write(f"Avg Time per Request: {avg_time*1000:.2f}ms\n")
        f.write(f"Throughput:           {throughput:.2f} req/s\n\n")

        # Risk level distribution
        if responses:
            risk_levels = {}
            for response in responses:
                level = response.get('risk_level', 'UNKNOWN')
                risk_levels[level] = risk_levels.get(level, 0) + 1

            f.write("-" * 80 + "\n")
            f.write("RISK LEVEL DISTRIBUTION\n")
            f.write("-" * 80 + "\n")
            for level, count in sorted(risk_levels.items()):
                pct = (count / successful_requests) * 100
                f.write(f"{level:<15} {count:>5} ({pct:>5.1f}%)\n")
            f.write("\n")

        # Performance targets
        f.write("-" * 80 + "\n")
        f.write("PERFORMANCE TARGETS\n")
        f.write("-" * 80 + "\n")

        target_p95 = 100  # ms
        target_throughput = 100  # req/s

        avg_time_ms = avg_time * 1000

        f.write(f"Avg Latency:    {avg_time_ms:.2f}ms ")
        if avg_time_ms < 50:
            f.write("✓ EXCELLENT\n")
        elif avg_time_ms < target_p95:
            f.write("✓ PASS\n")
        else:
            f.write("✗ FAIL (Target: <100ms)\n")

        f.write(f"Throughput:     {throughput:.2f} req/s ")
        if throughput >= target_throughput:
            f.write("✓ PASS\n")
        else:
            f.write(f"✗ FAIL (Target: >={target_throughput} req/s)\n")

    print(f"✓ Summary report saved to: {output_file}")


# ============================================================================
# Main Profiling Function
# ============================================================================

def run_profiling(
    host: str,
    api_key: str,
    num_requests: int,
    detailed: bool = False
) -> None:
    """
    Run profiling on the Fraud API.

    Args:
        host: API host URL
        api_key: API authentication key
        num_requests: Number of requests to profile
        detailed: Whether to generate detailed reports
    """
    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for this profiling run
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    print("=" * 80)
    print("DYGSOM Fraud API - Performance Profiling")
    print("=" * 80)
    print(f"Host:          {host}")
    print(f"Requests:      {num_requests}")
    print(f"Detailed:      {detailed}")
    print("=" * 80)
    print()

    # Initialize client
    client = FraudAPIClient(host, api_key)

    # Profile the requests
    print(f"🔍 Profiling {num_requests} requests...")

    profiler = cProfile.Profile()
    profiler.enable()

    start_time = datetime.utcnow()
    responses = profile_multiple_requests(client, num_requests)
    end_time = datetime.utcnow()

    profiler.disable()

    profile_time = (end_time - start_time).total_seconds()

    print(f"✓ Profiling complete in {profile_time:.2f}s")
    print(f"✓ Successful requests: {len(responses)}/{num_requests}")
    print()

    # Generate profile stats
    stats = pstats.Stats(profiler)

    # Save raw profile data
    profile_file = RESULTS_DIR / f"profile_{timestamp}.prof"
    stats.dump_stats(str(profile_file))
    print(f"✓ Raw profile data saved to: {profile_file}")

    # Generate reports
    print()
    print("📊 Generating reports...")
    print()

    # 1. Summary report
    summary_file = RESULTS_DIR / f"summary_{timestamp}.txt"
    generate_summary_report(num_requests, responses, profile_time, summary_file)

    # 2. Hotspots report
    hotspots_file = RESULTS_DIR / f"hotspots_{timestamp}.txt"
    generate_hotspots_report(stats, hotspots_file)

    # 3. Detailed report (optional)
    if detailed:
        report_file = RESULTS_DIR / f"profile_{timestamp}.txt"
        generate_profile_report(stats, report_file)

    # Close client
    client.close()

    print()
    print("=" * 80)
    print("✅ Profiling Complete!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print(f"1. Review hotspots: cat {hotspots_file}")
    print(f"2. Review summary: cat {summary_file}")
    if detailed:
        print(f"3. Review detailed profile: cat {report_file}")
    print(f"4. Visualize with SnakeViz: snakeviz {profile_file}")
    print(f"5. Generate call graph: gprof2dot -f pstats {profile_file} | dot -Tpng -o callgraph_{timestamp}.png")
    print()


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point for the profiling script."""
    parser = argparse.ArgumentParser(
        description="Profile the DYGSOM Fraud API performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile 1 request (quick test)
  python profile_api.py --requests 1

  # Profile 100 requests (realistic load)
  python profile_api.py --requests 100

  # Profile with custom host
  python profile_api.py --host http://localhost:3000 --requests 50

  # Generate detailed reports
  python profile_api.py --requests 100 --detailed

  # Visualize results
  snakeviz performance/profiling/results/profile_<timestamp>.prof
        """
    )

    parser.add_argument(
        '--host',
        type=str,
        default=DEFAULT_HOST,
        help=f'API host URL (default: {DEFAULT_HOST})'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        default=API_KEY,
        help='API authentication key'
    )

    parser.add_argument(
        '--requests',
        type=int,
        default=10,
        help='Number of requests to profile (default: 10)'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Generate detailed profiling reports'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.requests < 1:
        print("❌ Error: --requests must be at least 1", file=sys.stderr)
        sys.exit(1)

    # Run profiling
    try:
        run_profiling(
            host=args.host,
            api_key=args.api_key,
            num_requests=args.requests,
            detailed=args.detailed
        )
    except KeyboardInterrupt:
        print("\n\n❌ Profiling interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Profiling failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
