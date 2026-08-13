import pandas as pd
import os

files = {
    ("LIGHT", "fixed"): "results/fixed_v2_light_results.csv",
    ("LIGHT", "adaptive"): "results/adaptive_v2_light_results.csv",

    ("MEDIUM", "fixed"): "results/fixed_v2_medium_results.csv",
    ("MEDIUM", "adaptive"): "results/adaptive_v2_medium_results.csv",

    ("HEAVY", "fixed"): "results/fixed_v2_heavy_results.csv",
    ("HEAVY", "adaptive"): "results/adaptive_v2_heavy_results.csv",

    ("UNBALANCED", "fixed"): "results/fixed_v2_unbalanced_results.csv",
    ("UNBALANCED", "adaptive"): "results/adaptive_v2_unbalanced_results.csv",
}

summary = {}

for (scenario, controller), path in files.items():

    if not os.path.exists(path):
        print(f"Missing file: {path}")
        continue

    df = pd.read_csv(path)

    total_queue = df["ns_queue"] + df["ew_queue"]

    avg_queue = total_queue.mean()
    max_queue = total_queue.max()

    throughput = df["completed_vehicles"].max()

    final_total_waiting = df["total_waiting_time"].iloc[-1]

    if throughput > 0:
        avg_wait = final_total_waiting / throughput
    else:
        avg_wait = 0

    summary[(scenario, controller)] = {
        "avg_wait": avg_wait,
        "avg_queue": avg_queue,
        "max_queue": max_queue,
        "throughput": throughput,
    }


print("\n=== TWO-LANE COMPARISON SUMMARY ===\n")

for scenario in ["LIGHT", "MEDIUM", "HEAVY", "UNBALANCED"]:

    for controller in ["fixed", "adaptive"]:

        key = (scenario, controller)

        if key not in summary:
            continue

        r = summary[key]

        print(
            f"{scenario} | {controller} | "
            f"Avg Wait: {r['avg_wait']:.2f} | "
            f"Avg Queue: {r['avg_queue']:.2f} | "
            f"Max Queue: {r['max_queue']:.0f} | "
            f"Throughput: {r['throughput']}"
        )


print("\n=== TWO-LANE IMPROVEMENT SUMMARY ===\n")

for scenario in ["LIGHT", "MEDIUM", "HEAVY", "UNBALANCED"]:

    fixed_key = (scenario, "fixed")
    adaptive_key = (scenario, "adaptive")

    if fixed_key not in summary or adaptive_key not in summary:
        continue

    fixed = summary[fixed_key]
    adaptive = summary[adaptive_key]

    waiting_improvement = (
        (fixed["avg_wait"] - adaptive["avg_wait"])
        / fixed["avg_wait"]
        * 100
        if fixed["avg_wait"] > 0 else 0
    )

    queue_improvement = (
        (fixed["avg_queue"] - adaptive["avg_queue"])
        / fixed["avg_queue"]
        * 100
        if fixed["avg_queue"] > 0 else 0
    )

    throughput_change = (
        (adaptive["throughput"] - fixed["throughput"])
        / fixed["throughput"]
        * 100
        if fixed["throughput"] > 0 else 0
    )

    print(
        f"{scenario} | "
        f"Waiting improvement: {waiting_improvement:.2f}% | "
        f"Queue improvement: {queue_improvement:.2f}% | "
        f"Throughput change: {throughput_change:.2f}%"
    )