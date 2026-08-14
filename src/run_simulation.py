"""
Fixed-Time Traffic Signal Controller

MSc Project
Dublin City University

Author: Sameer Srinivas

Implements the baseline fixed-time traffic signal controller used
for comparison with the proposed WATSC.
"""
import traci

SUMO_BINARY = "sumo-gui"
SUMO_CONFIG = "sumo/simulation.sumocfg"
TRAFFIC_LIGHT_ID = "J1"

LANES = {
    "north": "E0_0",
    "south": "-E1_0",
    "west": "-E2_0",
    "east": "-E3_0",
}

NS_GREEN = "GGgrrrGGgrrr"
EW_GREEN = "rrrGGGrrrGGG"

MIN_GREEN_TIME = 20

def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)

def run():
    traci.start([SUMO_BINARY, "-c", SUMO_CONFIG])

    current_phase = "NS"
    last_switch = 0

    for step in range(300):
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

            if ew_queue > ns_queue and current_phase != "EW":
                current_phase = "EW"
                last_switch = step

            elif ns_queue >= ew_queue and current_phase != "NS":
                current_phase = "NS"
                last_switch = step

        if current_phase == "NS":
            traci.trafficlight.setRedYellowGreenState(
                TRAFFIC_LIGHT_ID,
                NS_GREEN
            )
        else:
            traci.trafficlight.setRedYellowGreenState(
                TRAFFIC_LIGHT_ID,
                EW_GREEN
            )

        print(
            f"Step {step} | NS={ns_queue} | EW={ew_queue} | Phase={current_phase}",
            flush=True
        )

    traci.close()

if __name__ == "__main__":
    run()