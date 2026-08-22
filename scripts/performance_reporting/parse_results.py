import glob
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPOSITORY_ROOT / 'perf_test_scripts' / 'results'
OUTPUT_DIR = RESULTS_DIR / 'parsed'

SIMULATIONS = [
    {
        'label': 'Browse And Write',
        'folder_glob': 'uc01-createorupdate-*',
        'simulation_name': 'youtrack.UC01_createOrUpdate',
    },
    {
        'label': 'Search',
        'folder_glob': 'uc02-performsearches-*',
        'simulation_name': 'youtrack.UC02_performSearches',
    },
    {
        'label': 'View Issue',
        'folder_glob': 'uc03-viewissue-*',
        'simulation_name': 'youtrack.UC03_viewIssue',
    },
]


def get_percentile(sorted_data, percentile):
    if not sorted_data:
        return 0.0
    size = len(sorted_data)
    k = (size - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1


def find_latest_directory(folder_glob):
    candidates = sorted(glob.glob(str(RESULTS_DIR / folder_glob)))
    return Path(candidates[-1]) if candidates else None


def parse_simulation_log(log_path):
    run_start = None
    min_start_ts = None
    max_end_ts = None
    request_latencies = defaultdict(list)
    request_counts = defaultdict(int)
    failed_requests = defaultdict(int)
    timeline = defaultdict(int)

    with open(log_path, 'r', encoding='utf-8') as handle:
        for raw_line in handle:
            parts = raw_line.rstrip('\n').split('\t')
            if not parts:
                continue

            if parts[0] == 'RUN' and len(parts) >= 4:
                try:
                    run_start = int(parts[3])
                except ValueError:
                    run_start = None
                continue

            if parts[0] != 'REQUEST' or len(parts) < 7:
                continue

            request_name = parts[2]

            try:
                start_ts = int(parts[4])
                end_ts = int(parts[5])
            except ValueError:
                continue

            if min_start_ts is None or start_ts < min_start_ts:
                min_start_ts = start_ts
            if max_end_ts is None or end_ts > max_end_ts:
                max_end_ts = end_ts

            if run_start is None:
                run_start = start_ts

            bucket_minute = max(0, int((start_ts - run_start) // 60000))
            timeline[bucket_minute] += 1
            request_counts[request_name] += 1

            if parts[6] == 'OK':
                request_latencies[request_name].append(end_ts - start_ts)
            else:
                failed_requests[request_name] += 1

    return {
        'run_start': run_start,
        'min_start_ts': min_start_ts,
        'max_end_ts': max_end_ts,
        'request_latencies': request_latencies,
        'request_counts': request_counts,
        'failed_requests': failed_requests,
        'timeline': timeline,
    }


def summarize_latencies(request_latencies, request_counts, failed_requests):
    rows = []
    for request_name in sorted(request_counts.keys()):
        latencies = sorted(request_latencies.get(request_name, []))
        success_count = len(latencies)
        total_count = request_counts[request_name]
        fail_count = failed_requests.get(request_name, 0)
        avg_val = sum(latencies) / success_count if success_count else 0.0
        rows.append({
            'request_name': request_name,
            'total': total_count,
            'success': success_count,
            'failed': fail_count,
            'error_rate': (fail_count / total_count * 100.0) if total_count else 0.0,
            'avg': avg_val,
            'p50': get_percentile(latencies, 50.0),
            'p90': get_percentile(latencies, 90.0),
            'min': latencies[0] if latencies else 0.0,
            'max': latencies[-1] if latencies else 0.0,
        })
    return rows


def write_csv(path, header, rows):
    import csv

    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def svg_line_chart(series_map, output_path, title='Requests Over Time'):
    width = 1200
    height = 650
    margin_left = 80
    margin_right = 30
    margin_top = 70
    margin_bottom = 90
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    all_points = []
    for points in series_map.values():
        all_points.extend(points)

    max_x = max((x for x, _ in all_points), default=0)
    max_y = max((y for _, y in all_points), default=1)
    max_x = max(max_x, 1)
    max_y = max(max_y, 1)

    colors = ['#0f766e', '#b45309', '#1d4ed8', '#dc2626', '#7c3aed']
    legend_items = []
    path_items = []
    axis_items = []

    def map_x(value):
        return margin_left + (value / max_x) * plot_width

    def map_y(value):
        return margin_top + plot_height - (value / max_y) * plot_height

    for tick in range(6):
        x = margin_left + (tick / 5.0) * plot_width
        axis_items.append(
            f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + plot_height}" stroke="#e5e7eb" stroke-width="1" />'
        )
        label = int(round((tick / 5.0) * max_x))
        axis_items.append(
            f'<text x="{x:.2f}" y="{margin_top + plot_height + 22}" text-anchor="middle" font-size="12" fill="#374151">{label}m</text>'
        )

    for tick in range(6):
        y = margin_top + plot_height - (tick / 5.0) * plot_height
        axis_items.append(
            f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_width}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1" />'
        )
        label = int(round((tick / 5.0) * max_y))
        axis_items.append(
            f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-size="12" fill="#374151">{label}</text>'
        )

    for index, (series_name, points) in enumerate(series_map.items()):
        if not points:
            continue

        color = colors[index % len(colors)]
        sorted_points = sorted(points)
        polyline = ' '.join(f'{map_x(x):.2f},{map_y(y):.2f}' for x, y in sorted_points)
        path_items.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{polyline}" />'
        )
        legend_y = 30 + index * 24
        legend_items.append(
            f'<rect x="{margin_left}" y="{legend_y - 12}" width="14" height="14" fill="{color}" />'
        )
        legend_items.append(
            f'<text x="{margin_left + 22}" y="{legend_y}" font-size="14" fill="#111827">{series_name}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{margin_left}" y="30" font-size="22" font-weight="bold" fill="#111827">{title}</text>
  {''.join(legend_items)}
  <rect x="{margin_left}" y="{margin_top}" width="{plot_width}" height="{plot_height}" fill="none" stroke="#9ca3af" stroke-width="1.5" />
  {''.join(axis_items)}
  {''.join(path_items)}
  <text x="{margin_left + plot_width / 2:.2f}" y="{height - 30}" text-anchor="middle" font-size="13" fill="#374151">Minutes since test start</text>
  <text x="24" y="{margin_top + plot_height / 2:.2f}" transform="rotate(-90 24 {margin_top + plot_height / 2:.2f})" text-anchor="middle" font-size="13" fill="#374151">Requests per minute</text>
</svg>
'''

    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write(svg)


def print_latency_table(label, rows):
    print(f'--- {label.upper()} LATENCY SUMMARY ---')
    if not rows:
        print('No request records found.')
        return

    for row in rows:
        print(
            f"{row['request_name']}: total={row['total']} success={row['success']} "
            f"failed={row['failed']} error_rate={row['error_rate']:.2f}% "
            f"avg={row['avg']:.2f} ms p50={row['p50']:.2f} ms p90={row['p90']:.2f} ms "
            f"min={row['min']:.2f} ms max={row['max']:.2f} ms"
        )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    timeline_series = {}
    simulation_windows = []
    global_start_ts = None
    global_end_ts = None

    for simulation in SIMULATIONS:
        latest_dir = find_latest_directory(simulation['folder_glob'])
        if latest_dir is None:
            print(f"Missing results for {simulation['label']} ({simulation['folder_glob']})")
            continue

        log_path = latest_dir / 'simulation.log'
        if not log_path.exists():
            print(f"Missing simulation log: {log_path}")
            continue

        print(f"Latest {simulation['label']} directory: {latest_dir.name}")
        parsed = parse_simulation_log(log_path)

        simulation_start = parsed['min_start_ts']
        simulation_end = parsed['max_end_ts']
        if simulation_start is not None and simulation_end is not None:
            if global_start_ts is None or simulation_start < global_start_ts:
                global_start_ts = simulation_start
            if global_end_ts is None or simulation_end > global_end_ts:
                global_end_ts = simulation_end
            simulation_windows.append({
                'simulation': simulation['label'],
                'directory': latest_dir.name,
                'start_ms': simulation_start,
                'end_ms': simulation_end,
                'start_utc': datetime.fromtimestamp(simulation_start / 1000.0, tz=timezone.utc).isoformat(),
                'end_utc': datetime.fromtimestamp(simulation_end / 1000.0, tz=timezone.utc).isoformat(),
                'duration_minutes': f"{(simulation_end - simulation_start) / 60000.0:.2f}",
            })

        latency_rows = summarize_latencies(
            parsed['request_latencies'],
            parsed['request_counts'],
            parsed['failed_requests'],
        )
        print_latency_table(simulation['label'], latency_rows)
        print()

        for row in latency_rows:
            summary_rows.append({
                'simulation': simulation['label'],
                'request_name': row['request_name'],
                'total': row['total'],
                'success': row['success'],
                'failed': row['failed'],
                'error_rate': f"{row['error_rate']:.2f}",
                'avg_ms': f"{row['avg']:.2f}",
                'p50_ms': f"{row['p50']:.2f}",
                'p90_ms': f"{row['p90']:.2f}",
                'min_ms': f"{row['min']:.2f}",
                'max_ms': f"{row['max']:.2f}",
            })

        timeline_series[simulation['label']] = sorted(parsed['timeline'].items())

    if summary_rows:
        write_csv(
            OUTPUT_DIR / 'latency_summary.csv',
            ['simulation', 'request_name', 'total', 'success', 'failed', 'error_rate', 'avg_ms', 'p50_ms', 'p90_ms', 'min_ms', 'max_ms'],
            summary_rows,
        )
        print(f'Wrote latency summary to {OUTPUT_DIR / "latency_summary.csv"}')

    if timeline_series:
        write_csv(
            OUTPUT_DIR / 'requests_over_time.csv',
            ['simulation', 'minute', 'request_count'],
            [
                {'simulation': simulation_name, 'minute': minute, 'request_count': count}
                for simulation_name, points in timeline_series.items()
                for minute, count in points
            ],
        )
        svg_line_chart(timeline_series, OUTPUT_DIR / 'requests_over_time.svg')
        print(f'Wrote request timeline graph to {OUTPUT_DIR / "requests_over_time.svg"}')

    if simulation_windows:
        write_csv(
            OUTPUT_DIR / 'simulation_time_windows.csv',
            ['simulation', 'directory', 'start_ms', 'end_ms', 'start_utc', 'end_utc', 'duration_minutes'],
            simulation_windows,
        )
        print(f'Wrote per-simulation time windows to {OUTPUT_DIR / "simulation_time_windows.csv"}')

    if global_start_ts is not None and global_end_ts is not None:
        global_window_row = [{
            'window': 'all_latest_simulations',
            'from_ms': global_start_ts,
            'to_ms': global_end_ts,
            'from_utc': datetime.fromtimestamp(global_start_ts / 1000.0, tz=timezone.utc).isoformat(),
            'to_utc': datetime.fromtimestamp(global_end_ts / 1000.0, tz=timezone.utc).isoformat(),
            'duration_minutes': f"{(global_end_ts - global_start_ts) / 60000.0:.2f}",
        }]
        write_csv(
            OUTPUT_DIR / 'test_time_range.csv',
            ['window', 'from_ms', 'to_ms', 'from_utc', 'to_utc', 'duration_minutes'],
            global_window_row,
        )
        print(f'Wrote combined test time range to {OUTPUT_DIR / "test_time_range.csv"}')


if __name__ == '__main__':
    main()
