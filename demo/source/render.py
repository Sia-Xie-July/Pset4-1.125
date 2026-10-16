"""Render the technical demo: frames from content.py, local Kokoro TTS narration, captions, scene list.
Requires: pip install kokoro-onnx soundfile pillow; model files kokoro-v1.0.onnx and voices-v1.0.bin
(github.com/thewh1teagle/kokoro-onnx releases) in $KOKORO_DIR. Assemble with ffmpeg (see demo/README.md)."""
import sys, re, json, subprocess, os, math
from PIL import Image, ImageDraw, ImageFont
import soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
sys.path.insert(0, os.path.dirname(__file__))
from content import SCENES
W,H=1920,1080
OUT=os.path.join(os.path.dirname(__file__),"build"); os.makedirs(OUT,exist_ok=True)
SANS="/usr/share/fonts/opentype/inter/Inter-Regular.otf"; SANSB="/usr/share/fonts/opentype/inter/Inter-Bold.otf"
MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG=(18,20,26); PANEL=(28,31,40); BAR=(40,44,56); FG=(222,226,235); DIM=(140,148,165); ACC=(255,138,61); GRN=(120,210,140); CYN=(110,190,255)
def font(p,s): return ImageFont.truetype(p,s)
def title_card(d,p):
    img=Image.new("RGB",(W,H),BG); g=ImageDraw.Draw(img)
    g.rectangle([0,0,W,8],fill=ACC)
    g.text((160,360),p["title"],font=font(SANSB,110),fill=FG)
    g.text((165,510),p["sub"],font=font(SANS,46),fill=DIM)
    g.text((165,860),p["foot"],font=font(SANS,32),fill=DIM)
    return img
def terminal(p):
    img=Image.new("RGB",(W,H),BG); g=ImageDraw.Draw(img)
    x0,y0,x1,y1=80,60,W-80,H-170
    g.rounded_rectangle([x0,y0,x1,y1],radius=18,fill=PANEL)
    g.rounded_rectangle([x0,y0,x1,y0+64],radius=18,fill=BAR); g.rectangle([x0,y0+40,x1,y0+64],fill=BAR)
    for i,c in enumerate([(255,95,86),(255,189,46),(39,201,63)]): g.ellipse([x0+24+i*30,y0+22,x0+42+i*30,y0+40],fill=c)
    g.text((x0+130,y0+16),p["title"],font=font(SANSB,30),fill=FG)
    lines=p["lines"]; n=len(lines); size=30 if n<=15 else 27 if n<=17 else 25
    f=font(MONO,size); lh=int(size*1.45); y=y0+95
    maxw=x1-x0-80
    for ln in lines:
        col=FG
        if ln.startswith("$"): col=GRN
        elif ln.strip().startswith("#"): col=DIM
        elif ln.strip().startswith(("+",)): col=CYN
        elif ln.strip().startswith("-") and not ln.strip().startswith("--"): col=(240,170,120)
        t=ln
        while g.textlength(t,font=f)>maxw and len(t)>10: t=t[:-2]
        if t!=ln: t=t[:-1]+"…"
        g.text((x0+40,y),t,font=f,fill=col); y+=lh
    return img
def box(g,xy,txt,fill,fs=28,col=FG,bold=False):
    g.rounded_rectangle(xy,radius=14,fill=fill)
    f=font(SANSB if bold else SANS,fs); x0,y0,x1,y1=xy
    lines=txt.split("\n"); th=len(lines)*fs*1.25; y=(y0+y1)/2-th/2
    for l in lines:
        tw=g.textlength(l,font=f); g.text(((x0+x1)/2-tw/2,y),l,font=f,fill=col); y+=fs*1.25
def arrow(g,a,b):
    g.line([a,b],fill=DIM,width=4); ang=math.atan2(b[1]-a[1],b[0]-a[0])
    for s in (2.6,-2.6): g.line([b,(b[0]+18*math.cos(ang+s),b[1]+18*math.sin(ang+s))],fill=DIM,width=4)
