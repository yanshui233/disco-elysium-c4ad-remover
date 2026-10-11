import UnityPy
p = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data/StreamingAssets/AssetBundles/Windows/images/english"
env = UnityPy.load(p)
print("files:", list(env.files.keys()))
for k, f in env.files.items():
    print("key:", k, "type:", type(f).__name__, "objs:", len(getattr(f, "objects", []) or []))
print("container:", len(env.container))
for k, v in list(env.container.items())[:10]:
    print("  ", k, "->", v)
