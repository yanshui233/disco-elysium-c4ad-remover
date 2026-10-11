import os, struct, UnityPy
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
P = os.path.join(DATA, "level2")
env = UnityPy.load(P)
target = None
for o in env.objects:
    if o.type.name == "GameObject":
        try:
            if o.read().m_Name == "C4Ad":
                target = o; break
        except Exception: pass
print("pathid:", target.path_id)
for a in ("byte_start", "byte_size", "set_raw_data"):
    print(a, "=", getattr(target, a, "<none>"))
raw = target.get_raw_data()
print("raw len:", len(raw))
cnt = struct.unpack_from("<i", raw, 0)[0]
print("component count:", cnt)
off = 4 + 12 * cnt
layer = struct.unpack_from("<i", raw, off)[0]
nlen = struct.unpack_from("<i", raw, off + 4)[0]
name = raw[off + 8: off + 8 + nlen].decode("utf8", "replace")
nxt = off + 8 + nlen
nxt += (-nxt) % 4
tag = struct.unpack_from("<H", raw, nxt)[0]
print("layer:", layer, "name:", repr(name), "tag:", tag, "isActive off:", nxt + 2, "val:", raw[nxt + 2])
print("computed is_active_file_off:", (getattr(target, 'byte_start', 0) or 0) + nxt + 2)
with open(P, "rb") as f:
    f.seek((getattr(target, 'byte_start', 0) or 0))
    got = f.read(len(raw))
print("file bytes match raw:", got == raw)
