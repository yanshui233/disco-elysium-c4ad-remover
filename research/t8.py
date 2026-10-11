import os, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
for o in env.objects:
    if o.type.name == "GameObject":
        d = o.read()
        if d.m_Name == "C4Ad":
            print("GameObject attrs:", [a for a in dir(d) if not a.startswith("__")])
            print("m_Component type:", type(d.m_Component), d.m_Component)
            break
for o in env.objects:
    if o.type.name in ("Transform", "RectTransform"):
        d = o.read()
        print("Transform class:", type(d).__name__, "attrs:", [a for a in dir(d) if not a.startswith("__")])
        break
