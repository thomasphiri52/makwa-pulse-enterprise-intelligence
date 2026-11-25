import streamlit as st
import pandas as pd
import numpy as np
import sqlite3, hashlib, hmac, json, os, requests
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
DB = DATA / "makwa_pulse_v2.db"
st.set_page_config(page_title="MAKWA PULSE V2", page_icon="◈", layout="wide")

st.markdown("""
<style>
.stApp{background:#091321;color:#edf4ff}
section[data-testid="stSidebar"]{background:#101d30}
.block-container{padding-top:1.25rem}
div[data-testid="stMetric"]{background:#14243a;border:1px solid #2a405c;padding:14px;border-radius:12px}
.small{color:#9cb1ca;font-size:.88rem}
div[data-testid="stDataFrame"]{border:1px solid #2a405c;border-radius:10px}
</style>
""", unsafe_allow_html=True)

# --- Security / identity ---
USERS = {
    "executive": {"password": "PulseDemo!2026", "role": "Executive"},
    "engineer": {"password": "PulseDemo!2026", "role": "Engineer"},
    "analyst": {"password": "PulseDemo!2026", "role": "Analyst"},
}
ROLE_PAGES = {
    "Executive": ["Executive Overview", "SLA Intelligence", "Cloud Cost Intelligence", "Customer Experience", "Reports & Data"],
    "Engineer": ["Executive Overview", "IT Operations", "Predictive Risk", "Integration Hub", "Reports & Data"],
    "Analyst": ["Executive Overview", "AI Intelligence Analyst", "Predictive Risk", "SLA Intelligence", "Cloud Cost Intelligence", "Customer Experience", "Reports & Data"]
}
def login():
    st.title("◈ MAKWA PULSE V2")
    st.caption("Enterprise Intelligence Command Centre · Secure demo sign-in")
    st.info("Demo credentials are provided for evaluation only. Replace this local demo authentication with MakwaIT SSO/identity provider before any production use.")
    with st.form("login"):
        username = st.text_input("Username", value="executive")
        password = st.text_input("Password", type="password", value="PulseDemo!2026")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        user = USERS.get(username.lower())
        if user and hmac.compare_digest(password, user["password"]):
            st.session_state["user"] = username.lower()
            st.session_state["role"] = user["role"]
            st.rerun()
        else:
            st.error("Invalid demo credentials.")
    st.markdown("**Demo accounts:** `executive`, `engineer`, `analyst` · Password: `PulseDemo!2026`")
    st.caption("This is demo-only local authentication, not production-grade identity management.")

if "user" not in st.session_state:
    login()
    st.stop()

role = st.session_state["role"]
st.sidebar.markdown("# ◈ MAKWA PULSE")
st.sidebar.caption("V2 · ENTERPRISE INTELLIGENCE")
st.sidebar.success(f"Signed in · {role}")
if st.sidebar.button("Sign out"):
    st.session_state.clear()
    st.rerun()

# --- Data layer ---
def conn():
    return sqlite3.connect(DB)
