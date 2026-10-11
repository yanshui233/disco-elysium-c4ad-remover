import struct, sys
C = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
for fn in ("level2", "level2.c4ad-backup"):
    p = C + "\\" + fn
    try:
        data = open(p, "rb").read()
    except OSError as e:
        print(fn, "MISSING", e); continue
    needle = struct.pack("<i", 4) + b"C4Ad"
    hits = []
    i = data.find(needle)
    while i != -1:
        hits.append(i)
        i = data.find(needle, i + 1)
    print(f"=== {fn}  size={len(data)}  hits={len(hits)}")
    for h in hits:
        active = data[h + 10]
        tag = struct.unpack_from("<H", data, h + 8)[0]
        ctx_after = data[h + 11:h + 24]
        print(f"   name_hdr_off={h}  tag={tag}  is_active@ {h+10} = {active}   after={ctx_after!r}")
