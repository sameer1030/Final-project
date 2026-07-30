import csv
import os

import traci


SUMO_BINARY = "sumo-gui"
TRAFFIC_LIGHT_ID = "J1"

SCENARIOS = {
    "light": "sumo/simulation_light.sumocfg",
    "medium": "sumo/simulation_medium.sumocfg",
    "heavy": "sumo/simulation_heavy.sumocfg",
}

# Incoming lanes in the stable one-lane network
LANES = {
    "north": "E0_0",
    "south": "-E1_0",
    "west": "-E2_0",
    "east": "-E3_0",
}

# Existing traffic-light phase indices
NS_PHASE = 0
EW_PHASE = 2
NS_YELLOW_PHASE = 1
EW_YELLOW_PHASE = 3

SIMULATION_STEPS = 500

# Adaptive switching constraints
MIN_GREEN = 12
MAX_GREEN = 32
CHECK_INTERVAL = 5
SWITCH_ADVANTAGE = 4


def get_queue_length(lane_id):
    """Return the number of halted vehicles on one lane."""
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_lane_vehicle_count(lane_id):
    """Return all vehicles currently present on one lane."""
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_waiting_time(lane_id):
    """Return cumulative waiting time for vehicles currently on one lane."""
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.lane.getLastStepVehicleIDs(lane_id)
    )


def get_total_waiting_time():
    """Return cumulative waiting time for every vehicle in the simulation."""
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.vehicle.getIDList()
    )


def get_direction_metrics(direction):
    """Calculate demand measurements for NS or EW traffic."""
    if direction == "NS":
        lane_ids = [
            LANES["north"],
            LANES["south"],
        ]
    elif direction == "EW":
        lane_ids = [
            LANES["west"],
            LANES["east"],
        ]
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

    # Queue length receives the highest priority.
    traffic_score = (
        queue * 3.5
        + vehicle_count * 1.2
        + waiting_time * 0.2
    )

    return queue, vehicle_count, waiting_time, traffic_score


def classify_traffic(score):
    """Assign a readable traffic category to the current score."""
    if score == 0:
        return "EMPTY"
    elif score <= 8:
        return "VERY_LIGHT"
    elif score <= 20:
        return "LIGHT"
    elif score <= 40:
        return "MEDIUM"
    elif score <= 70:
        return "HEAVY"
    else:
        return "VERY_HEAVY"


def run_scenario(scenario_name, sumo_config):
    """Run one traffic scenario using adaptive signal control."""
    results_file = f"results/adaptive_{scenario_name}_results.csv"

    print(f"\nStarting adaptive {scenario_name} scenario...")
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
            current_sumo_phase
        )

        with open(
            results_file,
            mode="w",
            newline="",
            encoding="utf-8"
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

                # Prevent one direction from keeping green indefinitely.
                if elapsed_green >= MAX_GREEN:
                    should_switch = True

                # After minimum green, reconsider traffic every five seconds.
                elif (
                    elapsed_green >= MIN_GREEN
                    and elapsed_green % CHECK_INTERVAL == 0
                ):
                    # Switch when the active direction is empty.
                    if current_score == 0 and opposite_score > 0:
                        should_switch = True

                    # Switch when the opposite demand is clearly higher.
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
                        current_sumo_phase
                    )

                    # Report the new active direction's traffic category.
                    active_score = (
                        ns_score
                        if current_phase == "NS"
                        else ew_score
                    )
                    traffic_level = classify_traffic(active_score)

                vehicles_in_simulation = traci.vehicle.getIDCount()
                total_waiting_time = get_total_waiting_time()
                completed_vehicles = (
                    traci.simulation.getArrivedNumber()
                )

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
                    f"[ADAPTIVE - {scenario_name.upper()}] "
                    f"Step {step} | "
                    f"NS queue={ns_queue} | "
                    f"EW queue={ew_queue} | "
                    f"NS score={ns_score:.2f} | "
                    f"EW score={ew_score:.2f} | "
                    f"Direction={current_phase} | "
                    f"Level={traffic_level} | "
                    f"ElapsedGreen={elapsed_green} | "
                    f"Waiting={total_waiting_time:.2f}",
                    flush=True
                )

    finally:
        traci.close()

    print(f"Adaptive {scenario_name} scenario completed.")
    print(f"Saved to {results_file}")


def run():
    os.makedirs("results", exist_ok=True)

    for scenario_name, sumo_config in SCENARIOS.items():
        run_scenario(scenario_name, sumo_config)

    print("\nAll adaptive scenarios completed.")


if __name__ == "__main__":
    run()