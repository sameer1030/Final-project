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

fixed = comparison[comparison["controller"] == "fixed"]
adaptive = comparison[comparison["controller"] == "adaptive"]

scenarios = ["Light", "Medium", "Heavy"]
x = range(len(scenarios))


def add_value_labels(bars):
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=9
        )


def create_bar_chart(fixed_values, adaptive_values, ylabel, title, filename):
    plt.figure(figsize=(9, 6), dpi=300)

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
        label="Adaptive"
    )

    add_value_labels(fixed_bars)
    add_value_labels(adaptive_bars)

    plt.xticks(x, scenarios)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

    plt.savefig(os.path.join(RESULTS_DIR, filename))
    plt.close()


create_bar_chart(
    fixed["average_waiting_time"],
    adaptive["average_waiting_time"],
    "Average Waiting Time (seconds)",
    "Comparison of Average Vehicle Waiting Time",
    "waiting_time_comparison.png"
)

create_bar_chart(
    fixed["average_queue_length"],
    adaptive["average_queue_length"],
    "Average Queue Length (vehicles)",
    "Comparison of Average Queue Length",
    "queue_length_comparison.png"
)

create_bar_chart(
    fixed["throughput"],
    adaptive["throughput"],
    "Completed Vehicles",
    "Comparison of Vehicle Throughput",
    "throughput_comparison.png"
)

# Percentage improvement graph
plt.figure(figsize=(10, 6), dpi=300)

bar1 = plt.bar(
    [i - 0.25 for i in x],
    improvement["waiting_time_improvement_percent"],
    width=0.25,
    label="Waiting Time Improvement"
)

bar2 = plt.bar(
    x,
    improvement["queue_length_improvement_percent"],
    width=0.25,
    label="Queue Length Improvement"
)

bar3 = plt.bar(
    [i + 0.25 for i in x],
    improvement["throughput_change_percent"],
    width=0.25,
    label="Throughput Change"
)

add_value_labels(bar1)
add_value_labels(bar2)
add_value_labels(bar3)

plt.xticks(x, scenarios)
plt.ylabel("Percentage Change (%)")
plt.title("Percentage Performance Change of Adaptive Controller")
plt.axhline(0, linewidth=1)
plt.grid(axis="y", linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()

plt.savefig(os.path.join(RESULTS_DIR, "percentage_improvement_comparison.png"))
plt.close()

print("\nGraphs generated successfully.")
print("Saved in results folder:")
print("waiting_time_comparison_v2.png")
print("queue_length_comparison_v2.png")
print("throughput_comparison_v2.png")
print("percentage_improvement_comparison_v2.png")