import os, re, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
OBJ = {o.path_id: o for o in env.objects}
GOM, TR = {}, {}
for pid, o in OBJ.items():
    if o.type.name == "GameObject":
        try:
            d = o.read(); GOM[pid] = (d.m_Name, [c.component.m_PathID for c in d.m_Component])
        except Exception: pass
    elif o.type.name in ("Transform", "RectTransform"):
        try:
            d = o.read(); TR[pid] = (d.m_GameObject.m_PathID, d.m_Father.m_PathID, [c.m_PathID for c in d.m_Children])
        except Exception: pass
go2tr = {v[0]: k for k, v in TR.items()}
def tinfo(gid):
    tr = go2tr.get(gid)
    return TR.get(tr, (0, 0, [])) if tr else (0, 0, [])
def strings_of(pid):
    o = OBJ.get(pid)
    if not o or o.type.name != "MonoBehaviour": return None
    try: raw = o.get_raw_data()
    except Exception: return None
    return [s.decode() for s in re.findall(rb"[ -~]{5,}", raw)]
def ctypes(gid):
    out = []
    for c in GOM.get(gid, ("", []))[1]:
        o = OBJ.get(c)
        if o is None: continue
        t = o.type.name
        if t == "MonoBehaviour":
            try:
                t = "MB:" + o.read().m_Script.read().m_ClassName
            except Exception:
                t = "MB:?"
        out.append(t)
    return out
def walk(gid, depth, lines):
    n = GOM.get(gid, ("?",))[0]
    lines.append("  " * depth + f"- {n}  [{', '.join(ctypes(gid))}]")
    for c in GOM.get(gid, ("", []))[1]:
        s = strings_of(c)
        if s:
            for x in s[:6]:
                lines.append("  " * (depth + 1) + "str> " + x[:120])
    _, _, kids = tinfo(gid)
    if depth < 6:
        for k in kids:
            walk(TR.get(k, (0,))[0], depth + 1, lines)
for gid, (n, _) in GOM.items():
    if n == "C4Ad":
        out = []
        f = tinfo(gid)[1]; pgo = TR.get(f, (0,))[0]
        out.append("parent: " + GOM.get(pgo, ("<none>",))[0] + " / " + GOM.get(pgo, ("",))[0])
        p = pgo
        for _ in range(3):
            f = tinfo(p)[1]; p = TR.get(f, (0,))[0]
            if not p: break
            out.append("  ^ " + GOM.get(p, ("<none>",))[0])
        walk(gid, 0, out)
        print("\n".join(out))
        break
