import os
import csv
from yafs.core import Sim
from yafs_utils import load_topology, load_applications, load_placement, load_population, get_selection

DATA_FOLDER = "dataGA"

def main():
    # 1. Load topology
    topo = load_topology(os.path.join(DATA_FOLDER, "networkDefinition.json"))

    # 2. Load applications
    apps = load_applications(os.path.join(DATA_FOLDER, "appDefinition.json"))

    # 3. Load placement (allocation from GA)
    placement = load_placement(os.path.join(DATA_FOLDER, "allocDefinitionGA.json"))

    # 4. Load population (user requests)
    population = load_population(os.path.join(DATA_FOLDER, "usersDefinition.json"))

    # 5. Selection (routing)
    selection = get_selection()

    # 6. Simulasi
    sim = Sim(topo, default_results_path=DATA_FOLDER)
    for app in apps:
        sim.deploy_app(app, placement, population)
    sim.run(until=1000000000)  # Run for 1000000000 time units

if __name__ == "__main__":
    main()