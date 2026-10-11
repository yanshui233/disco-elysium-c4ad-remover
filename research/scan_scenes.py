import os, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "globalgamemanagers"))
for obj in env.objects:
    if obj.type.name == "BuildSettings":
        d = obj.read()
        scenes = getattr(d, "scenes", None)
        print("scene count:", len(scenes) if scenes else 0)
        for i, s in enumerate(scenes or []):
            print(i, getattr(s, "path", s))
