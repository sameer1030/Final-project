import traci
import os

SUMO_BINARY = "sumo-gui"
SUMO_CONFIG = "sumo/simulation.sumocfg"

def run():
    traci.start([SUMO_BINARY, "-c", SUMO_CONFIG])

    step = 0

    while step < 100:
        traci.simulationStep()

        vehicle_count = traci.vehicle.getIDCount()
        print(f"Step {step}: Vehicles = {vehicle_count}")

        step += 1

    traci.close()

if __name__ == "__main__":
    run()