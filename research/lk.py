import os, re, UnityPy
B = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data/StreamingAssets/AssetBundles/Windows/lockits/english"
env = UnityPy.load(B)
print("container keys:", list(env.container.keys())[:10])
for k, f in env.files.items():
    print("file:", type(f).__name__, "objs:", len(getattr(f, "objects", []) or []))
    for o in getattr(f, "objects", []) or []:
        print("  ", o.type.name, o.path_id)
        if o.type.name == "TextAsset":
            d = o.read()
            t = d.m_Script if hasattr(d, "m_Script") else getattr(d, "m_Text", "")
            hits = [l for l in str(t).splitlines() if "C4" in l]
            print("     name:", getattr(d, "m_Name", "?"), "C4 lines:", hits[:10])