def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS telemetry(
        id INTEGER PRIMARY KEY, timestamp TEXT, client TEXT, service TEXT, region TEXT,
        cpu REAL, memory REAL, latency_ms REAL, availability REAL, incidents INTEGER,
        severity TEXT, monthly_cost REAL, sla_target REAL, satisfaction REAL, source TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, actor TEXT, action TEXT, detail TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS connector_config(
        name TEXT PRIMARY KEY, endpoint TEXT, enabled INTEGER, notes TEXT)""")
        existing = c.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
        if existing == 0:
            rng=np.random.default_rng(2026)
            clients=["Atlas Financial (DEMO)","Ubuntu Manufacturing (DEMO)","Karoo Health (DEMO)","Coastal Retail (DEMO)","Metsi Logistics (DEMO)"]
            services=["Cloud Platform","Network Services","Identity & Access","Business Applications","Security Operations"]
            regions=["Johannesburg","Cape Town","Durban","Pretoria"]
            rows=[]
            now=datetime.now()
            for i in range(720):
                ts=now-timedelta(hours=720-i)
                cpu=float(np.clip(rng.normal(58,17),5,99))
                mem=float(np.clip(rng.normal(66,13),10,99))
                lat=float(np.clip(rng.normal(118,38),15,500))
                avail=float(np.clip(rng.normal(99.72,.22),97.5,100))
                inc=int(rng.poisson(.2))
                if i in [91,92,237,238,351,509,510,651]:
                    cpu,lat,avail,inc=94,310,98.4,3
                sev="Critical" if inc>=3 or avail<98.8 else ("High" if cpu>85 or lat>230 else "Normal")
                rows.append((ts.isoformat(timespec="minutes"),rng.choice(clients),rng.choice(services),rng.choice(regions),cpu,mem,lat,avail,inc,sev,float(rng.uniform(18000,95000)),99.5,float(np.clip(rng.normal(4.25,.45),2.8,5)),"Synthetic demo generator"))
            c.executemany("""INSERT INTO telemetry(timestamp,client,service,region,cpu,memory,latency_ms,availability,incidents,severity,monthly_cost,sla_target,satisfaction,source)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",rows)
        defaults=[
            ("REST API Connector","",0,"Template only; configure an approved endpoint and authentication outside source code."),
            ("CSV Import","",1,"Enabled; upload approved CSV data using the Integration Hub."),
            ("Power BI Export","",1,"CSV hand-off for prototype; production semantic model requires tenant setup.")
        ]
        c.executemany("INSERT OR IGNORE INTO connector_config VALUES(?,?,?,?)",defaults)
init_db()

def audit(action, detail):
    with conn() as c:
        c.execute("INSERT INTO audit_log(timestamp,actor,action,detail) VALUES(?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"),st.session_state.get("user","unknown"),action,detail))

def load_data():
    return pd.read_sql_query("SELECT * FROM telemetry ORDER BY timestamp", conn(), parse_dates=["timestamp"])
df=load_data()

pages=ROLE_PAGES[role]
page=st.sidebar.radio("WORKSPACE",pages)
st.sidebar.markdown("---")
st.sidebar.caption("Environment: DEMO / SYNTHETIC DATA")
st.sidebar.caption("No MakwaIT production systems connected.")
st.title("◈ MAKWA PULSE V2")
st.markdown("<div class='small'>Enterprise service intelligence · Governed demo workspace</div>",unsafe_allow_html=True)

# filters
c1,c2,c3=st.columns([2,2,2])
with c1: client=st.selectbox("Client",["All clients"]+sorted(df.client.unique().tolist()))
with c2: region=st.selectbox("Region",["All regions"]+sorted(df.region.unique().tolist()))
with c3: window=st.selectbox("Window",["7 days","30 days","All demo records"])
cut=datetime.now()-timedelta(days=7 if window=="7 days" else 30) if window!="All demo records" else df.timestamp.min()
f=df[df.timestamp>=pd.Timestamp(cut)].copy()
if client!="All clients": f=f[f.client==client]
if region!="All regions": f=f[f.region==region]
if f.empty: f=df.copy()

def kpis(d):
    a,b,c,e=st.columns(4)
    a.metric("Availability",f"{d.availability.mean():.2f}%")
    b.metric("Incidents",int(d.incidents.sum()))
    c.metric("SLA sample attainment",f"{(d.availability>=d.sla_target).mean()*100:.1f}%")
    e.metric("Average monthly cost",f"R{d.monthly_cost.mean():,.0f}")

if page=="Executive Overview":
    st.subheader("Executive command centre")
    kpis(f)
    l,r=st.columns(2)
    with l:
        st.markdown("### Availability trend")
        t=f.groupby(f.timestamp.dt.date).availability.mean().reset_index()
        st.plotly_chart(__import__("plotly.express").express.line(t,x="timestamp",y="availability",markers=True).update_layout(template="plotly_dark",height=330),use_container_width=True)
    with r:
        st.markdown("### Operational health")
        s=f.severity.value_counts().reindex(["Normal","High","Critical"],fill_value=0).rename_axis("Health").reset_index(name="Samples")
        st.plotly_chart(__import__("plotly.express").express.pie(s,names="Health",values="Samples",hole=.6).update_layout(template="plotly_dark",height=330),use_container_width=True)
    st.markdown("### Service portfolio")
    st.dataframe(f.groupby("service").agg(Availability=("availability","mean"),Incidents=("incidents","sum"),Latency_ms=("latency_ms","mean")).reset_index(),use_container_width=True,hide_index=True)