def diagram():
    img=Image.new("RGB",(W,H),BG); g=ImageDraw.Draw(img)
    g.text((80,40),"Architecture  ·  run_local.sh → run.sh → two workflows → 13 components",font=font(SANSB,36),fill=FG)
    C1=(44,60,92); C2=(70,52,90); C3=(40,80,60); C4=(92,62,40)
    box(g,(80,130,560,230),"run_local.sh → run.sh\n(coordinate only)",C4,28,bold=True)
    box(g,(80,300,560,380),"workflows/collect_sources.sh",C1,26,bold=True)
    col=[("collectors/fetch_feeds.sh\nfetch_youtube.sh · fetch_podcasts.sh",(80,410,560,500)),
         ("processing/extract_content.sh",(80,530,560,600)),
         ("data/store.sh  (only owner of SQLite index)",(80,630,560,700)),
         ("processing/filter_items.sh  (30-day window)",(80,730,560,800))]
    for t,xy in col: box(g,xy,t,PANEL,22)
    for a,b in [((320,380),(320,410)),((320,500),(320,530)),((320,600),(320,630)),((320,700),(320,730))]: arrow(g,a,b)
    box(g,(700,300,1180,380),"workflows/create_series.sh",C2,26,bold=True)
    col2=[("editorial/select_items.sh  ◆ model",(700,410,1180,480)),
          ("editorial/create_briefs.sh  ◆ model",(700,510,1180,580)),
          ("content/write_articles.sh  ◆ model\ncontent/write_video_scripts.sh  ◆ model",(700,610,1180,700)),
          ("review/check_content.sh  → review.json",(700,730,1180,800))]
    for t,xy in col2: box(g,xy,t,PANEL,22)
    for a,b in [((940,380),(940,410)),((940,480),(940,510)),((940,580),(940,610)),((940,700),(940,730))]: arrow(g,a,b)
    arrow(g,(560,180),(700,330)); arrow(g,(320,230),(320,300)); arrow(g,(560,765),(700,440))
    box(g,(1320,300,1840,400),"STOP: awaiting_review\nhuman review → approval.json",C3,24,bold=True)
    box(g,(1320,450,1840,540),"run.sh --package\n→ publishing/prepare_package.sh",C4,24)
    box(g,(1320,590,1840,680),"Manual: Google Vids · YouTube\nSubstack · publication_links.json",PANEL,22)
    box(g,(1320,730,1840,800),"reporting/summarize_run.sh → summary.json",PANEL,22)
    arrow(g,(1180,765),(1320,350)); arrow(g,(1580,400),(1580,450)); arrow(g,(1580,540),(1580,590))
    g.text((80,840),"JSON Lines between components · every invocation writes a receipt in RUN/logs/ · ◆ = model call (local qwen3:8b)",font=font(SANS,26),fill=DIM)
    return img
# --- TTS
KD=os.environ.get("KOKORO_DIR",".")
k=Kokoro(os.path.join(KD,"kokoro-v1.0.onnx"),os.path.join(KD,"voices-v1.0.bin"))
VOICE=os.environ.get("VOICE","af_heart"); SR=24000
def sentences(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+",t) if s.strip()]
def caption_text(s):  # spoken spellings -> readable captions
    rep=[("A I ","AI "),("R S S","RSS"),("run underscore local dot S H","run_local.sh"),("run dot S H","run.sh"),("store dot S H","store.sh"),
         ("J S O N lines","JSON Lines"),("review I D","review_id"),("claim zero one C one","claim 01-c1"),("segment s zero zero zero zero nine six","segment s-000096"),
         ("X M L","XML"),("UTC","UTC"),("eighty percent","80%")]
    for a,b in rep: s=s.replace(a,b)
    return s
def chunks(s,maxw=13):
    w=s.split(); n=max(1,math.ceil(len(w)/maxw)); per=math.ceil(len(w)/n)
    return [" ".join(w[i:i+per]) for i in range(0,len(w),per)]
audio=[]; cues=[]; t=0.0; segs=[]
GAP=0.35; LEAD=0.6; TAIL=0.9
for i,(kind,p,narr) in enumerate(SCENES):
    img = title_card(None,p) if kind=="title" else diagram() if kind=="diagram" else terminal(p)
    path=f"{OUT}/scene_{i:02d}.png"; img.save(path)
    start=t; audio.append(np.zeros(int(LEAD*SR),dtype=np.float32)); t+=LEAD
    for s in sentences(narr):
        a,sr=k.create(s,voice=VOICE,speed=1.0,lang="en-us"); a=a.astype(np.float32)
        d=len(a)/SR; cap=caption_text(s); parts=chunks(cap); tot=sum(len(x) for x in parts)
        ct=t
        for x in parts:
            dd=d*len(x)/tot; cues.append((ct,ct+dd,x)); ct+=dd
        audio.append(a); audio.append(np.zeros(int(GAP*SR),dtype=np.float32)); t+=d+GAP
    audio.append(np.zeros(int(TAIL*SR),dtype=np.float32)); t+=TAIL
    segs.append((path,t-start)); print(i,kind,round(t-start,1),flush=True)
wav=np.concatenate(audio); sf.write(f"{OUT}/narration.wav",wav,SR)
def ts(x):
    h=int(x//3600); m=int(x%3600//60); s=x%60; return f"{h:02d}:{m:02d}:{int(s):02d},{int((s-int(s))*1000):03d}"
with open(f"{OUT}/captions.srt","w") as f:
    for j,(a,b,x) in enumerate(cues,1): f.write(f"{j}\n{ts(a)} --> {ts(b)}\n{x}\n\n")
with open(f"{OUT}/scenes.txt","w") as f:
    for p,d in segs: f.write(f"file '{p}'\nduration {d:.3f}\n")
    f.write(f"file '{segs[-1][0]}'\n")
print("total",round(t,1))
