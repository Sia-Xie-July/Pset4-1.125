"""Build Substack-ready HTML from the approved package articles (reader-friendly source list)."""
import re, json, markdown, sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
yt={"01":"https://youtu.be/2mOpLgQUm2Y","02":"https://youtu.be/nKaQr6ya9cY","03":"https://youtu.be/cexb5hJ__Ss"}
names={"01":"Episode 1","02":"Episode 2","03":"Episode 3"}
def fmt(sec):
    s=int(float(sec)); return f"{s//60}:{s%60:02d}"
out={}
for n in ("01","02","03"):
    md=(R/"package/articles"/f"{n}.md").read_text()
    title=md.splitlines()[0].lstrip("# ").strip()
    body=md.split("\n",1)[1]
    main,src=body.split("\n## Sources",1)
    # condense sources: per claim, group by base URL
    claims=re.split(r"\n- \*\*", "\n"+src.strip())
    items=[]
    for c in claims:
        c=c.strip()
        if not c: continue
        head,*subs=c.split("\n")
        cid,stmt=head.split("**:",1)
        groups={}
        for s in subs:
            m=re.match(r"\s*- \[(.+?)\]\((.+?)\) — (.*?)(?:: .*)?\(version `([0-9a-f]+)`\)\.",s.strip())
            if not m:
                m2=re.match(r"\s*- \[(.+?)\]\((.+?)\)(.*)",s.strip())
                if m2: groups.setdefault(m2.group(2),{"t":m2.group(1),"url":m2.group(2),"r":[],"v":None})
                continue
            t,url,loc,ver=m.groups()
            base=re.sub(r"[&?]t=\d+$","",url)
            g=groups.setdefault(base,{"t":t,"url":url,"r":[],"v":ver})
            rr=re.match(r"([\d.]+)–([\d.]+) seconds",loc)
            if rr: g["r"]+= [float(rr.group(1)),float(rr.group(2))]
            else: g["loc"]=loc.strip()
        lines=[]
        for base,g in groups.items():
            if g["r"]:
                a,b=min(g["r"]),max(g["r"]); link=(f"{base}&t={int(a)}" if "youtube.com" in base else base)
                lines.append(f"[{g['t']}]({link}), {fmt(a)}–{fmt(b)} (version `{g['v'][:12]}`)")
            else:
                q=g.get('loc') or ''
                q=re.sub(r'(\w),\d+ ', r'\1, ', q)
                if len(q)>180: q=q[:170].rsplit(' ',1)[0]+' …"'
                extra=f" — {q}" if q else ""
                lines.append(f"[{g['t']}]({g['url']}){extra}" + (f" (version `{g['v'][:12]}`)" if g['v'] else ""))
        items.append(f"- **{cid.strip()}** {stmt.strip()}  \n  " + "; ".join(lines))
    others=" · ".join(f"[{names[k]} video]({v})" for k,v in yt.items())
    top=(f"**Watch the video for this piece:** [{names[n]} on YouTube]({yt[n]}) (3–5 min, AI-generated presenter and voice)\n\n"
         f"*Before the Merge* is a three-part series for technical leads of 3–10-person software teams deciding how much work to delegate to coding agents.\n\n---\n")
    tail=(f"\n## Sources\n\nEach bracketed tag in the text (for example [{n}-c1]) refers to a claim below. Timestamps link to the exact passage; the version is the hash of the retained source text or transcript.\n\n"
          + "\n".join(items) + f"\n\n---\n\nSeries videos: {others}\n")
    html=markdown.markdown(top+main+tail)
    (R/"production/substack"/f"{n}.html").write_text(html)
    out[n]={"title":title,"html_len":len(html)}
print(json.dumps(out,indent=1))
