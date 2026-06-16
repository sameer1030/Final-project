import traci
import csv
import os

SUMO_BINARY = "sumo-gui"
SUMO_CONFIG = "sumo/simulation.sumocfg"
TRAFFIC_LIGHT_ID = "J1"

LANES = {
    "north": "E0_0",
    "south": "-E1_0",
    "west": "-E2_0",
    "east": "-E3_0",
}

MIN_GREEN_TIME = 20
SIMULATION_STEPS = 500
RESULTS_FILE = "results/adaptive_results.csv"


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_total_waiting_time():
    return sum(
        traci.vehicle.getWaitingTime(vehicle_id)
        for vehicle_id in traci.vehicle.getIDList()
    )


def run():
    os.makedirs("results", exist_ok=True)

    traci.start([SUMO_BINARY, "-c", SUMO_CONFIG])

    current_phase = traci.trafficlight.getPhase(TRAFFIC_LIGHT_ID)
    last_switch = 0

    print("Traffic Light ID:", TRAFFIC_LIGHT_ID)
    print("Initial Phase:", current_phase)
    print("Program Logic:", traci.trafficlight.getAllProgramLogics(TRAFFIC_LIGHT_ID))

    with open(RESULTS_FILE, mode="w", newline="") as file:
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

            if step - last_switch >= MIN_GREEN_TIME:
                if ns_queue >= ew_queue:
                    traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, 0)
                    current_phase = 0
                else:
                    traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, 2)
                    current_phase = 2

                last_switch = step

            vehicles_in_simulation = traci.vehicle.getIDCount()
            total_waiting_time = get_total_waiting_time()
            completed_vehicles = traci.simulation.getArrivedNumber()

            writer.writerow([
                step,
                ns_queue,
                ew_queue,
                current_phase,
                vehicles_in_simulation,
                total_waiting_time,
                completed_vehicles
            ])

            print(
                f"Step {step} | NS={ns_queue} | EW={ew_queue} | "
                f"Phase={current_phase} | Waiting={total_waiting_time}",
                flush=True
            )

    traci.close()
    print("Adaptive controller completed. Results saved to results/adaptive_results.csv")


if __name__ == "__main__":
    run()