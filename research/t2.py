import os, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
p = os.path.join(DATA, "level3")
env = UnityPy.load(p)
types = {}
names = []
for o in env.objects:
    t = o.type.name
    types[t] = types.get(t, 0) + 1
print("types:", types)
for o in env.objects:
    if o.type.name in ("GameObject", "Sprite", "Texture2D", "Material"):
        try:
            d = o.read()
            n = getattr(d, "m_Name", None)
            if n:
                names.append((o.type.name, n))
        except Exception as e:
            pass
for t, n in names:
    print(t, "|", n)
