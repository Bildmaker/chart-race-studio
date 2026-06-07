# -*- coding: utf-8 -*-
"""ChartRace Studio - Render-Engine.
Animierte Bar-Chart-Race-Videos (9:16). Live (yfinance) + Offline-Fallback (data.py).
Animation: Fuehrender = volle Breite, andere proportional dazu, graue Lane ueber volle Breite.
"""
import os, sys, math, shutil, tempfile, subprocess, datetime, wave
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as pe
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.image as mpimg

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data as D

PRESETS = {
    "Gold":      {"ticker": "GC=F",   "color": "#FFC93C", "offline": "gold"},
    "Bitcoin":   {"ticker": "BTC-USD","color": "#F7931A", "offline": "btc"},
    "Nvidia":    {"ticker": "NVDA",   "color": "#76D900", "offline": "nvda"},
    "Ethereum":  {"ticker": "ETH-USD","color": "#7B86F2", "offline": None},
    "Apple":     {"ticker": "AAPL",   "color": "#5AC8FA", "offline": None},
    "Microsoft": {"ticker": "MSFT",   "color": "#00A4EF", "offline": None},
    "Tesla":     {"ticker": "TSLA",   "color": "#E82127", "offline": None},
    "Amazon":    {"ticker": "AMZN",   "color": "#FF9900", "offline": None},
    "Meta":      {"ticker": "META",   "color": "#3B7BF0", "offline": None},
    "Google":    {"ticker": "GOOGL",  "color": "#EA4335", "offline": None},
    "S&P 500":   {"ticker": "^GSPC",  "color": "#34C759", "offline": None},
    "Silber":    {"ticker": "SI=F",   "color": "#BFC3CC", "offline": None},
}
PALETTE = ["#F7931A","#FFC93C","#76D900","#7B86F2","#5AC8FA","#E82127",
           "#34C759","#EA4335","#00A4EF","#BFC3CC"]
ACCENT = "#23B24A"   # gruener Betrag im Titel
MULT   = "#E2952A"   # Vielfaches (amber)

def _mix(h1,h2,t):
    a=h1.lstrip("#"); b=h2.lstrip("#")
    g=lambda s,i:int(s[i:i+2],16)
    f=lambda i:max(0,min(255,round(g(a,i)+(g(b,i)-g(a,i))*t)))
    return "#%02X%02X%02X"%(f(0),f(2),f(4))

MONTHS_FULL=["Januar","Februar","März","April","Mai","Juni","Juli","August",
             "September","Oktober","November","Dezember"]
W,H,DPI,FPS = 1080,1920,100,30

