import os
import glob
import math

results_dir = '/home/anton/projects/jb-try1/perf_test_scripts/results'

# 1) find latest directories
browse_dirs = sorted(glob.glob(os.path.join(results_dir, 'uc01_createorupdate-*')))
search_dirs = sorted(glob.glob(os.path.join(results_dir, 'uc02_performsearches-*')))

latest_browse = browse_dirs[-1]
latest_search = search_dirs[-1]

print(f"Latest Browse and Write directory: {os.path.basename(latest_browse)}")
print(f"Latest Search directory: {os.path.basename(latest_search)}")
print()

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

def analyze_simulation(log_path, match_string, mode='contains'):
    durations = []
    with open(log_path, 'r') as f:
        for line in f:
            parts = line.strip('\n').split('\t')
            # Look for GROUP lines
            if len(parts) >= 6 and parts[0] == 'GROUP':
                gname = parts[2]
                matched = False
                if mode == 'contains':
                    matched = match_string in gname
                elif mode == 'exact':
                    matched = gname == match_string
                
                if matched:
                    start_ts = int(parts[3])
                    end_ts = int(parts[4])
                    duration = end_ts - start_ts
                    durations.append(duration)
    
    if not durations:
        return None
    
    sorted_durations = sorted(durations)
    count = len(sorted_durations)
    avg_val = sum(sorted_durations) / count
    p50_val = get_percentile(sorted_durations, 50.0)
    p90_val = get_percentile(sorted_durations, 90.0)
    min_val = sorted_durations[0]
    max_val = sorted_durations[-1]
    
    return {
        'count': count,
        'avg': avg_val,
        'p50': p50_val,
        'p90': p90_val,
        'min': min_val,
        'max': max_val
    }

for mode in ['exact', 'contains']:
    print(f"=================================================")
    print(f"PARSING MODE: group name '{mode}' match")
    print(f"=================================================")
    
    # Analyze Browse and Write
    match_str = 'Script: BrowseAndWrite'
    stats_browse = analyze_simulation(os.path.join(latest_browse, 'simulation.log'), match_str, mode)
    print("--- BROWSE AND WRITE STATS ---")
    if stats_browse:
        print(f"Group match pattern: {match_str}")
        print(f"Count: {stats_browse['count']}")
        print(f"Avg duration: {stats_browse['avg']:.2f} ms")
        print(f"p50 duration: {stats_browse['p50']:.2f} ms")
        print(f"p90 duration: {stats_browse['p90']:.2f} ms")
        print(f"Min duration: {stats_browse['min']} ms")
        print(f"Max duration: {stats_browse['max']} ms")
        # Comparison against pacing thresholds: BrowseAndWrite 4000ms avg target
        target = 4000
        is_shorter = stats_browse['avg'] < target
        print(f"Comparison: Avg ({stats_browse['avg']:.2f} ms) is {'shorter' if is_shorter else 'longer or equal'} than/to target {target} ms")
    else:
        print("No matching groups found.")

    # Analyze Search
    match_str = 'Script: Search'
    stats_search = analyze_simulation(os.path.join(latest_search, 'simulation.log'), match_str, mode)
    print("\n--- SEARCH STATS ---")
    if stats_search:
        print(f"Group match pattern: {match_str}")
        print(f"Count: {stats_search['count']}")
        print(f"Avg duration: {stats_search['avg']:.2f} ms")
        print(f"p50 duration: {stats_search['p50']:.2f} ms")
        print(f"p90 duration: {stats_search['p90']:.2f} ms")
        print(f"Min duration: {stats_search['min']} ms")
        print(f"Max duration: {stats_search['max']} ms")
        # Comparison against pacing thresholds: Search 2000ms avg target
        target = 2000
        is_shorter = stats_search['avg'] < target
        print(f"Comparison: Avg ({stats_search['avg']:.2f} ms) is {'shorter' if is_shorter else 'longer or equal'} than/to target {target} ms")
    else:
        print("No matching groups found.")
    print()
