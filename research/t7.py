import os, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
ok = 0; bad = 0; msg = ""
names = []
for o in env.objects:
    if o.type.name == "GameObject":
        try:
            d = o.read()
            names.append(d.m_Name)
            ok += 1
        except Exception as e:
            bad += 1
            if not msg: msg = str(e)
print("GameObject ok:", ok, "bad:", bad, "err:", msg)
print("sample:", names[:15])
print("count with C4:", [n for n in names if "C4" in n or "c4" in n])