elif page=="IT Operations":
    st.subheader("IT operations")
    kpis(f)
    l,r=st.columns(2)
    with l:
        u=f.groupby(f.timestamp.dt.date)[["cpu","memory"]].mean().reset_index()
        st.plotly_chart(__import__("plotly.express").express.line(u,x="timestamp",y=["cpu","memory"]).update_layout(template="plotly_dark",height=330),use_container_width=True)
    with r:
        st.plotly_chart(__import__("plotly.express").express.scatter(f,x="latency_ms",y="cpu",color="severity",hover_data=["service","region"]).update_layout(template="plotly_dark",height=330),use_container_width=True)
    st.dataframe(f.sort_values("timestamp",ascending=False).head(50),use_container_width=True,hide_index=True)

elif page=="AI Intelligence Analyst":
    st.subheader("AI intelligence analyst")
    st.caption("Explainable rule-based analyst in this build. Optional LLM integration requires a separately configured, approved provider and data policy.")
    metrics={"Average CPU":f.cpu.mean(),"Average latency":f.latency_ms.mean(),"Availability":f.availability.mean(),"Critical samples":int((f.severity=="Critical").sum())}
    findings=[]
    if metrics["Average CPU"]>75: findings.append(("High compute pressure",f"Average CPU is {metrics['Average CPU']:.1f}%. Review workload peaks and capacity."))
    if metrics["Average latency"]>180: findings.append(("Elevated latency",f"Average latency is {metrics['Average latency']:.0f} ms. Segment by service and region."))
    if metrics["Availability"]<99.5: findings.append(("Availability below reference",f"Availability is {metrics['Availability']:.2f}% against illustrative 99.5%."))
    if not findings: findings.append(("No threshold breach in selected sample","Continue monitoring and validate against service-specific thresholds."))
    for title,desc in findings:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(desc)
    st.markdown("### Ask analyst (demo)")
    q=st.text_input("Question about the selected data")
    if st.button("Analyse selected data",type="primary"):
        st.write(f"Review {metrics['Critical samples']} critical samples, validate {metrics['Average latency']:.0f} ms average latency and investigate availability at {metrics['Availability']:.2f}%. Correlate time windows with approved ticketing and monitoring sources before assigning root cause. This is an advisory summary based on synthetic records.")
        audit("ANALYST_QUERY",q[:250])

elif page=="Predictive Risk":
    st.subheader("Risk and anomaly workbench")
    x=f.copy()
    for col in ["cpu","memory","latency_ms","availability"]:
        sd=x[col].std() or 1
        x[col+"_z"]=((x[col]-x[col].mean())/sd).abs()
    x["risk_score"]=(x.cpu_z*18+x.memory_z*12+x.latency_ms_z*25+x.availability_z*30+x.incidents.clip(0,4)*12).clip(0,100)
    x["risk_band"]=pd.cut(x.risk_score,[-1,35,65,101],labels=["Low","Medium","High"])
    a,b,c=st.columns(3)
    a.metric("High-risk records",int((x.risk_band=="High").sum()))
    b.metric("Medium-risk records",int((x.risk_band=="Medium").sum()))
    c.metric("Mean heuristic score",f"{x.risk_score.mean():.1f}/100")
    st.plotly_chart(__import__("plotly.express").express.scatter(x,x="timestamp",y="risk_score",color="risk_band",hover_data=["client","service","region"]).update_layout(template="plotly_dark",height=360),use_container_width=True)
    st.dataframe(x.sort_values("risk_score",ascending=False).head(25),use_container_width=True,hide_index=True)

elif page=="SLA Intelligence":
    st.subheader("SLA intelligence")
    f["met"]=f.availability>=f.sla_target
    st.metric("Sample attainment",f"{f.met.mean()*100:.1f}%")
    g=f.groupby("client").agg(Samples=("met","size"),Attainment=("met","mean"),Availability=("availability","mean")).reset_index()
    g["Attainment"]*=100
    st.plotly_chart(__import__("plotly.express").express.bar(g,x="client",y="Attainment",color="Attainment").update_layout(template="plotly_dark",height=340),use_container_width=True)
    st.dataframe(g,use_container_width=True,hide_index=True)
    st.caption("Illustrative sample metric only. Production SLA logic must use signed contracts, exclusions and agreed measurement windows.")

