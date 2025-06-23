import json
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
    with open(json_path) as f:
        app_defs = json.load(f)
    apps = []
    for app_def in app_defs:
        if not app_def or "name" not in app_def:
            continue
        app = Application(name=app_def["name"])
        # Tambah semua module (tanpa message_in, agar semua module terdaftar)
        for module in app_def.get("module", []):
            app.add_service_module(module["name"], None)
        # Tambah source module: modul tujuan pesan dari user (s == "None")
        for msg in app_def.get("message", []):
            if msg.get("s") == "None" and "d" in msg:
                app.add_service_source(msg["d"])
        # Tambah transmission (source messages) - hanya module saja!
        for tr in app_def.get("transmission", []):
            if "module" in tr and "message_in" not in tr:
                app.add_source_messages(tr["module"])
        apps.append(app)
    return apps

def load_placement(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return JSONPlacement(name="Placement", json=data)

def load_population(json_path):
    with open(json_path) as f:
        pop_def = json.load(f)
    population = Statical(name="UserPopulation")
    for user in pop_def.get("sources", []):
       
        node = user["id_resource"]
        app = user["app"]
        message = user["message"]
        lam = user["lambda"]
        distribution = {"name": "Deterministic", "param": {"time": lam}}
        population.set_src_control({
            "id_resource": node,
            "app": app,
            "message": message,
            "distribution": distribution,
            "number": 1,
            "model": "None"
        })
        
    return population

def get_selection():
    return First_ShortestPath()
