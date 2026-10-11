import os, re, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
OBJ = {o.path_id: o for o in env.objects}
def go_of(name):
    for pid, o in OBJ.items():
        if o.type.name == "GameObject":
            try:
                if o.read().m_Name == name: return pid
            except Exception: pass
ad = go_of("C4Ad")
d = OBJ[ad].read()
print("C4Ad pathid:", ad, "m_IsActive:", d.m_IsActive, "layer:", d.m_Layer, "tag:", d.m_Tag)
print("== 组件 ==")
for c in d.m_Component:
    pid = c.component.m_PathID
    o = OBJ.get(pid)
    t = o.type.name if o else "?"
    extra = ""
    if o and t == "MonoBehaviour":
        r = o.read()
        try: extra = "class=" + r.m_Script.read().m_ClassName
        except Exception as e: extra = "class?(%s)" % str(e)[:60]
        try:
            ss = [s.decode() for s in re.findall(rb"[ -~]{5,}", o.get_raw_data())]
            extra += " strings=" + " | ".join(ss[:4])
        except Exception: pass
    print(f"  {pid} {t} {extra[:400]}")
print("== 父链 m_IsActive ==")
TR = {}
for pid, o in OBJ.items():
    if o.type.name in ("Transform", "RectTransform"):
        try:
            r = o.read(); TR[pid] = (r.m_GameObject.m_PathID, r.m_Father.m_PathID)
        except Exception: pass
go2tr = {v[0]: k for k, v in TR.items()}
cur = ad
for _ in range(6):
    tr = go2tr.get(cur)
    if not tr: break
    gid = TR[tr][0]
    try: g = OBJ[gid].read()
    except Exception: break
    print("  ", g.m_Name, "active=", g.m_IsActive)
    f = TR[tr][1]
    if not f: break
    cur = TR.get(f, (0, 0))[0]
    if not cur: break
