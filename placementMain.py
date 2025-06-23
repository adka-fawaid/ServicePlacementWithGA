import json
from my_plot import GAPlots
import my_config
import experiment_configuration
import GA_Optimization
import GA_community

def run_my_config():
    print("\n=== Running my_config ===")
    cnf = my_config.MyConfig()
    print("Config:", vars(cnf))

def run_experiment_configuration():
    print("\n=== Running experiment_configuration ===")
    cnf = my_config.MyConfig()
    ec = experiment_configuration.ExperimentConfiguration(cnf)
    ec.load_configuration(cnf.my_configuration)
    ec.network_generation()
    ec.app_generation()
    ec.user_generation()
    print("ExperimentConfiguration loaded.")

def run_GA_Optimization():
    print("\n=== Running GA_Optimization ===")
    cnf = my_config.MyConfig()
    ec = experiment_configuration.ExperimentConfiguration(cnf)
    ec.load_configuration(cnf.my_configuration)
    ec.network_generation()
    ec.app_generation()
    ec.user_generation()
    gaopt = GA_Optimization.GAOptimization(ec, cnf)
    gaopt.solve(verbose=False)
    print("GA_Optimization selesai.")

def run_GA_community():
    print("\n=== Running GA_community ===")
    import networkx as nx
    import random
    G = nx.erdos_renyi_graph(10, 0.3)
    for n in G.nodes:
        G.nodes[n]['RAM'] = random.randint(1, 8)
        G.nodes[n]['STO'] = random.randint(10, 100)
        G.nodes[n]['IPT'] = random.randint(100, 1000)
    ga = GA_community.GACommunity(G, num_communities=3, generations=10)
    best_community, best_fitness = ga.run()
    print("Best community assignment:", best_community)
    print("Best fitness:", best_fitness)

if __name__ == "__main__":
    run_my_config()
    run_experiment_configuration()

    # 1. Baca appDefinition.json (setelah experiment_configuration dijalankan)
    with open("dataGA/appDefinition.json") as f:
        app_defs = json.load(f)

    # 2. Buat list jumlah aplikasi yang ingin diuji 
    max_app = len(app_defs)
    jumlah_aplikasi_list = list(range(1, max_app + 1)) 

    ga_results = []

    for jumlah_aplikasi in jumlah_aplikasi_list:
        # 3. Ambil subset aplikasi yang akan disimulasikan
        apps = app_defs[:jumlah_aplikasi]
        # 4. Hitung total service/module yang akan disimulasikan
        total_services = sum(len(app['module']) for app in apps)

        cnf_ = my_config.MyConfig()
        cnf_.number_of_services = total_services  # jika dipakai di config
        ec = experiment_configuration.ExperimentConfiguration(cnf_)
        ec.load_configuration(cnf_.my_configuration)
        ec.network_generation()
        ec.app_generation()
        ec.user_generation()
        ec.number_of_services = total_services

        if not hasattr(ec, "user_requests") or not ec.user_requests:
            ec.user_requests = []
            for user in getattr(ec, "my_users", []):
                iot_id = user["id_resource"]
                for service_id in range(ec.number_of_services):
                    ec.user_requests.append((iot_id, service_id))

        ga_ = GA_Optimization.GAOptimization(ec, cnf_)
        service2DevicePlacementMatrixGA = ga_.solve()
        ga_.service2DevicePlacementMatrixGA = service2DevicePlacementMatrixGA
        ga_results.append(ga_)

    # # 6. Plot hasil
    plotter = GAPlots(ga_results, cnf_)
    plotter.plot_all()

    run_GA_Optimization()
    run_GA_community()