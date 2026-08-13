import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "results"

comparison = pd.read_csv(
    os.path.join(RESULTS_DIR, "comparison_summary_v2.csv")
)

improvement = pd.read_csv(
    os.path.join(RESULTS_DIR, "improvement_summary_v2.csv")
)

scenario_order = ["light", "medium", "heavy", "unbalanced"]

comparison["scenario"] = pd.Categorical(
    comparison["scenario"],
    categories=scenario_order,
    ordered=True
)

comparison = comparison.sort_values("scenario")

improvement["scenario"] = pd.Categorical(
    improvement["scenario"],
    categories=scenario_order,
    ordered=True
)

improvement = improvement.sort_values("scenario")

fixed = comparison[
    comparison["controller"] == "fixed"
].reset_index(drop=True)

adaptive = comparison[
    comparison["controller"] == "adaptive"
].reset_index(drop=True)

scenarios = ["Light", "Medium", "Heavy", "Unbalanced"]
x = list(range(len(scenarios)))


def add_value_labels(bars, decimals=2):
    for bar in bars:
        height = bar.get_height()

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.{decimals}f}",
            ha="center",
            va="bottom",
            fontsize=8
        )


def create_comparison_chart(
    fixed_values,
    adaptive_values,
    ylabel,
    title,
    filename,
    decimals=2
):
    plt.figure(figsize=(8.5, 5.5), dpi=300)

    fixed_bars = plt.bar(
        [i - 0.2 for i in x],
        fixed_values,
        width=0.4,
        label="Fixed-Time"
    )

    adaptive_bars = plt.bar(
        [i + 0.2 for i in x],
        adaptive_values,
        width=0.4,
        label="Adaptive (WATSC)"
    )

    add_value_labels(fixed_bars, decimals)
    add_value_labels(adaptive_bars, decimals)

    plt.xticks(x, scenarios)
    plt.xlabel("Traffic Scenario")
    plt.ylabel(ylabel)
    plt.title(title)

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.35
    )

    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(
        RESULTS_DIR,
        filename
    )

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {output_path}")


# Figure 4 - Waiting Time
create_comparison_chart(
    fixed["average_waiting_time"],
    adaptive["average_waiting_time"],
    "Average Waiting Time (s)",
    "Average Waiting Time: Fixed-Time vs Adaptive (WATSC)",
    "figure4_waiting_time_v2.png"
)


# Figure 5 - Queue Length
create_comparison_chart(
    fixed["average_queue_length"],
    adaptive["average_queue_length"],
    "Average Queue Length (vehicles)",
    "Average Queue Length: Fixed-Time vs Adaptive (WATSC)",
    "figure5_queue_length_v2.png"
)


# Figure 6 - Throughput
create_comparison_chart(
    fixed["throughput"],
    adaptive["throughput"],
    "Completed Vehicles",
    "Vehicle Throughput: Fixed-Time vs Adaptive (WATSC)",
    "figure6_throughput_v2.png",
    decimals=0
)


# Figure 7 - Percentage Improvement
plt.figure(figsize=(9, 5.5), dpi=300)

waiting_bars = plt.bar(
    [i - 0.25 for i in x],
    improvement["waiting_time_improvement_percent"],
    width=0.25,
    label="Waiting Time"
)

queue_bars = plt.bar(
    x,
    improvement["queue_length_improvement_percent"],
    width=0.25,
    label="Queue Length"
)

throughput_bars = plt.bar(
    [i + 0.25 for i in x],
    improvement["throughput_change_percent"],
    width=0.25,
    label="Throughput"
)

add_value_labels(waiting_bars)
add_value_labels(queue_bars)
add_value_labels(throughput_bars)

plt.xticks(x, scenarios)
plt.xlabel("Traffic Scenario")
plt.ylabel("Performance Change (%)")
plt.title("Performance Improvement of the Proposed WATSC over Fixed-Time Control")

plt.axhline(
    0,
    linewidth=1
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.35
)

plt.legend()
plt.tight_layout()

output_path = os.path.join(
    RESULTS_DIR,
    "figure7_percentage_improvement_v2.png"
)

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Saved: {output_path}")

print("\nAll final paper graphs generated successfully.")