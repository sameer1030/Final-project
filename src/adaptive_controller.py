"""
Weighted Adaptive Traffic Signal Controller (WATSC)

MSc Project
Dublin City University

Author: Sameer Srinivas

Implements a rule-based adaptive traffic signal controller using
SUMO and TraCI for real-time traffic signal optimisation.
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

# Two incoming lanes on each approach
LANES = {
    "north": ["-E0_0", "-E0_1"],
    "south": ["-E2_0", "-E2_1"],
    "west": ["-E1_0", "-E1_1"],
    "east": ["-E3_0", "-E3_1"],
}

# Phase 2 serves the north-south pair.
# Phase 0 serves the east-west pair.
NS_PHASE = 0
EW_PHASE = 2
NS_YELLOW_PHASE = 1
EW_YELLOW_PHASE = 3

SIMULATION_STEPS = 500

MIN_GREEN = 12
MAX_GREEN = 32
CHECK_INTERVAL = 5
SWITCH_ADVANTAGE = 4


def get_queue_length(lane_id):
    """Return halted vehicles on one lane."""
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_lane_vehicle_count(lane_id):
    """Return vehicles currently present on one lane."""
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_waiting_time(lane_id):
    """Return waiting time of vehicles currently on one lane."""
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.lane.getLastStepVehicleIDs(lane_id)
    )


def get_total_waiting_time():
    """Return total waiting time of all active vehicles."""
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.vehicle.getIDList()
    )


def get_direction_metrics(direction):
    """Calculate combined demand across all lanes in one direction pair."""
    if direction == "NS":
        lane_ids = LANES["north"] + LANES["south"]
    elif direction == "EW":
        lane_ids = LANES["west"] + LANES["east"]
    else:
        raise ValueError(f"Unknown direction: {direction}")

    queue = sum(
        get_queue_length(lane_id)
        for lane_id in lane_ids
    )

    vehicle_count = sum(
        get_lane_vehicle_count(lane_id)
        for lane_id in lane_ids
    )

    waiting_time = sum(
        get_lane_waiting_time(lane_id)
        for lane_id in lane_ids
    )

    traffic_score = (
        queue * 3.5
        + vehicle_count * 1.2
        + waiting_time * 0.2
    )

    return queue, vehicle_count, waiting_time, traffic_score


def classify_traffic(score):
    """Assign a readable traffic category."""
    if score == 0:
        return "EMPTY"
    if score <= 8:
        return "VERY_LIGHT"
    if score <= 20:
        return "LIGHT"
    if score <= 40:
        return "MEDIUM"
    if score <= 70:
        return "HEAVY"
    return "VERY_HEAVY"


def run_scenario(scenario_name, sumo_config):
    """Run one two-lane scenario using adaptive control."""
    results_file = f"results/adaptive_v2_{scenario_name}_results.csv"

    print(f"\nStarting adaptive V2 {scenario_name} scenario...")
    print(f"Using configuration: {sumo_config}")

    traci.start([
        SUMO_BINARY,
        "-c",
        sumo_config,
        "--start",
        "--quit-on-end",
    ])

    current_phase = "NS"
    current_sumo_phase = NS_PHASE
    last_switch_step = 0

    try:
        traci.trafficlight.setPhase(
            TRAFFIC_LIGHT_ID,
            current_sumo_phase,
        )

        with open(
            results_file,
            mode="w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                "step",
                "ns_queue",
                "ew_queue",
                "ns_vehicle_count",
                "ew_vehicle_count",
                "ns_waiting_time",
                "ew_waiting_time",
                "ns_score",
                "ew_score",
                "chosen_direction",
                "traffic_level",
                "green_time",
                "vehicles_in_simulation",
                "total_waiting_time",
                "completed_vehicles",
            ])

            for step in range(SIMULATION_STEPS):
                traci.simulationStep()

                (
                    ns_queue,
                    ns_vehicles,
                    ns_wait,
                    ns_score,
                ) = get_direction_metrics("NS")

                (
                    ew_queue,
                    ew_vehicles,
                    ew_wait,
                    ew_score,
                ) = get_direction_metrics("EW")

                if current_phase == "NS":
                    current_score = ns_score
                    opposite_score = ew_score
                    opposite_phase = "EW"
                    opposite_sumo_phase = EW_PHASE
                else:
                    current_score = ew_score
                    opposite_score = ns_score
                    opposite_phase = "NS"
                    opposite_sumo_phase = NS_PHASE

                elapsed_green = step - last_switch_step
                traffic_level = classify_traffic(current_score)
                should_switch = False

                if elapsed_green >= MAX_GREEN:
                    should_switch = True

                elif (
                    elapsed_green >= MIN_GREEN
                    and elapsed_green % CHECK_INTERVAL == 0
                ):
                    if current_score == 0 and opposite_score > 0:
                        should_switch = True

                    elif (
                        opposite_score
                        >= current_score + SWITCH_ADVANTAGE
                    ):
                        should_switch = True

                if should_switch:
                    current_phase = opposite_phase
                    current_sumo_phase = opposite_sumo_phase
                    last_switch_step = step
                    elapsed_green = 0

                    traci.trafficlight.setPhase(
                        TRAFFIC_LIGHT_ID,
                        current_sumo_phase,
                    )

                    active_score = (
                        ns_score
                        if current_phase == "NS"
                        else ew_score
                    )
                    traffic_level = classify_traffic(active_score)

                vehicles_in_simulation = traci.vehicle.getIDCount()
                total_waiting_time = get_total_waiting_time()
                completed_vehicles = traci.simulation.getArrivedNumber()

                writer.writerow([
                    step,
                    ns_queue,
                    ew_queue,
                    ns_vehicles,
                    ew_vehicles,
                    round(ns_wait, 2),
                    round(ew_wait, 2),
                    round(ns_score, 2),
                    round(ew_score, 2),
                    current_phase,
                    traffic_level,
                    elapsed_green,
                    vehicles_in_simulation,
                    round(total_waiting_time, 2),
                    completed_vehicles,
                ])

                print(
                    f"[ADAPTIVE V2 - {scenario_name.upper()}] "
                    f"Step {step} | "
                    f"NS queue={ns_queue} | "
                    f"EW queue={ew_queue} | "
                    f"NS score={ns_score:.2f} | "
                    f"EW score={ew_score:.2f} | "
                    f"Direction={current_phase} | "
                    f"Level={traffic_level} | "
                    f"ElapsedGreen={elapsed_green} | "
                    f"Waiting={total_waiting_time:.2f}",
                    flush=True,
                )

    finally:
        traci.close()

    print(f"Adaptive V2 {scenario_name} scenario completed.")
    print(f"Saved to {results_file}")


def run():
    os.makedirs("results", exist_ok=True)

    for scenario_name, sumo_config in SCENARIOS.items():
        run_scenario(scenario_name, sumo_config)

    print("\nAll adaptive V2 scenarios completed.")


if __name__ == "__main__":
    run()