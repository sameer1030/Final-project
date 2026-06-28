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

SIMULATION_STEPS = 500
PHASE_DURATION = 30


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_total_waiting_time():
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.vehicle.getIDList()
    )


def run_scenario(scenario_name, sumo_config):
    results_file = f"results/fixed_{scenario_name}_results.csv"

    traci.start([SUMO_BINARY, "-c", sumo_config])

    with open(results_file, mode="w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "step",
            "ns_queue",
            "ew_queue",
            "active_phase",
            "vehicles_in_simulation",
            "total_waiting_time",
            "completed_vehicles"
        ])

        for step in range(SIMULATION_STEPS):
            traci.simulationStep()

            ns_queue = (
                get_queue_length(LANES["north"]) +
                get_queue_length(LANES["south"])
            )

            ew_queue = (
                get_queue_length(LANES["west"]) +
                get_queue_length(LANES["east"])
            )

            if (step // PHASE_DURATION) % 2 == 0:
                active_phase = "NS_GREEN"
                traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, 0)
            else:
                active_phase = "EW_GREEN"
                traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, 2)

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
                completed_vehicles
            ])

            print(
                f"[FIXED - {scenario_name.upper()}] Step {step} | "
                f"NS={ns_queue} | EW={ew_queue} | "
                f"Phase={active_phase} | Waiting={total_waiting_time}",
                flush=True
            )

    traci.close()
    print(f"Fixed-time {scenario_name} scenario completed.")


def run():
    os.makedirs("results", exist_ok=True)

    for scenario_name, sumo_config in SCENARIOS.items():
        run_scenario(scenario_name, sumo_config)

    print("All fixed-time scenarios completed.")


if __name__ == "__main__":
    run()