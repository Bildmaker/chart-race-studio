# -*- coding: utf-8 -*-
"""ChartRace Studio - GUI.
Doppelklick auf start.bat (Windows) oder:  python chartrace_studio.py
"""
import os, sys, threading, queue, datetime, traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E

BG="#0f0f1a"; CARD="#181826"; FG="#eaeaf2"; SUB="#9a9ab2"; ACCENT="#7a7aff"

def default_outdir():
    for c in [os.path.join(os.path.expanduser("~"),"Videos"),
              os.path.join(os.path.expanduser("~"),"Desktop"),
              os.path.expanduser("~")]:
        if os.path.isdir(c): return c
    return HERE

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChartRace Studio")
        self.configure(bg=BG)
        self.geometry("660x980")
        self.minsize(600,900)
        self.q=queue.Queue()
        self._build()
        self.after(120,self._poll)

    def _lbl(self,parent,txt,**kw):
        return tk.Label(parent,text=txt,bg=kw.get("bg",BG),fg=kw.get("fg",FG),
                        font=kw.get("font",("Segoe UI",11)),anchor="w")

    def _build(self):
        head=tk.Frame(self,bg=BG); head.pack(fill="x",padx=22,pady=(18,6))
        tk.Label(head,text="ChartRace Studio",bg=BG,fg=FG,
                 font=("Segoe UI Semibold",20)).pack(anchor="w")
        tk.Label(head,text="Animierte Bar-Chart-Race-Videos (9:16) für Reels · TikTok · Shorts",
                 bg=BG,fg=SUB,font=("Segoe UI",10)).pack(anchor="w")

        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True,padx=22,pady=8)

        # --- Assets ---
        ca=tk.LabelFrame(body,text=" Assets ",bg=CARD,fg=SUB,font=("Segoe UI",10),bd=0)
        ca.pack(fill="x",pady=6,ipady=6)
        self.asset_vars={}
        grid=tk.Frame(ca,bg=CARD); grid.pack(fill="x",padx=10,pady=4)
        names=list(E.PRESETS.keys())
        defaults={"Gold","Bitcoin","Nvidia"}
        for i,n in enumerate(names):
            v=tk.BooleanVar(value=(n in defaults)); self.asset_vars[n]=v
            cb=tk.Checkbutton(grid,text=n,variable=v,bg=CARD,fg=FG,selectcolor="#26263a",
                activebackground=CARD,activeforeground=FG,font=("Segoe UI",10),anchor="w")
            cb.grid(row=i//3,column=i%3,sticky="w",padx=6,pady=2)
        cf=tk.Frame(ca,bg=CARD); cf.pack(fill="x",padx=10,pady=(2,4))
        self._lbl(cf,"Eigene Ticker (Komma-getrennt, z. B. AMD, ^NDX):",bg=CARD,fg=SUB,
                  font=("Segoe UI",9)).pack(anchor="w")
        self.custom=tk.Entry(cf,bg="#101020",fg=FG,insertbackground=FG,relief="flat")
        self.custom.pack(fill="x",ipady=4)

        # --- Parameter grid ---
        cp=tk.LabelFrame(body,text=" Einstellungen ",bg=CARD,fg=SUB,font=("Segoe UI",10),bd=0)
        cp.pack(fill="x",pady=6,ipady=6)
        g=tk.Frame(cp,bg=CARD); g.pack(fill="x",padx=10,pady=4)
        thisyear=datetime.date.today().year
        def row(r,label,widget):
            self._lbl(g,label,bg=CARD).grid(row=r,column=0,sticky="w",pady=5)
            widget.grid(row=r,column=1,sticky="we",pady=5,padx=(10,0))
        g.columnconfigure(1,weight=1)
        self.invest=tk.StringVar(value="10000")
        self.startmax=tk.StringVar(value="50000")
        self.syear=tk.IntVar(value=2020)
        self.smonth=tk.IntVar(value=1)
        self.dur=tk.StringVar(value="15")
        self.hold=tk.StringVar(value="2")
        row(0,"Investbetrag (€)",tk.Entry(g,textvariable=self.invest,bg="#101020",fg=FG,insertbackground=FG,relief="flat"))
        row(1,"StartMax / graue Lane (€)",tk.Entry(g,textvariable=self.startmax,bg="#101020",fg=FG,insertbackground=FG,relief="flat"))
        row(2,"Startjahr",tk.Spinbox(g,from_=2012,to=thisyear,textvariable=self.syear,bg="#101020",fg=FG,relief="flat",buttonbackground=CARD))
        row(3,"Startmonat",tk.Spinbox(g,from_=1,to=12,textvariable=self.smonth,bg="#101020",fg=FG,relief="flat",buttonbackground=CARD))
        row(4,"Länge (Sek.)",tk.Spinbox(g,from_=5,to=60,textvariable=self.dur,bg="#101020",fg=FG,relief="flat",buttonbackground=CARD))
        row(5,"Endstand stehen lassen (Sek.)",tk.Spinbox(g,from_=0,to=6,textvariable=self.hold,bg="#101020",fg=FG,relief="flat",buttonbackground=CARD))

        # --- options ---
        co=tk.Frame(body,bg=BG); co.pack(fill="x",pady=2)
        self.look=tk.StringVar(value="dark")
        self.blink=tk.BooleanVar(value=True)
        self.music=tk.BooleanVar(value=True)
        self.live=tk.BooleanVar(value=True)
        self.sort=tk.BooleanVar(value=True)
        lf=tk.Frame(co,bg=BG); lf.pack(fill="x",pady=4)
        self._lbl(lf,"Look:").pack(side="left")
        for txt,val in [("Dark Neon","dark"),("Clean Light","light")]:
            tk.Radiobutton(lf,text=txt,variable=self.look,value=val,bg=BG,fg=FG,selectcolor="#26263a",
                activebackground=BG,activeforeground=FG,font=("Segoe UI",10)).pack(side="left",padx=8)
        of=tk.Frame(co,bg=BG); of.pack(fill="x")
        for txt,var in [("Sieger blinken",self.blink),("Musik",self.music),("Live-Daten",self.live),("Nach Wert sortieren",self.sort)]:
            tk.Checkbutton(of,text=txt,variable=var,bg=BG,fg=FG,selectcolor="#26263a",
                activebackground=BG,activeforeground=FG,font=("Segoe UI",10)).pack(side="left",padx=(0,14))

        # --- output ---
        co2=tk.Frame(body,bg=BG); co2.pack(fill="x",pady=6)
        self._lbl(co2,"Ausgabeordner:").pack(anchor="w")
        of2=tk.Frame(co2,bg=BG); of2.pack(fill="x")
        self.outdir=tk.StringVar(value=default_outdir())
        tk.Entry(of2,textvariable=self.outdir,bg="#101020",fg=FG,insertbackground=FG,relief="flat").pack(side="left",fill="x",expand=True,ipady=4)
        tk.Button(of2,text="Durchsuchen",command=self._browse,bg=CARD,fg=FG,relief="flat",
                  activebackground="#26263a",activeforeground=FG).pack(side="left",padx=(8,0))

        cbg=tk.Frame(body,bg=BG); cbg.pack(fill="x",pady=6)
        self._lbl(cbg,"Hintergrundbild (leer = keins):").pack(anchor="w")
        ofb=tk.Frame(cbg,bg=BG); ofb.pack(fill="x")
        self.bg=tk.StringVar(value=os.path.join(HERE,"images","background.png"))
        tk.Entry(ofb,textvariable=self.bg,bg="#101020",fg=FG,insertbackground=FG,relief="flat").pack(side="left",fill="x",expand=True,ipady=4)
        tk.Button(ofb,text="Durchsuchen",command=self._browse_bg,bg=CARD,fg=FG,relief="flat",
                  activebackground="#26263a",activeforeground=FG).pack(side="left",padx=(8,0))
        tk.Button(ofb,text="Kein Bild",command=lambda:self.bg.set(""),bg=CARD,fg=FG,relief="flat",
                  activebackground="#26263a",activeforeground=FG).pack(side="left",padx=(6,0))

        # --- action ---
        # ---- Log-Fenster (Prozess live beobachten) ----
        clog=tk.Frame(body,bg=BG); clog.pack(fill="both",expand=True,pady=(8,2))
        self._lbl(clog,"Render-Log:").pack(anchor="w")
        lwrap=tk.Frame(clog,bg=BG); lwrap.pack(fill="both",expand=True)
        sb=tk.Scrollbar(lwrap); sb.pack(side="right",fill="y")
        self.logbox=tk.Text(lwrap,height=9,bg="#0c0c16",fg="#cfd2e6",insertbackground=FG,
            relief="flat",font=("Consolas",9),yscrollcommand=sb.set,wrap="word")
        self.logbox.pack(side="left",fill="both",expand=True)
        sb.config(command=self.logbox.yview)

        self.btn=tk.Button(body,text="▶  Video rendern",command=self._start,bg=ACCENT,fg="#0b0b16",
            relief="flat",font=("Segoe UI Semibold",13),activebackground="#9a9aff",cursor="hand2")
        self.btn.pack(fill="x",pady=(10,6),ipady=10)
        self.pb=ttk.Progressbar(body,maximum=100); self.pb.pack(fill="x",pady=(2,2))
        self.status=tk.Label(body,text="Bereit.",bg=BG,fg=SUB,font=("Segoe UI",9),anchor="w")
        self.status.pack(fill="x")

    def _browse(self):
        d=filedialog.askdirectory(initialdir=self.outdir.get() or HERE)
        if d: self.outdir.set(d)

    def _browse_bg(self):
        init=os.path.dirname(self.bg.get()) if self.bg.get() else os.path.join(HERE,"images")
        p=filedialog.askopenfilename(initialdir=init or HERE,
            filetypes=[("Bilder","*.png *.jpg *.jpeg *.bmp *.webp"),("Alle Dateien","*.*")])
        if p: self.bg.set(p)

    def _collect_assets(self):
        a=[n for n,v in self.asset_vars.items() if v.get()]
        for c in self.custom.get().split(","):
            c=c.strip()
            if c: a.append(c)
        return a

    def _start(self):
        assets=self._collect_assets()
        if len(assets)<2:
            messagebox.showwarning("Hinweis","Bitte mindestens 2 Assets auswählen."); return
        if len(assets)>6:
            messagebox.showwarning("Hinweis","Bitte höchstens 6 Assets (Lesbarkeit)."); return
        try:
            invest=float(self.invest.get().replace(".","").replace(",","."))
            startmax=float(self.startmax.get().replace(".","").replace(",","."))
            dur=float(self.dur.get().replace(",",".")); hold=float(self.hold.get().replace(",","."))
        except ValueError:
            messagebox.showerror("Fehler","Bitte gültige Zahlen eingeben."); return
        os.makedirs(self.outdir.get(),exist_ok=True)
        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tag="_".join(a.replace(" ","").replace("^","")[:6] for a in assets[:3])
        out=os.path.join(self.outdir.get(),f"chartrace_{tag}_{self.syear.get()}_{stamp}.mp4")
        cfg=dict(assets=assets,invest=invest,start_year=self.syear.get(),
                 start_month=self.smonth.get(),duration=dur,hold=hold,
                 blink=self.blink.get(),look=self.look.get(),music=self.music.get(),
                 out_path=out,currency="€",prefer_live=self.live.get(),sort=self.sort.get(),start_max=startmax,background=self.bg.get())
        self.logbox.delete("1.0","end")
        logpath=os.path.join(self.outdir.get(),"render_log.txt")
        self._log("Starte Render: "+", ".join(assets))
        self._log("Ausgabe: "+out)
        self._log("Log-Datei: "+logpath)
        self.btn.config(state="disabled",text="Rendere …")
        self.pb["value"]=0
        threading.Thread(target=self._worker,args=(cfg,logpath),daemon=True).start()

    def _worker(self,cfg,logpath):
        lf=None
        try: lf=open(logpath,"w",encoding="utf-8")
        except Exception: lf=None
        def log(m):
            line=str(m); self.q.put(("log",line))
            if lf:
                try: lf.write(line+"\n"); lf.flush()
                except Exception: pass
        def prog(p,m): self.q.put(("prog",p,m))
        try:
            out=E.render_video(cfg,progress=prog,log=log)
            self.q.put(("done",out))
        except Exception as e:
            log("FEHLER:\n"+traceback.format_exc())
            self.q.put(("err",str(e)))
        finally:
            if lf:
                try: lf.close()
                except Exception: pass

    def _poll(self):
        try:
            while True:
                item=self.q.get_nowait()
                if item[0]=="log":
                    self._log(item[1])
                elif item[0]=="prog":
                    self.pb["value"]=item[1]; self.status.config(text=item[2])
                elif item[0]=="done":
                    self.pb["value"]=100; self.status.config(text="Fertig: "+item[1])
                    self.btn.config(state="normal",text="▶  Video rendern")
                    if messagebox.askyesno("Fertig","Video erstellt:\n%s\n\nOrdner öffnen?"%item[1]):
                        self._open(os.path.dirname(item[1]))
                elif item[0]=="err":
                    self.btn.config(state="normal",text="▶  Video rendern")
                    self.status.config(text="Fehler.")
                    messagebox.showerror("Fehler beim Rendern",item[1])
        except queue.Empty:
            pass
        self.after(120,self._poll)

    def _log(self,msg):
        try:
            self.logbox.insert("end",str(msg)+"\n"); self.logbox.see("end")
        except Exception: pass

    def _open(self,path):
        try:
            if sys.platform.startswith("win"): os.startfile(path)
            elif sys.platform=="darwin": os.system(f'open "{path}"')
            else: os.system(f'xdg-open "{path}"')
        except Exception: pass

if __name__=="__main__":
    App().mainloop()
