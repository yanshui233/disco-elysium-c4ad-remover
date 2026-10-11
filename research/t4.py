import os, UnityPy, collections, re
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level2"))
print("objects:", len(env.objects))
cnt = collections.Counter()
for o in env.objects:
    cnt[o.type.name] += 1
print(cnt)
KEY = b"2863680"
print("==== 含广告链接的对象 ====")
for o in env.objects:
    raw = o.get_raw_data()
    if KEY in raw:
        print("--- pathid", o.path_id, "type", o.type.name)
        try:
            d = o.read()
            for a in ("m_Name", "m_Text", "m_ClassName", "m_GameObject"):
                v = getattr(d, a, None)
                if v is not None and not hasattr(v, "read"):
                    print("   ", a, "=", repr(v)[:300])
            go = getattr(d, "m_GameObject", None)
            if go is not None and hasattr(go, "read"):
                print("    m_GameObject ->", go.read().m_Name)
            sc = getattr(d, "m_Script", None)
            if sc is not None and hasattr(sc, "read"):
                print("    script ->", sc.read().m_ClassName)
        except Exception as e:
            print("    (read err)", e)
