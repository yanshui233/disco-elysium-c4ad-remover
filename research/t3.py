import os, re, UnityPy, collections
DATA = r"D:/Steam/steamapps/common/Disco Elysium/disco_Data"
env = UnityPy.load(os.path.join(DATA, "level3"))
KW = re.compile(r"zero|parade|promo|banner|\bad\b|ads|store|buy|news|upsell|cross|zaum|shop|link|marquee|ticker|sponsor", re.I)
print("==== 关键词命中的 GameObject / 其他名称 ====")
mono = collections.Counter()
for o in env.objects:
    n = None
    try:
        d = o.read()
        n = getattr(d, "m_Name", None)
    except Exception:
        pass
    if n and KW.search(n):
        print(o.type.name, "|", n)
    if o.type.name == "MonoBehaviour":
        try:
            s = d.m_Script.read()
            mono[getattr(s, "m_ClassName", "?")] += 1
        except Exception:
            mono["<unresolved>"] += 1
print("==== MonoBehaviour 脚本类名 (top 60) ====")
for k, v in mono.most_common(60):
    print(v, k)