elif page=="Cloud Cost Intelligence":
    st.subheader("Cloud cost intelligence")
    g=f.groupby("client").agg(Avg_Monthly_Cost=("monthly_cost","mean"),CPU=("cpu","mean"),Memory=("memory","mean")).reset_index()
    st.metric("Illustrative monthly cost total",f"R{g.Avg_Monthly_Cost.sum():,.0f}")
    st.plotly_chart(__import__("plotly.express").express.bar(g,x="client",y="Avg_Monthly_Cost",color="Avg_Monthly_Cost").update_layout(template="plotly_dark",height=340),use_container_width=True)
    st.dataframe(g,use_container_width=True,hide_index=True)
    st.warning("Synthetic costs only; not invoices, savings or a forecast.")

elif page=="Customer Experience":
    st.subheader("Customer experience")
    g=f.groupby("client").agg(Satisfaction=("satisfaction","mean"),Incidents=("incidents","sum"),Availability=("availability","mean")).reset_index()
    st.metric("Average satisfaction",f"{f.satisfaction.mean():.2f}/5")
    st.plotly_chart(__import__("plotly.express").express.scatter(g,x="Incidents",y="Satisfaction",size="Availability",color="client").update_layout(template="plotly_dark",height=350),use_container_width=True)
    st.dataframe(g,use_container_width=True,hide_index=True)

elif page=="Integration Hub":
    st.subheader("Integration hub")
    st.warning("Connector setup is a framework demonstration. Do not paste production secrets into this app. Use approved secrets management and MakwaIT security review.")
    st.markdown("### Approved CSV ingestion")
    up=st.file_uploader("Upload a CSV with compatible telemetry columns",type=["csv"])
    required=["timestamp","client","service","region","cpu","memory","latency_ms","availability","incidents","severity","monthly_cost","sla_target","satisfaction"]
    if up is not None:
        try:
            incoming=pd.read_csv(up)
            missing=[c for c in required if c not in incoming.columns]
            if missing: st.error("Missing required columns: "+", ".join(missing))
            else:
                incoming=incoming[required].copy()
                incoming["source"]="User-uploaded CSV"
                if st.button("Import validated CSV",type="primary"):
                    with conn() as c:
                        incoming.to_sql("telemetry",c,if_exists="append",index=False)
                    audit("CSV_IMPORT",f"{len(incoming)} records imported")
                    st.success(f"Imported {len(incoming)} records. Refresh the app to view them.")
        except Exception as ex: st.error(f"Could not read CSV: {ex}")
    st.markdown("### REST connector configuration template")
    endpoint=st.text_input("Approved API endpoint",placeholder="https://api.example.com/telemetry")
    st.caption("This build does not call arbitrary endpoints. A connector must be implemented, security-reviewed and tested for the target API.")
    if st.button("Save endpoint as pending configuration"):
        with conn() as c:
            c.execute("INSERT OR REPLACE INTO connector_config VALUES(?,?,?,?)",("REST API Connector",endpoint,0,"Pending engineering/security approval; not active."))
        audit("CONNECTOR_CONFIG_SAVED","REST endpoint saved as pending")
        st.success("Saved as pending configuration. No connection was made.")
    cfg=pd.read_sql_query("SELECT * FROM connector_config",conn())
    st.dataframe(cfg,use_container_width=True,hide_index=True)

elif page=="Reports & Data":
    st.subheader("Reports and data")
    st.download_button("Download filtered CSV for Excel / Power BI",f.to_csv(index=False).encode(), "makwa_pulse_v2_export.csv","text/csv",type="primary")
    st.markdown("### Power BI hand-off")
    st.write("Import the exported CSV into Power BI Desktop for prototype exploration. Production use should move to a governed SQL view/API with refresh policy, workspace permissions and row-level security.")
    st.markdown("### Audit log")
    logs=pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100",conn())
    st.dataframe(logs,use_container_width=True,hide_index=True)
    st.markdown("### Dataset profile")
    st.write(f"{len(f):,} rows · {len(f.columns)} columns")
    st.dataframe(f.describe(include="all").transpose(),use_container_width=True)

st.markdown("---")
st.caption("MAKWA PULSE V2 · Independent concept demonstration · Synthetic data unless explicitly imported · Not an official MakwaIT product or connected production service.")
