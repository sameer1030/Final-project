"""
Fixed-Time Traffic Signal Controller

MSc Project
Dublin City University

Author: Sameer Srinivas

Implements the baseline fixed-time traffic signal controller used
for comparison with the proposed WATSC.
"""
import csv
import os

import traci


SUMO_BINARY = "sumo-gui"
TRAFFIC_LIGHT_ID = "J0"

SCENARIOS = {
    "light": "sumo/simulation_light_v2.sumocfg",
    "medium": "sumo/simulation_medium_v2.sumocfg",
    "heavy": "sumo/simulation_heavy_v2.sumocfg",
    "unbalanced": "sumo/simulation_unbalanced_v2.sumocfg",
}

LANES = {
    "north": ["-E0_0", "-E0_1"],
    "south": ["-E2_0", "-E2_1"],
    "west": ["-E1_0", "-E1_1"],
    "east": ["-E3_0", "-E3_1"],
}

SIMULATION_STEPS = 500
PHASE_DURATION = 30

NS_GREEN_PHASE = 0
EW_GREEN_PHASE = 2


def get_queue_length(lane_ids):
    return sum(
        traci.lane.getLastStepHaltingNumber(lane_id)
        for lane_id in lane_ids
    )


def get_total_waiting_time():
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.vehicle.getIDList()
    )


def run_scenario(scenario_name, sumo_config):
    results_file = f"results/fixed_v2_{scenario_name}_results.csv"

    traci.start([
        SUMO_BINARY,
        "-c",
        sumo_config,
    ])

    try:
        with open(results_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
                "step",
                "ns_queue",
                "ew_queue",
                "active_phase",
                "vehicles_in_simulation",
                "total_waiting_time",
                "completed_vehicles",
            ])

            for step in range(SIMULATION_STEPS):
                traci.simulationStep()

                ns_queue = (
                    get_queue_length(LANES["north"])
                    + get_queue_length(LANES["south"])
                )

                ew_queue = (
                    get_queue_length(LANES["west"])
                    + get_queue_length(LANES["east"])
                )

                if (step // PHASE_DURATION) % 2 == 0:
                    active_phase = "NS_GREEN"
                    traci.trafficlight.setPhase(
                        TRAFFIC_LIGHT_ID,
                        NS_GREEN_PHASE,
                    )
                else:
                    active_phase = "EW_GREEN"
                    traci.trafficlight.setPhase(
                        TRAFFIC_LIGHT_ID,
                        EW_GREEN_PHASE,
                    )

                vehicles_in_simulation = traci.vehicle.getIDCount()
                total_waiting_time = get_total_waiting_time()
                completed_vehicles = traci.simulation.getArrivedNumber()

                writer.writerow([
                    step,
                    ns_queue,
                    ew_queue,
                    active_phase,
                    vehicles_in_simulation,
                    total_waiting_time,
                    completed_vehicles,
                ])

                print(
                    f"[FIXED V2 - {scenario_name.upper()}] "
                    f"Step {step} | "
                    f"NS={ns_queue} | EW={ew_queue} | "
                    f"Phase={active_phase} | "
                    f"Waiting={total_waiting_time:.2f}",
                    flush=True,
                )

    finally:
        traci.close()

    print(f"Fixed-time V2 {scenario_name} scenario completed.")


def run():
    os.makedirs("results", exist_ok=True)

    for scenario_name, sumo_config in SCENARIOS.items():
        run_scenario(scenario_name, sumo_config)

    print("All fixed-time V2 scenarios completed.")


if __name__ == "__main__":
    run()