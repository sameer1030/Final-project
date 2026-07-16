import os
import pandas as pd

RESULTS_DIR = "results"

FILES = {
    ("fixed", "light"): "fixed_light_results.csv",
    ("fixed", "medium"): "fixed_medium_results.csv",
    ("fixed", "heavy"): "fixed_heavy_results.csv",
    ("adaptive", "light"): "adaptive_light_results.csv",
    ("adaptive", "medium"): "adaptive_medium_results.csv",
    ("adaptive", "heavy"): "adaptive_heavy_results.csv",
}


def analyse_file(controller, scenario, filename):
    path = os.path.join(RESULTS_DIR, filename)
    df = pd.read_csv(path)

    df["total_queue"] = df["ns_queue"] + df["ew_queue"]

    return {
        "controller": controller,
        "scenario": scenario,
        "average_waiting_time": round(df["total_waiting_time"].mean(), 2),
        "maximum_waiting_time": round(df["total_waiting_time"].max(), 2),
        "average_queue_length": round(df["total_queue"].mean(), 2),
        "maximum_queue_length": round(df["total_queue"].max(), 2),
        "throughput": int(df["completed_vehicles"].sum()),
    }


def calculate_improvement(fixed_value, adaptive_value):
    if fixed_value == 0:
        return 0
    return round(((fixed_value - adaptive_value) / fixed_value) * 100, 2)


def main():
    summary = []

    for (controller, scenario), filename in FILES.items():
        summary.append(analyse_file(controller, scenario, filename))

    summary_df = pd.DataFrame(summary)

    comparison_rows = []

    for scenario in ["light", "medium", "heavy"]:
        fixed = summary_df[
            (summary_df["controller"] == "fixed") &
            (summary_df["scenario"] == scenario)
        ].iloc[0]

        adaptive = summary_df[
            (summary_df["controller"] == "adaptive") &
            (summary_df["scenario"] == scenario)
        ].iloc[0]

        comparison_rows.append({
            "scenario": scenario,
            "fixed_avg_waiting_time": fixed["average_waiting_time"],
            "adaptive_avg_waiting_time": adaptive["average_waiting_time"],
            "waiting_time_improvement_percent": calculate_improvement(
                fixed["average_waiting_time"],
                adaptive["average_waiting_time"]
            ),
            "fixed_avg_queue_length": fixed["average_queue_length"],
            "adaptive_avg_queue_length": adaptive["average_queue_length"],
            "queue_length_improvement_percent": calculate_improvement(
                fixed["average_queue_length"],
                adaptive["average_queue_length"]
            ),
            "fixed_throughput": fixed["throughput"],
            "adaptive_throughput": adaptive["throughput"],
            "throughput_change_percent": round(
                ((adaptive["throughput"] - fixed["throughput"]) / fixed["throughput"]) * 100,
                2
            )
        })

    comparison_df = pd.DataFrame(comparison_rows)

    summary_path = os.path.join(RESULTS_DIR, "comparison_summary.csv")
    improvement_path = os.path.join(RESULTS_DIR, "improvement_summary.csv")

    summary_df.to_csv(summary_path, index=False)
    comparison_df.to_csv(improvement_path, index=False)

    print("\n=== COMPARISON SUMMARY ===")
    for _, row in summary_df.iterrows():
        print(
            f"{row['scenario'].upper()} | {row['controller']} | "
            f"Avg Wait: {row['average_waiting_time']} | "
            f"Avg Queue: {row['average_queue_length']} | "
            f"Throughput: {row['throughput']}"
        )

    print("\n=== IMPROVEMENT SUMMARY ===")
    for _, row in comparison_df.iterrows():
        print(
            f"{row['scenario'].upper()} | "
            f"Waiting improvement: {row['waiting_time_improvement_percent']}% | "
            f"Queue improvement: {row['queue_length_improvement_percent']}% | "
            f"Throughput change: {row['throughput_change_percent']}%"
        )

    print(f"\nSaved to {summary_path}")
    print(f"Saved to {improvement_path}")


if __name__ == "__main__":
    main()