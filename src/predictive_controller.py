import csv
import os
from collections import deque

import traci


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

# Signal-control constraints
MIN_GREEN = 12
MAX_GREEN = 35
CHECK_INTERVAL = 5
SWITCH_ADVANTAGE = 4

# Prediction settings
HISTORY_SIZE = 5
PREDICTION_HORIZON = 5


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_vehicle_count(lane_id):
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_waiting_time(lane_id):
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.lane.getLastStepVehicleIDs(lane_id)
    )


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
    vehicles = sum(get_vehicle_count(lane) for lane in lanes)
    waiting = sum(get_lane_waiting_time(lane) for lane in lanes)

    # Current traffic pressure
    score = (
        queue * 3.5
        + vehicles * 1.2
        + waiting * 0.2
    )

    return queue, vehicles, waiting, score


def predict_score(current_score, score_history):
    """
    Predicts short-term traffic pressure using the recent score trend.
    Only a positive trend increases the prediction, preventing falling
    traffic demand from being exaggerated.
    """
    score_history.append(current_score)

    if len(score_history) < 2:
        return current_score, 0.0

    trend = (
        score_history[-1] - score_history[0]
    ) / (len(score_history) - 1)

    predicted_score = current_score + (
        max(trend, 0) * PREDICTION_HORIZON
    )

    return max(predicted_score, 0), trend


def classify_traffic(score):
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
    results_file = (
        f"results/predictive_{scenario_name}_results.csv"
    )

    ns_history = deque(maxlen=HISTORY_SIZE)
    ew_history = deque(maxlen=HISTORY_SIZE)

    traci.start([SUMO_BINARY, "-c", sumo_config])

    current_phase = "NS"
    current_sumo_phase = NS_PHASE
    last_switch_step = 0

    traci.trafficlight.setPhase(
        TRAFFIC_LIGHT_ID,
        current_sumo_phase
    )

    try:
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
                "ns_current_score",
                "ew_current_score",
                "ns_predicted_score",
                "ew_predicted_score",
                "ns_score_trend",
                "ew_score_trend",
                "chosen_direction",
                "traffic_level",
                "elapsed_green",
                "vehicles_in_simulation",
                "total_waiting_time",
                "completed_vehicles",
            ])

            for step in range(SIMULATION_STEPS):
                traci.simulationStep()

                (
                    ns_queue,
                    ns_vehicles,
                    ns_waiting,
                    ns_score,
                ) = get_direction_metrics("NS")

                (
                    ew_queue,
                    ew_vehicles,
                    ew_waiting,
                    ew_score,
                ) = get_direction_metrics("EW")

                ns_predicted, ns_trend = predict_score(
                    ns_score,
                    ns_history
                )

                ew_predicted, ew_trend = predict_score(
                    ew_score,
                    ew_history
                )

                if current_phase == "NS":
                    current_predicted = ns_predicted
                    opposite_predicted = ew_predicted
                    opposite_phase = "EW"
                    opposite_sumo_phase = EW_PHASE
                else:
                    current_predicted = ew_predicted
                    opposite_predicted = ns_predicted
                    opposite_phase = "NS"
                    opposite_sumo_phase = NS_PHASE

                elapsed_green = step - last_switch_step
                should_switch = False

                # Mandatory maximum prevents starvation
                if elapsed_green >= MAX_GREEN:
                    should_switch = True

                # Predictive decision after minimum green
                elif (
                    elapsed_green >= MIN_GREEN
                    and elapsed_green % CHECK_INTERVAL == 0
                ):
                    if (
                        current_predicted == 0
                        and opposite_predicted > 0
                    ):
                        should_switch = True

                    elif (
                        opposite_predicted
                        >= current_predicted + SWITCH_ADVANTAGE
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

                selected_predicted_score = (
                    ns_predicted
                    if current_phase == "NS"
                    else ew_predicted
                )

                traffic_level = classify_traffic(
                    selected_predicted_score
                )

                vehicles_in_simulation = (
                    traci.vehicle.getIDCount()
                )

                total_waiting_time = (
                    get_total_waiting_time()
                )

                completed_vehicles = (
                    traci.simulation.getArrivedNumber()
                )

                writer.writerow([
                    step,
                    ns_queue,
                    ew_queue,
                    ns_vehicles,
                    ew_vehicles,
                    round(ns_waiting, 2),
                    round(ew_waiting, 2),
                    round(ns_score, 2),
                    round(ew_score, 2),
                    round(ns_predicted, 2),
                    round(ew_predicted, 2),
                    round(ns_trend, 2),
                    round(ew_trend, 2),
                    current_phase,
                    traffic_level,
                    elapsed_green,
                    vehicles_in_simulation,
                    round(total_waiting_time, 2),
                    completed_vehicles,
                ])

                print(
                    f"[PREDICTIVE - {scenario_name.upper()}] "
                    f"Step {step} | "
                    f"NS predicted={ns_predicted:.2f} | "
                    f"EW predicted={ew_predicted:.2f} | "
                    f"Direction={current_phase} | "
                    f"Waiting={total_waiting_time:.2f}",
                    flush=True
                )

    finally:
        traci.close()

    print(
        f"Predictive {scenario_name} scenario completed."
    )
    print(f"Saved to {results_file}")


def run():
    os.makedirs("results", exist_ok=True)

    for scenario_name, sumo_config in SCENARIOS.items():
        run_scenario(scenario_name, sumo_config)

    print("All predictive scenarios completed.")


if __name__ == "__main__":
    run()