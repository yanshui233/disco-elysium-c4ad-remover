import os, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "globalgamemanagers"))
print("objects:", len(env.objects))
types = {}
for o in env.objects:
    types[o.type.name] = types.get(o.type.name, 0) + 1
print(types)
for o in env.objects:
    if o.type.name == "BuildSettings":
        d = o.read()
        print("BuildSettings attrs:", [a for a in dir(d) if not a.startswith("_")][:40])
        sc = getattr(d, "scenes", None)
        print("scenes:", type(sc), sc if isinstance(sc, (list, tuple)) else "")
        break
