import os, struct, re, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
GOM, TR = {}, {}
for o in env.objects:
    t = o.type.name
    if t == "GameObject":
        try:
            d = o.read()
            GOM[o.path_id] = (d.m_Name, [c.m_PathID for c in d.m_Component])
        except Exception:
            pass
    elif t in ("Transform", "RectTransform"):
        try:
            d = o.read()
            TR[o.path_id] = (d.m_GameObject.m_PathID, d.m_Father.m_PathID,
                             [c.m_PathID for c in d.m_Children])
        except Exception:
            pass
go2tr = {v[0]: k for k, v in TR.items()}
def comps(gid):
    tr = go2tr.get(gid)
    return TR.get(tr, (0, 0, [])) if tr else (0, 0, [])
print("==== 名称含 C4 / Ad / Banner / Promo 的 GameObject ====")
pat = re.compile(r"c4|_ad$|^ad$|ad_|banner|promo|wishlist|store", re.I)
for gid, (n, _) in GOM.items():
    if n and pat.search(n):
        print(" ", gid, "|", n)
print("==== C4Ad 子树 ====")
def walk(gid, depth):
    n, cl = GOM.get(gid, ("?", []))
    print("  " * depth + f"- {n} (go {gid})")
    _, _, kids = comps(gid)
    for k in kids:
        kgo = TR.get(k, (0,))[0]
        if depth < 4:
            walk(kgo, depth + 1)
for gid, (n, _) in GOM.items():
    if n == "C4Ad":
        par = comps(gid)[1]
        pgo = TR.get(par, (0,))[0]
        print("parent:", GOM.get(pgo, ("?",))[0])
        walk(gid, 0)
