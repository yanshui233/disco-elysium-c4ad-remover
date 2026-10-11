import os, UnityPy
B = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(B, "level3"))
for f in env.files.values():
    print("file:", getattr(f, "name", "?"), "| unity:", getattr(f, "unity_version", "?"), "| type:", type(f).__name__)
