import os, struct, UnityPy, re
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
objs = {o.path_id: o for o in env.objects}
ad = objs[31065]
raw = ad.get_raw_data()
print("raw len:", len(raw))
print("head hex:", raw[:24].hex())
goid = struct.unpack_from("<q", raw, 4)[0]
sid = struct.unpack_from("<q", raw, 16)[0]
print("m_GameObject pathid:", goid, " m_Script pathid:", sid)
def name_of(pid):
    o = objs.get(pid)
    if not o: return None
    try:
        return o.read().m_Name
    except Exception:
        return "<read err>"
print("GameObject name:", name_of(goid))
if sid in objs:
    try:
        print("script class:", objs[sid].read().m_ClassName)
    except Exception as e:
        print("script read err", e)
print("==== 对象内可读字符串 ====")
for s in re.findall(rb"[ -~]{4,}", raw):
    print("   ", s.decode("ascii", "ignore"))