def midx(year, month): return (year-2012)*12 + (month-1)
def ymd(t): t=max(0,t); return (2012+int(t)//12, int(t)%12)

def fmt_eur(v, cur="€"):
    if v < 1000:   return f"{v:,.0f} {cur}".replace(",",".")
    if v < 1e6:    return f"{v:,.0f} {cur}".replace(",","X").replace(".",",").replace("X",".")
    if v < 1e9:    return f"{v/1e6:,.1f} Mio {cur}".replace(".",",")
    return f"{v/1e9:,.2f} Mrd {cur}".replace(".",",")

def fmt_mult(m):
    if m < 100: return f"{m:.1f}".replace(".",",")+" ×"
    return f"{m:,.0f}".replace(",",".")+" ×"

# ---------------------------------------------------------------- data
def _offline_series(key):
    if key=="gold":
        mi=np.append(np.arange(len(D.GOLD)),173); v=np.array(D.GOLD+[D.GOLD_FINAL])
    elif key=="btc":
        mi=np.append(np.arange(len(D.BTC)),173);  v=np.array(D.BTC+[D.BTC_FINAL])
    elif key=="nvda":
        mi=np.array([a for a,_ in D.NVDA_ANCHORS],float)
        v =np.array([b for _,b in D.NVDA_ANCHORS],float)
    else: raise KeyError(key)
    return mi,v

def load_series(name, ticker, offline_key, start_mi, end_mi, prefer_live=True, log=print):
    live_reason=None
    if prefer_live:
        yf=None
        try:
            import yfinance as yf
        except ModuleNotFoundError:
            live_reason=("yfinance nicht in DIESEM Python verfuegbar: %s . "
                         "Das Programm laeuft offenbar mit einem anderen Python als pip. "
                         "Installiere mit:  \"%s\" -m pip install -r requirements.txt"
                         % (sys.executable, sys.executable))
            log("    ! "+live_reason)
        except Exception as e:
            import traceback as _tb
            live_reason="yfinance-Importfehler: %r" % (e,)
            log("    ! "+live_reason); log(_tb.format_exc())
        if yf is not None:
            sy=2012+start_mi//12; sm=start_mi%12+1; start=f"{sy:04d}-{sm:02d}-01"
            df=None
            try:
                log(f"  - {name}: Live ({ticker}) ab {start} ...")
                d=yf.download(ticker,start=start,interval="1mo",auto_adjust=True,progress=False)
                if d is not None and len(d)>2: df=d
            except Exception as e:
                live_reason=f"download-Fehler: {e}"
            if df is None:
                try:
                    d=yf.Ticker(ticker).history(period="max",interval="1mo",auto_adjust=True)
                    if d is not None and len(d)>2: df=d
                except Exception as e:
                    live_reason=live_reason or f"history-Fehler: {e}"
            if df is not None:
                close=df["Close"]
                if hasattr(close,"columns"): close=close.iloc[:,0]
                close=close.dropna()
                mi=np.array([midx(d.year,d.month) for d in close.index],float)
                v=np.asarray(close.values,dtype=float)
                if len(mi)>2:
                    log(f"    OK {len(mi)} Monatswerte live geladen")
                    return mi, v, "live"
                live_reason=live_reason or "keine verwertbaren Kurse erhalten"
            else:
                live_reason=live_reason or f"keine Daten von Yahoo fuer '{ticker}'"
            log("    ! Live fehlgeschlagen: "+str(live_reason))
    if offline_key:
        mi,v=_offline_series(offline_key); return mi,v,"offline"
    extra=f" (Live-Grund: {live_reason})" if live_reason else ""
    raise RuntimeError(
        f"Fuer '{name}' sind keine Offline-Daten vorhanden{extra}. "
        f"Bitte Internet + yfinance sicherstellen (einmal install.bat ausfuehren) "
        f"oder ein Asset mit Offline-Daten waehlen: Gold, Bitcoin, Nvidia.")

# ---------------------------------------------------------------- music
def make_music(path, dur):
    SR=44100; N=int(SR*dur); out=np.zeros(N); BPM=125.0; beat=60.0/BPM
    def tone(freq,start,length,kind="saw",a=0.005,d=0.12,amp=0.3):
        i0=int(start*SR); i1=min(N,int((start+length)*SR))
        if i0>=N or i1<=i0: return
        n=i1-i0; tt=np.arange(n)/SR; ph=2*np.pi*freq*tt
        if kind=="saw": w=2*(ph/(2*np.pi)%1)-1
        elif kind=="square": w=np.sign(np.sin(ph))
        else: w=np.sin(ph)
        eg=np.ones(n); ai=max(1,min(int(a*SR),n)); eg[:ai]=np.linspace(0,1,ai); eg*=np.exp(-tt/d)
        out[i0:i1]+=amp*w*eg
    def kick(start,amp=0.95):
        i0=int(start*SR); i1=min(N,int((start+0.18)*SR))
        if i0>=N or i1<=i0: return
        n=i1-i0; tt=np.arange(n)/SR; f=110*np.exp(-tt/0.03)+45
        out[i0:i1]+=amp*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt/0.10)
    def hat(start,amp=0.18):
        i0=int(start*SR); i1=min(N,int((start+0.04)*SR))
        if i0>=N or i1<=i0: return
        n=i1-i0; tt=np.arange(n)/SR; out[i0:i1]+=amp*np.random.randn(n)*np.exp(-tt/0.012)
    nf=lambda s:440.0*2**(s/12.0)
    prog=[-12,-16,-9,-2]; chord={-12:[0,3,7],-16:[0,4,7],-9:[0,4,7],-2:[0,4,7]}
    for b in range(int(dur/beat)+1):
        kick(b*beat); hat(b*beat+beat*0.5)
        if b%2==1: hat(b*beat+beat*0.25,0.10)
    chunk=2*beat
    for c in range(int(dur/chunk)+1):
        root=prog[c%4]; rootf=nf(root-12)
        for k in range(4): tone(rootf,c*chunk+k*(chunk/4),chunk/4*0.9,"square",d=0.18,amp=0.22)
        arp=[root+s for s in chord[root]]+[root+12]
        for k in range(8): tone(nf(arp[k%len(arp)]),c*chunk+k*(chunk/8),chunk/8*0.95,"saw",d=0.10,amp=0.13)
        for s in chord[root]: tone(nf(root+s),c*chunk,chunk*0.98,"sine",a=0.05,d=1.2,amp=0.06)
    rs=max(0,dur-2.2); i0=int(rs*SR); tt=np.arange(N-i0)/SR
    if len(tt)>0:
        fr=200*2**(tt/1.1); out[i0:]+=0.18*np.sin(2*np.pi*np.cumsum(fr)/SR)*(tt/2.2)
    out=out/max(1e-9,np.max(np.abs(out)))*0.92; out=np.tanh(out*1.2)/np.tanh(1.2)
    fo=int(0.15*SR); out[-fo:]*=np.linspace(1,0,fo)
    pcm=(out*32767).astype(np.int16); st=np.repeat(pcm.reshape(-1,1),2,1).reshape(-1)
    w=wave.open(path,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(st.tobytes()); w.close()

# ---------------------------------------------------------------- themes
THEMES={
 "light":{"bg":["#f4f5f8","#eceef3","#f4f5f8"],"fig":"#f4f5f8","text":"#111118",
          "sub":"#9aa0ad","track":"#d9dae6","islight":True},
 "dark": {"bg":["#0a0a16","#13131f","#0a0a16"],"fig":"#0a0a16","text":"#ffffff",
          "sub":"#8a8aa2","track":"#22222e","islight":False},
}

def _bg(ax, th):
    grad=np.linspace(0,1,256).reshape(-1,1)
    ax.imshow(grad,extent=[0,W,0,H],aspect="auto",
              cmap=LinearSegmentedColormap.from_list("bg",th["bg"]),origin="lower",zorder=0)

_MEASURE={}
def _text_w(text, fs, weight="bold"):
    key=(text,fs,weight)
    if key in _MEASURE: return _MEASURE[key]
    fig=Figure(figsize=(2,1),dpi=DPI); FigureCanvasAgg(fig); r=fig.canvas.get_renderer()
    t=fig.text(0,0,text,fontsize=fs,fontweight=weight)
    w=t.get_window_extent(renderer=r).width
    _MEASURE[key]=w; return w

def _title(ax, y, invest, cur, th, alpha=1.0, effects=None):
    amt=f"{int(round(invest)):,}".replace(",",".")+cur
    parts=[("AUS ", th["text"]),(amt, ACCENT),(" WERDEN", th["text"])]
    fs=46
    widths=[_text_w(t,fs) for t,_ in parts]
    x=W/2-sum(widths)/2
    for (t,c),w in zip(parts,widths):
        ax.text(x,y,t,ha="left",va="center",color=c,fontsize=fs,fontweight="bold",alpha=alpha,path_effects=effects)
        x+=w

def _bar_fraction(v, scale_max):
    # Bezug = scale_max = max(StartMax, aktueller Spitzenwert).
    if scale_max<=0: return 0.0
    return max(0.0, min(1.0, v/scale_max))

def _layout(n):
    if n<=3: return 196, 70
    if n==4: return 150, 56
    if n==5: return 122, 46
    return 100, 40

# ---------------------------------------------------------------- frame
def _frame(path, assets, vals, ydisp, t, th, invest, cur, start_year, start_month,
           scale_max, winner=None, blink=None, bgimg=None):
    n=len(assets); barh,_=_layout(n)
    X0=70; TW=W-2*X0; rad=min(46, barh*0.30)
    islight=th["islight"]

    fig=Figure(figsize=(W/DPI,H/DPI),dpi=DPI); FigureCanvasAgg(fig)
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
    use_bg = bgimg is not None
    if use_bg:
        ax.imshow(bgimg, extent=[0,W,0,H], aspect="auto", zorder=0)
    else:
        _bg(ax,th)
    bar_a  = 0.80 if use_bg else 1.0
    lane_a = 0.42 if use_bg else 1.0
    txt_a  = 0.90 if use_bg else 1.0
    txt_eff=[pe.withStroke(linewidth=3,foreground=("#ffffff" if islight else "#000000"),alpha=0.45)] if use_bg else None

    # ---- title + date (top) ----
    _title(ax, H-110, invest, cur, th, txt_a, txt_eff)
    yr,mo=ymd(t)
    ax.text(W/2,H-250,MONTHS_FULL[mo].upper(),ha="center",va="center",
            color=th["text"],fontsize=46,fontweight="bold",alpha=txt_a,path_effects=txt_eff)
    ax.text(W/2,H-385,f"{yr}",ha="center",va="center",color=th["text"],fontsize=150,fontweight="bold",alpha=txt_a,path_effects=txt_eff)

    # ---- bars ----
    regionTop=H-575; regionBottom=210; pitch=(regionTop-regionBottom)/n
    for a in assets:
        nm=a["name"]; c=a["color"]; v=vals[nm]
        cy=regionTop-(ydisp[nm]+0.5)*pitch; y=cy-barh/2
        frac=_bar_fraction(v,scale_max); bw=max(frac*TW, 4.0); rb=min(rad, bw*0.5)
        is_win=(winner is not None and nm==winner and blink is not None)
        gp=(blink if is_win else 0.0)
        # graue Lane (volle Breite)
        ax.add_patch(FancyBboxPatch((X0,y),TW,barh,boxstyle=f"round,pad=0,rounding_size={rad}",
            lw=0,facecolor=th["track"],alpha=lane_a,zorder=1))
        # Glow
        for dx,al in [(22,0.05),(13,0.08),(6,0.12)]:
            ax.add_patch(FancyBboxPatch((X0-dx,y-dx),bw+2*dx,barh+2*dx,
                boxstyle=f"round,pad=0,rounding_size={rb+4}",lw=0,
                facecolor=_mix(c,'#ffffff',0.3),alpha=min(1.0,al+gp*0.85),zorder=2))
        # farbiger Balken (Gradient)
        clip=FancyBboxPatch((X0,y),bw,barh,boxstyle=f"round,pad=0,rounding_size={rb}",
            lw=0,facecolor='none',zorder=3); ax.add_patch(clip)
        grad=np.linspace(0,1,256).reshape(1,-1)
        im=ax.imshow(grad,extent=[X0,X0+bw,y,y+barh],aspect="auto",origin="lower",zorder=3,
            cmap=LinearSegmentedColormap.from_list("b",[_mix(c,'#ffffff',0.45),c]))
        im.set_clip_path(clip); im.set_alpha(bar_a)
        sh=FancyBboxPatch((X0,y+barh*0.52),bw,barh*0.48,boxstyle=f"round,pad=0,rounding_size={rb}",
            lw=0,facecolor='#ffffff',alpha=0.12,zorder=4); ax.add_patch(sh); sh.set_clip_path(clip)
        if is_win:
            ax.add_patch(FancyBboxPatch((X0,y),bw,barh,boxstyle=f"round,pad=0,rounding_size={rb}",
                lw=6,edgecolor=c,facecolor='none',alpha=blink,zorder=6))
        # Name ueber dem Balken
        fs_name=40 if n<=3 else (32 if n<=4 else 26)
        ax.text(X0+8,y+barh+34,nm,ha="left",va="center",color=th["text"],
                fontsize=fs_name,fontweight="bold",zorder=7,alpha=txt_a,path_effects=txt_eff)
        # Wert + Vielfaches (rechts in der Lane)
        fs_v=58 if n<=3 else (46 if n<=4 else 38)
        vtxt=fmt_eur(v,cur); mtxt=fmt_mult(v/invest); vx=X0+TW-34
        vcol = "#111118" if islight else "#ffffff"
        vstroke = "#ffffff" if islight else "#0a0a16"
        veff=[pe.withStroke(linewidth=4,foreground=vstroke,alpha=0.6)]
        ax.text(vx,cy+barh*0.13,vtxt,ha="right",va="center",color=vcol,fontsize=fs_v,
                fontweight="bold",zorder=7,alpha=txt_a,path_effects=veff)
        ax.text(vx,cy-barh*0.26,mtxt,ha="right",va="center",color=MULT,fontsize=fs_v*0.52,
                fontweight="bold",zorder=7,alpha=txt_a,path_effects=veff)

    # ---- footer ----
    ax.text(W/2,82,f"seit {MONTHS_FULL[start_month-1]} {start_year}",ha="center",va="center",
            color=th["sub"],fontsize=30,fontweight="bold",alpha=txt_a,path_effects=txt_eff)

    fig.savefig(path,facecolor=th["fig"])

# ---------------------------------------------------------------- main
def render_video(cfg, progress=None, log=print):
    def report(p,msg):
        if progress: progress(p,msg)
        log(msg)
    assets_in=cfg["assets"]; invest=float(cfg["invest"])
    sy=int(cfg["start_year"]); sm=int(cfg.get("start_month",1))
    dur=float(cfg["duration"]); hold=float(cfg.get("hold",2.0))
    blink=bool(cfg.get("blink",True)); look=cfg.get("look","dark")
    music=bool(cfg.get("music",True)); cur=cfg.get("currency","€")
    prefer_live=bool(cfg.get("prefer_live",True)); sort_v=bool(cfg.get("sort",True))
    th=THEMES.get(look,THEMES["dark"])
    # Hintergrundbild (Default: images/background.png; leerer Pfad = keins)
    if "background" in cfg:
        bg_path = cfg["background"] or None
    else:
        bg_path = os.path.join(HERE,"images","background.png")
    bgimg=None
    if bg_path and os.path.isfile(bg_path):
        try: bgimg=mpimg.imread(bg_path)
        except Exception as e: log("Hintergrundbild konnte nicht geladen werden: %r"%e)
    today=datetime.date.today()
    start_mi=midx(sy,sm); end_mi=midx(today.year,today.month)
    if end_mi<=start_mi: end_mi=start_mi+12

    report(2,"Lade Kursdaten …")
    assets=[]
    for i,nm in enumerate(assets_in):
        pre=PRESETS.get(nm,{"ticker":nm,"color":PALETTE[i%len(PALETTE)],"offline":None})
        mi,v,src=load_series(nm,pre["ticker"],pre.get("offline"),start_mi,end_mi,prefer_live,log)
        assets.append({"name":nm,"color":pre["color"],"mi":mi,"v":v,"src":src})
    def price(a,t): return float(np.interp(t,a["mi"],a["v"]))
    for a in assets:
        a["p0"]=price(a,start_mi)
        if a["p0"]<=0: a["p0"]=price(a,a["mi"][0])
    def values_at(t): return {a["name"]: invest*price(a,t)/a["p0"] for a in assets}

    endvals=values_at(end_mi); winner=max(endvals,key=lambda k:endvals[k])
    start_max=float(cfg.get("start_max",50000))
    report(8,f"Sieger: {winner} ({fmt_eur(endvals[winner],cur)}) · StartMax: {fmt_eur(start_max,cur)}")

    total=int(round(dur*FPS)); holdf=int(round(hold*FPS)); racef=max(2,total-holdf)
    tmp=tempfile.mkdtemp(prefix="crs_")
    NAMES=[a["name"] for a in assets]; yd={}
    fixed={n:i for i,n in enumerate(NAMES)}
    def step(t):
        vals=values_at(t)
        if sort_v:
            order=sorted(NAMES,key=lambda k:vals[k],reverse=True)
            tg={n:order.index(n) for n in NAMES}
        else:
            tg=fixed
        if not yd:
            for n in NAMES: yd[n]=float(tg[n])
        else:
            for n in NAMES: yd[n]+=(tg[n]-yd[n])*0.22
        return vals
    try:
        for i in range(total):
            if i<racef:
                t=start_mi+(i/(racef-1))*(end_mi-start_mi); bl=None
            else:
                t=end_mi; bl=0.5+0.5*math.sin(((i-racef)/FPS)*2*math.pi*2.5)
            vals=step(t)
            smax=max(start_max, max(vals.values()))
            _frame(os.path.join(tmp,f"f{i:05d}.png"),assets,vals,yd,t,th,invest,cur,
                   sy,sm,smax,winner=winner,blink=(bl if blink else None),bgimg=bgimg)
            if i%10==0: report(10+int(78*i/total),f"Rendere Frame {i+1}/{total} …")
        audio=None
        if music:
            report(90,"Erzeuge Musik …"); audio=os.path.join(tmp,"music.wav"); make_music(audio,dur)
        report(92,"Setze Video zusammen (ffmpeg) …")
        ff=_ffmpeg_exe(); out=cfg["out_path"]
        cmd=[ff,"-y","-framerate",str(FPS),"-i",os.path.join(tmp,"f%05d.png")]
        if audio: cmd+=["-i",audio]
        cmd+=["-c:v","libx264","-pix_fmt","yuv420p","-crf","19","-preset","medium"]
        if audio: cmd+=["-c:a","aac","-b:a","192k","-shortest"]
        cmd+=["-movflags","+faststart",out]
        subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        report(100,f"Fertig: {out}")
        return out
    finally:
        shutil.rmtree(tmp,ignore_errors=True)

def _ffmpeg_exe():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe=shutil.which("ffmpeg")
        if exe: return exe
        raise RuntimeError("ffmpeg nicht gefunden. Bitte 'pip install imageio-ffmpeg' ausfuehren.")
