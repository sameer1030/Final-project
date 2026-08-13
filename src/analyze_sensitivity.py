import os

import pandas as pd


RESULTS_DIR = "results"

FILES = {
    "Conservative": "adaptive_sensitivity_conservative.csv",
    "Current": "adaptive_sensitivity_current.csv",
    "Responsive": "adaptive_sensitivity_responsive.csv",
}


def analyse_file(configuration, filename):
    path = os.path.join(RESULTS_DIR, filename)
    df = pd.read_csv(path)

    df["total_queue"] = df["ns_queue"] + df["ew_queue"]

    return {
        "configuration": configuration,
        "average_waiting_time": round(
            df["total_waiting_time"].mean(),
            2,
        ),
        "maximum_waiting_time": round(
            df["total_waiting_time"].max(),
            2,
        ),
        "average_queue_length": round(
            df["total_queue"].mean(),
            2,
        ),
        "maximum_queue_length": int(
            df["total_queue"].max(),
        ),
        "throughput": int(
            df["completed_vehicles"].sum(),
        ),
    }


def main():
    results = []

    for configuration, filename in FILES.items():
        results.append(
            analyse_file(configuration, filename)
        )

    results_df = pd.DataFrame(results)

    output_path = os.path.join(
        RESULTS_DIR,
        "sensitivity_summary.csv",
    )

    results_df.to_csv(output_path, index=False)

    print("\n=== PARAMETER SENSITIVITY SUMMARY ===")

    for _, row in results_df.iterrows():
        print(
            f"{row['configuration']} | "
            f"Avg Wait: {row['average_waiting_time']} | "
            f"Max Wait: {row['maximum_waiting_time']} | "
            f"Avg Queue: {row['average_queue_length']} | "
            f"Max Queue: {row['maximum_queue_length']} | "
            f"Throughput: {row['throughput']}"
        )

    best_waiting = results_df.loc[
        results_df["average_waiting_time"].idxmin()
    ]

    best_queue = results_df.loc[
        results_df["average_queue_length"].idxmin()
    ]

    best_throughput = results_df.loc[
        results_df["throughput"].idxmax()
    ]

    print("\n=== BEST CONFIGURATIONS ===")
    print(
        f"Lowest average waiting time: "
        f"{best_waiting['configuration']}"
    )
    print(
        f"Lowest average queue length: "
        f"{best_queue['configuration']}"
    )
    print(
        f"Highest throughput: "
        f"{best_throughput['configuration']}"
    )

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
