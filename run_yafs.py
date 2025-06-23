import os
from yafs_utils import (
    load_topology, load_applications, load_placement, load_population, get_selection,
    export_yafs_metrics_to_csv,
    analyze_placement_usage, analyze_resource_usage, analyze_delay
)

DATA_FOLDER = "dataGA"

def main():
    # 1. Load semua konfigurasi
    topo = load_topology(os.path.join(DATA_FOLDER, "networkDefinition.json"))
    apps = load_applications(os.path.join(DATA_FOLDER, "appDefinition.json"))
    placement = load_placement(os.path.join(DATA_FOLDER, "allocDefinitionGA.json"))
    population = load_population(os.path.join(DATA_FOLDER, "usersDefinition.json"))
    selection = get_selection()

    # 2. Jalankan simulasi YAFS
    from yafs.core import Sim
    sim = Sim(topo, default_results_path=DATA_FOLDER)
    for app in apps:
        sim.deploy_app(app, placement, population)
    print("Mulai simulasi...")
    sim.run(until=1000000000)
    print("Simulasi selesai.")
    # 3. Ekspor hasil ke CSV
    export_yafs_metrics_to_csv(DATA_FOLDER)

    # 4. Analisis hasil
    analyze_placement_usage(
        os.path.join(DATA_FOLDER, "allocDefinitionGA.json"),
        os.path.join(DATA_FOLDER, "networkDefinition.json")
    )
    analyze_resource_usage(
        os.path.join(DATA_FOLDER, "allocDefinitionGA.json"),
        os.path.join(DATA_FOLDER, "networkDefinition.json")
    )
    analyze_delay(os.path.join(DATA_FOLDER, "dataGA.csv"))

if __name__ == "__main__":
    main()