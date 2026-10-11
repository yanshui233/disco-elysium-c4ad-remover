import os, re, sys, UnityPy
KW = re.compile(r"zero|parade|promo|banner|store|buy|news|upsell|sponsor|zaum|marquee|ticker", re.I)
B = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data/StreamingAssets/AssetBundles/Windows"
files = []
for root, dirs, fs in os.walk(B):
    for f in fs:
        if f.endswith(".manifest"):
            continue
        files.append(os.path.join(root, f))
print("bundle files:", len(files))
allhits = []
for p in files:
    try:
        env = UnityPy.load(p)
    except Exception as e:
        print("FAIL", os.path.basename(p), e); continue
    for k in env.container:
        if KW.search(k):
            allhits.append((os.path.relpath(p, B), k))
    print(f"  {os.path.relpath(p, B)}: {len(env.container)} keys")
print("==== HITS ====")
for f, k in allhits:
    print(f, "|", k)
