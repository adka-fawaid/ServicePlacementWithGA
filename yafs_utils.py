import os
import json
import csv
from yafs.core import Sim
from yafs.application import Application
from yafs.placement import JSONPlacement
from yafs.population import Statical
from yafs.topology import Topology
from yafs.selection import First_ShortestPath

def load_topology(json_path):
    with open(json_path) as f:
        data = json.load(f)
    topo = Topology()
    topo.load(data)
    return topo

def load_applications(json_path):
    from yafs.application import Application
    with open(json_path) as f:
        app_defs = json.load(f)
    apps = []
    for app_def in app_defs:
        if not app_def or "name" not in app_def:
            continue
        app = Application(name=app_def["name"])
        app.load(app_def)
        apps.append(app)
    return apps

def load_placement(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return JSONPlacement(name="GA Placement", json=data)

def load_population(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return Statical(data)

def get_selection():
    return First_ShortestPath()

def export_yafs_metrics_to_csv(data_folder="dataGA"):
    events_path = os.path.join(data_folder, "events_log.json")
    csv_path = os.path.join(data_folder, "dataGA.csv")
    if not os.path.exists(events_path):
        print(f"[export_yafs_metrics_to_csv] File {events_path} tidak ditemukan.")
        return
    with open(events_path) as f:
        events = json.load(f)
    fieldnames = [
        "id", "type", "app", "module", "message", "DES.src", "DES.dst",
        "TOPO.src", "TOPO.dst", "module.src", "service",
        "time_in", "time_out", "time_emit", "time_reception"
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, event in enumerate(events):
            row = {k: event.get(k, "") for k in fieldnames}
            row["id"] = i
            writer.writerow(row)

def analyze_placement_usage(alloc_path, topo_path):
    with open(alloc_path) as f:
        alloc = json.load(f)
    with open(topo_path) as f:
        topo = json.load(f)
    node_count = {str(n["id"]): 0 for n in topo["entity"]}
    for item in alloc["initialAllocation"]:
        node_id = str(item["id_resource"])
        node_count[node_id] = node_count.get(node_id, 0) + 1
    print("\n=== Placement Usage (Jumlah service/module per node) ===")
    for nid, count in node_count.items():
        print(f"Node {nid}: {count} module(s)")

def analyze_resource_usage(alloc_path, topo_path):
    with open(alloc_path) as f:
        alloc = json.load(f)
    with open(topo_path) as f:
        topo = json.load(f)
    node_resource = {str(n["id"]): n.get("RAM", 1) for n in topo["entity"]}
    node_usage = {str(n["id"]): 0 for n in topo["entity"]}
    for item in alloc["initialAllocation"]:
        node_id = str(item["id_resource"])
        node_usage[node_id] = node_usage.get(node_id, 0) + 1
    print("\n=== Resource Usage (Persentase pemakaian RAM tiap node) ===")
    for nid in node_resource:
        usage = node_usage[nid]
        total = node_resource[nid]
        percent = (usage / total) * 100 if total else 0
        print(f"Node {nid}: {usage}/{total} module(s) ({percent:.2f}%)")

def analyze_delay(csv_path):
    delays = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t_in = float(row["time_in"])
                t_out = float(row["time_out"])
                delays.append(t_out - t_in)
            except:
                continue
    if delays:
        avg_delay = sum(delays) / len(delays)
        print(f"\n=== Delay/Latensi ===\nRata-rata delay: {avg_delay:.4f} time unit ({len(delays)} event)")
    else:
        print("\n=== Delay/Latensi ===\nTidak ada data delay.")