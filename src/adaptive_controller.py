import traci
import csv
import os

SUMO_BINARY = "sumo-gui"
TRAFFIC_LIGHT_ID = "J1"

SCENARIOS = {
    "light": "sumo/simulation_light.sumocfg",
    "medium": "sumo/simulation_medium.sumocfg",
    "heavy": "sumo/simulation_heavy.sumocfg",
}

LANES = {
    "north": "E0_0",
    "south": "-E1_0",
    "west": "-E2_0",
    "east": "-E3_0",
}

NS_PHASE = 0
EW_PHASE = 2

SIMULATION_STEPS = 500

EMPTY_GREEN = 8
VERY_LIGHT_GREEN = 12
LIGHT_GREEN = 18
MEDIUM_GREEN = 28
HEAVY_GREEN = 40
VERY_HEAVY_GREEN = 55


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_lane_vehicle_count(lane_id):
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_waiting_time(lane_id):
    total_wait = 0
    for vehicle_id in traci.lane.getLastStepVehicleIDs(lane_id):
        total_wait += traci.vehicle.getWaitingTime(vehicle_id)
    return total_wait


def get_total_waiting_time():
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.vehicle.getIDList()
    )


def get_direction_metrics(direction):
    if direction == "NS":
        lanes = [LANES["north"], LANES["south"]]
    else:
        lanes = [LANES["west"], LANES["east"]]

    queue = sum(get_queue_length(lane) for lane in lanes)
    vehicle_count = sum(get_lane_vehicle_count(lane) for lane in lanes)
    waiting_time = sum(get_lane_waiting_time(lane) for lane in lanes)

    traffic_score = (queue * 3) + (vehicle_count * 1.5) + (waiting_time * 0.2)

    return queue, vehicle_count, waiting_time, traffic_score


def calculate_green_time(traffic_score):
    if traffic_score == 0:
        return EMPTY_GREEN, "EMPTY"
    elif traffic_score <= 8:
        return VERY_LIGHT_GREEN, "VERY_LIGHT"
    elif traffic_score <= 18:
        return LIGHT_GREEN, "LIGHT"
    elif traffic_score <= 35:
        return MEDIUM_GREEN, "MEDIUM"
    elif traffic_score <= 60:
        return HEAVY_GREEN, "HEAVY"
    else:
        return VERY_HEAVY_GREEN, "VERY_HEAVY"


def run_scenario(scenario_name, sumo_config):
    results_file = f"results/adaptive_{scenario_name}_results.csv"

    traci.start([SUMO_BINARY, "-c", sumo_config])

    current_phase = "NS"
    current_green_time = MEDIUM_GREEN
    last_switch_step = 0

    with open(results_file, mode="w", newline="") as file:
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
            "completed_vehicles"
        ])

        for step in range(SIMULATION_STEPS):
            traci.simulationStep()

            ns_queue, ns_vehicles, ns_wait, ns_score = get_direction_metrics("NS")
            ew_queue, ew_vehicles, ew_wait, ew_score = get_direction_metrics("EW")

            if ns_score >= ew_score:
                selected_phase = "NS"
                selected_score = ns_score
                selected_sumo_phase = NS_PHASE
            else:
                selected_phase = "EW"
                selected_score = ew_score
                selected_sumo_phase = EW_PHASE

            green_time, traffic_level = calculate_green_time(selected_score)

            if step - last_switch_step >= current_green_time:
                current_phase = selected_phase
                current_green_time = green_time
                last_switch_step = step

                traci.trafficlight.setPhase(
                    TRAFFIC_LIGHT_ID,
                    selected_sumo_phase
                )

            vehicles_in_simulation = traci.vehicle.getIDCount()
            total_waiting_time = get_total_waiting_time()
            completed_vehicles = traci.simulation.getArrivedNumber()

            writer.writerow([
                step,
                ns_queue,
                ew_queue,
                ns_vehicles,
                ew_vehicles,
                ns_wait,
                ew_wait,
                round(ns_score, 2),
                round(ew_score, 2),
                current_phase,
                traffic_level,
                current_green_time,
                vehicles_in_simulation,
                total_waiting_time,
                completed_vehicles
            ])

            print(
                f"[ADAPTIVE - {scenario_name.upper()}] Step {step} | "
                f"NS_score={ns_score:.2f} | EW_score={ew_score:.2f} | "
                f"Direction={current_phase} | Level={traffic_level} | "
                f"Green={current_green_time} | Waiting={total_waiting_time}",
                flush=True
            )

    traci.close()
    print(f"Adaptive {scenario_name} scenario completed.")


def run():
    os.makedirs("results", exist_ok=True)

    for scenario_name, sumo_config in SCENARIOS.items():
        run_scenario(scenario_name, sumo_config)

    print("All adaptive scenarios completed.")


if __name__ == "__main__":
    run()