import time
import json
import networkx as nx
import os
import random
from experiment_configuration import ExperimentConfiguration
from GA_community import GACommunity  

class GAOptimization:
    def __init__(self, expconf, cnf, num_communities=3):
        self.expconf = expconf
        self.cnf = cnf
        self.G = expconf.G
        self.num_communities = num_communities
        self.fog_nodes = [n for n, d in self.G.nodes(data=True) if d.get('level', 'fog') == 'fog']
        self.all_nodes = list(self.G.nodes)
        self.cloud_id = expconf.cloud_id

    def calculateDistancesRequest(self, service2DevicePlacementMatrix):
        """
        Menghitung distribusi hop distance antara IoT device yang request dan node tempat service ditempatkan.
        Output: dict {hop_distance: jumlah}
        """
        distances = {}
        # Pastikan user_requests ada dan tidak kosong
        user_requests = getattr(self.expconf, "user_requests", None)
        if not user_requests or len(user_requests) == 0:
            print("[WARNING] user_requests kosong, delay tidak bisa dihitung!")
            return distances

        for iot_dev, service_id in user_requests:
            # Cek validitas index service_id
            if service_id < 0 or service_id >= len(service2DevicePlacementMatrix):
                print(f"[WARNING] service_id {service_id} di luar range!")
                continue
            placement_row = service2DevicePlacementMatrix[service_id]
            try:
                placed_dev = placement_row.index(1)
            except ValueError:
                print(f"[WARNING] Service {service_id} tidak ditempatkan di node manapun.")
                continue
            try:
                hop = nx.shortest_path_length(self.G, source=iot_dev, target=placed_dev)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                print(f"[WARNING] Tidak ada path dari IoT {iot_dev} ke node {placed_dev}.")
                continue
            distances[hop] = distances.get(hop, 0) + 1

        print(f"[INFO] Jumlah request dihitung: {len(user_requests)}")
        print(f"[INFO] Distribusi delay (hop): {distances}")
        return distances
    
    def calculateNodeUsage(self, service2DevicePlacementMatrix):
        nodeResUse = [0.0 for _ in self.G.nodes]
        nodeNumServ = [0 for _ in self.G.nodes]
        for idServ in range(len(service2DevicePlacementMatrix)):
            for idDev in range(len(service2DevicePlacementMatrix[idServ])):
                if service2DevicePlacementMatrix[idServ][idDev] == 1:
                    nodeNumServ[idDev] += 1
                    nodeResUse[idDev] += self.expconf.service_resources[idServ]
        for idDev in range(len(nodeResUse)):
            if self.expconf.node_resources[idDev] > 0:
                nodeResUse[idDev] = nodeResUse[idDev] / self.expconf.node_resources[idDev]
            else:
                nodeResUse[idDev] = 0.0
        nodeResUse = sorted(nodeResUse)
        nodeNumServ = sorted(nodeNumServ)
        
        return nodeResUse, nodeNumServ

    # ===================== GA Service Placement =====================
    def ga_service_placement(self, pop_size=30, generations=50, mutation_rate=0.1):
        # Pastikan cloud node sudah ada sebelum ambil node_ids
        if self.cloud_id not in self.G.nodes:
            self.G.add_node(self.cloud_id)
        node_ids = list(self.G.nodes)
        num_nodes = len(node_ids)
        service_resources = self.expconf.service_resources
        node_resources = self.expconf.node_resources
        cloud_id = self.cloud_id

        # Pastikan resource cloud ada
        if cloud_id not in node_resources:
            node_resources[cloud_id] = 1e12

        try:
            cloud_idx = node_ids.index(cloud_id)
        except ValueError:
            raise RuntimeError("Cloud node not found in node_ids after explicit add.")

        def random_chrom():
            return [random.randint(0, num_nodes-1) for _ in range(self.expconf.number_of_services)]

        def chrom_to_matrix(chrom):
            matrix = [[0 for _ in range(num_nodes)] for _ in range(self.expconf.number_of_services)]
            for sid, idx in enumerate(chrom):
                matrix[sid][idx] = 1
            return matrix

        def fitness(chrom):
            usage = [0.0 for _ in range(num_nodes)]
            
            for sid, idx in enumerate(chrom):
 
                if idx >= num_nodes:
                    raise ValueError(f"Chromosome index {idx} out of range for node_ids (len={num_nodes})")
                if sid in service_resources:
                    usage[idx] += service_resources[sid]
                else:
                    print(f"[ERROR] sid {sid} tidak ada di service_resources, diisi 0")
                    usage[idx] += 0
            penalty = 0
            for idx in range(num_nodes):
                if usage[idx] > node_resources[node_ids[idx]]:
                    penalty += 10000 * (usage[idx] - node_resources[node_ids[idx]])
            total_hop = 0
            if hasattr(self.expconf, "user_requests"):
                for iot_id, service_id in self.expconf.user_requests:
                    node_id = node_ids[chrom[service_id]]
                    try:
                        hop = nx.shortest_path_length(self.G, source=iot_id, target=node_id)
                    except:
                        hop = 100
                    total_hop += hop
            fog_penalty = sum(1 for idx in chrom if idx == cloud_idx) * 0.1
            return -(total_hop + penalty + fog_penalty)

        def selection(pop, fits):
            idx1, idx2 = random.sample(range(len(pop)), 2)
            return pop[idx1] if fits[idx1] > fits[idx2] else pop[idx2]

        def crossover(p1, p2):
            point = random.randint(1, self.expconf.number_of_services-1)
            return p1[:point] + p2[point:]

        def mutate(chrom):
            idx = random.randint(0, self.expconf.number_of_services-1)
            chrom[idx] = random.randint(0, num_nodes-1)
            return chrom

        population = [random_chrom() for _ in range(pop_size)]
        for gen in range(generations):
            fits = [fitness(ch) for ch in population]
            new_pop = []
            for _ in range(pop_size):
                p1 = selection(population, fits)
                p2 = selection(population, fits)
                child = crossover(p1, p2)
                if random.random() < mutation_rate:
                    child = mutate(child)
                new_pop.append(child)
            population = new_pop
        fits = [fitness(ch) for ch in population]
        best_idx = fits.index(max(fits))
        best_chrom = population[best_idx]
        return [node_ids[idx] for idx in best_chrom], chrom_to_matrix(best_chrom)
    # ===================== END GA Service Placement =====================

    def solve(self, verbose=True):
        t = time.time()
        print("=== GA Optimization (Service Placement) ===")

        # 1. Jalankan GA Service Placement
        best_chrom, service2DevicePlacementMatrixGA = self.ga_service_placement(
            pop_size=30, generations=50, mutation_rate=0.1
        )

        num_services = self.expconf.number_of_services
        node_ids = self.all_nodes
        node_id_to_idx = {nid: idx for idx, nid in enumerate(node_ids)}
        servicesInCloud = 0
        servicesInFog = 0
        allAlloc = {}
        myAllocationList = []

        for idServ, devId in enumerate(best_chrom):
            if devId == self.cloud_id:
                servicesInCloud += 1
            else:
                servicesInFog += 1
            myAllocation = {
                "app": self.expconf.map_service_to_apps[idServ],
                "module_name": self.expconf.map_service_id_to_service_name[idServ],
                "id_resource": devId
            }
            myAllocationList.append(myAllocation)

        # Statistik penggunaan node
        nodeResUseGA, nodeNumServGA = self.calculateNodeUsage(service2DevicePlacementMatrixGA)
        self.nodeResUseGA = nodeResUseGA
        self.nodeNumServGA = nodeNumServGA
        self.statisticsDistancesRequestGA = self.calculateDistancesRequest(service2DevicePlacementMatrixGA)
        print("Number of services in cloud (GA):", servicesInCloud)
        print("Number of services in fog (GA):", servicesInFog)

        # Average resource usage
        avg_resource_usage = sum(nodeResUseGA) / len(nodeResUseGA) if nodeResUseGA else 0
        print("Average Resource Usage (GA): {:.4f}".format(avg_resource_usage))

        allAlloc["initialAllocation"] = myAllocationList

        # Simpan ke appAllocation.json
        output_path = os.path.join(self.cnf.data_folder, "allocDefinitionGA.json")
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(output_path, "w") as file:
            file.write(json.dumps(allAlloc, indent=2))

        print("Allocation saved to", output_path)
        print(str(time.time() - t) + " seconds for GA-based")

if __name__ == "__main__":
    # 1. Load experiment configuration (no dummy, no halu)
    class Config:
        def __init__(self):
            self.data_folder = "."
            self.verbose_log = True
            self.graphic_terminal = False

    config = Config()
    expconf = ExperimentConfiguration(config)
    expconf.load_configuration("iotjournal")  # atau preset lain sesuai kebutuhanmu
    expconf.network_generation()
    expconf.app_generation()

    # 2. Jalankan GAOptimization
    gaopt = GAOptimization(expconf, config, num_communities=3)
    ga_matrix = gaopt.solve(verbose=True)
    print("GA Placement Matrix:")
    for row in ga_matrix:
        print(row)