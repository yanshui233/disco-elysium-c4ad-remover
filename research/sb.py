import os, re, sys, UnityPy
KW = re.compile(r"zero|parade|promo|banner|store|buy|news|upsell|sponsor|zaum|link|shop", re.I)
for p in sys.argv[1:]:
    print("=" * 10, os.path.basename(p))
    try:
        env = UnityPy.load(p)
    except Exception as e:
        print("  load fail:", e); continue
    cnt = {}
    hits = []
    tot = 0
    for o in env.objects:
        tot += 1
        t = o.type.name
        cnt[t] = cnt.get(t, 0) + 1
        try:
            d = o.read()
            n = getattr(d, "m_Name", None) or getattr(d, "name", None)
        except Exception:
            n = None
        if n and KW.search(str(n)):
            hits.append(f"{t} | {n}")
    print("  objects:", tot, cnt)
    for h in hits[:40]:
        print("  HIT", h)
