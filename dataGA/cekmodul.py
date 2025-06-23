import json

APP_DEF_PATH = "dataGA/appDefinition.json"
ALLOC_PATH = "dataGA/allocDefinitionGA.json"

def get_all_source_modules(app_defs):
    # Kembalikan dict: {app_name: set([source_module, ...])}
    sources = {}
    for app in app_defs:
        if not app or "name" not in app or "message" not in app:
            continue
        app_name = str(app["name"])
        for msg in app["message"]:
            if msg.get("s") == "None" and "d" in msg:
                sources.setdefault(app_name, set()).add(msg["d"])
    return sources

def main():
    # Load appDefinition.json
    with open(APP_DEF_PATH) as f:
        app_defs = json.load(f)
    source_modules = get_all_source_modules(app_defs)

    # Load allocDefinitionGA.json
    with open(ALLOC_PATH) as f:
        alloc = json.load(f)
    allocated = set()
    for entry in alloc.get("initialAllocation", []):
        app = str(entry.get("app"))
        mod = entry.get("module_name")
        if app and mod:
            allocated.add((app, mod))

    # Cari source module yang belum dialokasikan
    to_add = []
    for app, mods in source_modules.items():
        for mod in mods:
            if (app, mod) not in allocated:
                # Pilih id_resource default (misal: 0), bisa kamu ganti sesuai kebutuhan
                to_add.append({"app": app, "module_name": mod, "id_resource": 0})

    if to_add:
        print(f"Menambahkan {len(to_add)} source module yang belum dialokasikan ke allocDefinitionGA.json")
        alloc["initialAllocation"].extend(to_add)
        with open(ALLOC_PATH, "w") as f:
            json.dump(alloc, f, indent=2)
    else:
        print("Semua source module sudah dialokasikan.")

if __name__ == "__main__":
    main()