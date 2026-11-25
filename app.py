import streamlit as st
import pandas as pd
import numpy as np
import sqlite3, hmac, os, json
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
DB = DATA / "makwa_pulse.db"

st.set_page_config(page_title="MAKWA PULSE V3–V10", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root{--bg:#07111f;--panel:#101f33;--line:#23415f;--cyan:#28d7ff;--muted:#91a9c4}
.stApp{background:radial-gradient(circle at 80% 0%,#102d4a 0%,#07111f 42%);color:#edf6ff}
section[data-testid="stSidebar"]{background:#09192b;border-right:1px solid #1d3855}
.block-container{padding-top:1.1rem;padding-bottom:2rem}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#122941,#0c1b2d);border:1px solid #285071;padding:14px;border-radius:13px;box-shadow:0 0 18px #0b9ac018}
div[data-testid="stDataFrame"]{border:1px solid #23415f;border-radius:10px}
.stButton>button,.stDownloadButton>button{border:1px solid #258db8;border-radius:9px;background:linear-gradient(100deg,#123a5b,#12506a);color:#effaff}
.stButton>button:hover{border-color:#4de2ff;color:white;box-shadow:0 0 15px #27cfff55}
h1,h2,h3{letter-spacing:.2px}
.pulse-sub{color:#91a9c4;font-size:.9rem}
.pulse-card{background:linear-gradient(145deg,#122941dd,#0b1b2cdd);border:1px solid #244867;border-radius:14px;padding:16px}
</style>
""", unsafe_allow_html=True)

USERS = {
    "executive": {"password": "PulseDemo!2026", "role": "Executive"},
    "engineer": {"password": "PulseDemo!2026", "role": "Engineer"},
    "analyst": {"password": "PulseDemo!2026", "role": "Analyst"},
}
NAV = [
    "Command Centre", "V3 · Advanced Intelligence", "V4 · AI Intelligence Engine",
    "V5 · Automation & Workflows", "V6 · Integration Hub", "V7 · Security & Governance",
    "V8 · Predictive Operations", "V9 · Enterprise Command", "V10 · Platform Control",
    "SLA Intelligence", "Cloud Cost Intelligence", "Customer Experience", "IT Operations",
    "Reports & Data"
]

def db():
    return sqlite3.connect(DB)

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS telemetry(
        id INTEGER PRIMARY KEY, timestamp TEXT, client TEXT, service TEXT, region TEXT,
        cpu REAL, memory REAL, latency_ms REAL, availability REAL, incidents INTEGER,
        severity TEXT, monthly_cost REAL, sla_target REAL, satisfaction REAL, source TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, actor TEXT, action TEXT, detail TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS connector_config(
        name TEXT PRIMARY KEY, endpoint TEXT, enabled INTEGER, notes TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS workflow_tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, title TEXT, owner TEXT,
        priority TEXT, status TEXT, due_date TEXT, notes TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS incident_register(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, client TEXT, service TEXT,
        severity TEXT, summary TEXT, status TEXT, owner TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS governance_notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, category TEXT, note TEXT, actor TEXT)""")
        if c.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0] == 0:
            rng=np.random.default_rng(2026)
            clients=["Atlas Financial (DEMO)","Ubuntu Manufacturing (DEMO)","Karoo Health (DEMO)","Coastal Retail (DEMO)","Metsi Logistics (DEMO)"]
            services=["Cloud Platform","Network Services","Identity & Access","Business Applications","Security Operations"]
            regions=["Johannesburg","Cape Town","Durban","Pretoria"]
            rows=[]; now=datetime.now()
            for i in range(720):
                ts=now-timedelta(hours=720-i)
                cpu=float(np.clip(rng.normal(58,17),5,99)); mem=float(np.clip(rng.normal(66,13),10,99))
                lat=float(np.clip(rng.normal(118,38),15,500)); avail=float(np.clip(rng.normal(99.72,.22),97.5,100))
                inc=int(rng.poisson(.2))
                if i in [91,92,237,238,351,509,510,651]: cpu,lat,avail,inc=94,310,98.4,3
                sev="Critical" if inc>=3 or avail<98.8 else ("High" if cpu>85 or lat>230 else "Normal")
                rows.append((ts.isoformat(timespec="minutes"),rng.choice(clients),rng.choice(services),rng.choice(regions),cpu,mem,lat,avail,inc,sev,float(rng.uniform(18000,95000)),99.5,float(np.clip(rng.normal(4.25,.45),2.8,5)),"Synthetic demo generator"))
            c.executemany("""INSERT INTO telemetry(timestamp,client,service,region,cpu,memory,latency_ms,availability,incidents,severity,monthly_cost,sla_target,satisfaction,source)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",rows)
        defaults=[
            ("REST API Connector","",0,"Pending approval; no network calls are made."),
            ("CSV Import","",1,"Validated CSV upload."),
            ("Power BI Export","",1,"CSV hand-off only; no live tenant connection.")
        ]
        c.executemany("INSERT OR IGNORE INTO connector_config VALUES(?,?,?,?)",defaults)
init_db()

def audit(action, detail):
    with db() as c:
        c.execute("INSERT INTO audit_log(timestamp,actor,action,detail) VALUES(?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"),st.session_state.get("user","unknown"),action,str(detail)[:500]))

def login():
    st.title("◈ MAKWA PULSE")
    st.subheader("V3–V10 Enterprise Intelligence & Automation Console")
    st.info("Independent concept demonstration for discussion with MakwaIT management and engineering teams. Not an official MakwaIT product and not connected to production systems.")
    with st.form("login"):
        username=st.text_input("Username","executive")
        password=st.text_input("Password",type="password",value="PulseDemo!2026")
        ok=st.form_submit_button("Sign in",type="primary")
    if ok:
        u=USERS.get(username.lower())
        if u and hmac.compare_digest(password,u["password"]):
            st.session_state.user=username.lower(); st.session_state.role=u["role"]; st.rerun()
        else: st.error("Invalid demo credentials.")
    st.caption("Demo accounts: executive / engineer / analyst · Password: PulseDemo!2026 · Local evaluation only.")

if "user" not in st.session_state:
    login(); st.stop()

role=st.session_state.role
st.sidebar.markdown("# ◈ MAKWA PULSE")
st.sidebar.caption("V3–V10 · ENTERPRISE INTELLIGENCE")
st.sidebar.success(f"Signed in · {role}")
if st.sidebar.button("Sign out"):
    st.session_state.clear(); st.rerun()
page=st.sidebar.radio("PLATFORM MODULES",NAV)
st.sidebar.divider()
st.sidebar.caption("Environment: DEMO / SYNTHETIC DATA")
st.sidebar.caption("No production systems connected.")

df=pd.read_sql_query("SELECT * FROM telemetry ORDER BY timestamp",db(),parse_dates=["timestamp"])
st.title("◈ MAKWA PULSE")
st.markdown("<div class='pulse-sub'>Enterprise service intelligence · Integrated V3–V10 concept build</div>",unsafe_allow_html=True)

a,b,c=st.columns(3)
with a: client=st.selectbox("Client",["All clients"]+sorted(df.client.unique().tolist()))
with b: region=st.selectbox("Region",["All regions"]+sorted(df.region.unique().tolist()))
with c: window=st.selectbox("Data window",["7 days","30 days","All demo records"])
cut=datetime.now()-timedelta(days=7 if window=="7 days" else 30) if window!="All demo records" else df.timestamp.min()
f=df[df.timestamp>=pd.Timestamp(cut)].copy()
if client!="All clients": f=f[f.client==client]
if region!="All regions": f=f[f.region==region]
if f.empty: f=df.copy()

def kpis(d):
    cols=st.columns(4)
    cols[0].metric("Availability",f"{d.availability.mean():.2f}%")
    cols[1].metric("Incidents",int(d.incidents.sum()))
    cols[2].metric("SLA sample attainment",f"{(d.availability>=d.sla_target).mean()*100:.1f}%")
    cols[3].metric("Average monthly cost",f"R{d.monthly_cost.mean():,.0f}")

def risk_frame(d):
    x=d.copy()
    for col in ["cpu","memory","latency_ms","availability"]:
        sd=x[col].std()
        x[col+"_z"]=((x[col]-x[col].mean())/(sd if pd.notna(sd) and sd else 1)).abs()
    x["risk_score"]=(x.cpu_z*18+x.memory_z*12+x.latency_ms_z*25+x.availability_z*30+x.incidents.clip(0,4)*12).clip(0,100)
    x["risk_band"]=pd.cut(x.risk_score,[-1,35,65,101],labels=["Low","Medium","High"])
    return x

def chart_line(data,x,y,title=None):
    import plotly.express as px
    fig=px.line(data,x=x,y=y,markers=True,title=title)
    fig.update_layout(template="plotly_dark",height=330,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True)

def show_table(data):
    st.dataframe(data,use_container_width=True,hide_index=True)

if page=="Command Centre":
    st.subheader("Executive command centre")
    kpis(f)
    l,r=st.columns(2)
    with l:
        t=f.groupby(f.timestamp.dt.date).availability.mean().reset_index()
        chart_line(t,"timestamp","availability","Availability trend")
    with r:
        import plotly.express as px
        s=f.severity.value_counts().reindex(["Normal","High","Critical"],fill_value=0).rename_axis("Health").reset_index(name="Samples")
        fig=px.pie(s,names="Health",values="Samples",hole=.62); fig.update_layout(template="plotly_dark",height=330)
        st.plotly_chart(fig,use_container_width=True)
    show_table(f.groupby("service").agg(Availability=("availability","mean"),Incidents=("incidents","sum"),Latency_ms=("latency_ms","mean")).reset_index())

elif page=="V3 · Advanced Intelligence":
    st.subheader("V3 · Advanced Intelligence")
    kpis(f)
    f["availability_gap"]=f.sla_target-f.availability
    f["cost_per_incident"]=f.monthly_cost/f.incidents.clip(lower=1)
    l,r=st.columns(2)
    with l:
        chart_line(f.groupby(f.timestamp.dt.date).agg(CPU=("cpu","mean"),Memory=("memory","mean")).reset_index(),"timestamp",["CPU","Memory"],"Compute utilisation")
    with r:
        import plotly.express as px
        agg=f.groupby("service").agg(Latency=("latency_ms","mean"),Incidents=("incidents","sum")).reset_index()
        fig=px.scatter(agg,x="Latency",y="Incidents",size="Incidents",color="service"); fig.update_layout(template="plotly_dark",height=330)
        st.plotly_chart(fig,use_container_width=True)
    st.markdown("#### Service intelligence detail")
    show_table(f.groupby(["client","service"]).agg(Availability=("availability","mean"),CPU=("cpu","mean"),Latency=("latency_ms","mean"),Incidents=("incidents","sum"),Cost=("monthly_cost","mean")).reset_index())

elif page=="V4 · AI Intelligence Engine":
    st.subheader("V4 · AI Intelligence Engine")
    st.caption("Explainable, deterministic rules engine. It is not a live generative-AI model and does not infer verified root cause.")
    metrics={"CPU":f.cpu.mean(),"Latency":f.latency_ms.mean(),"Availability":f.availability.mean(),"Critical samples":int((f.severity=="Critical").sum())}
    findings=[]
    if metrics["CPU"]>75: findings.append(("High compute pressure",f"Average CPU is {metrics['CPU']:.1f}%. Review workload peaks and capacity."))
    if metrics["Latency"]>180: findings.append(("Elevated latency",f"Average latency is {metrics['Latency']:.0f} ms. Segment by service and region."))
    if metrics["Availability"]<99.5: findings.append(("Availability below illustrative reference",f"Availability is {metrics['Availability']:.2f}% against 99.5%."))
    if metrics["Critical samples"]: findings.append(("Critical telemetry samples",f"{metrics['Critical samples']} records are labelled Critical; validate against source monitoring and ticket records."))
    if not findings: findings.append(("No threshold breach in sample","Continue monitoring and validate service-specific thresholds."))
    for title,desc in findings:
        with st.container(border=True): st.markdown(f"**{title}**"); st.write(desc)
    st.markdown("#### Ask the rules analyst")
    q=st.text_input("Question about the filtered sample",placeholder="What should the operations team review?")
    if st.button("Generate advisory",type="primary"):
        st.write(f"Advisory: review {metrics['Critical samples']} critical samples, {metrics['Latency']:.0f} ms mean latency and {metrics['Availability']:.2f}% availability. Correlate with approved incident and change records before assigning root cause. This output is based on synthetic or imported telemetry.")
        audit("RULES_ANALYST_QUERY",q)

elif page=="V5 · Automation & Workflows":
    st.subheader("V5 · Automation & Workflows")
    st.caption("Workflow records and simulated alert generation only. No email, SMS, ticket or remediation is sent.")
    x=risk_frame(f); alerts=x[x.risk_band.astype(str)=="High"].sort_values("risk_score",ascending=False).head(20)
    st.metric("High-risk alert candidates",len(alerts))
    with st.expander("Review alert candidates",expanded=True):
        show_table(alerts[["timestamp","client","service","severity","risk_score","risk_band"]])
        if st.button("Create follow-up tasks from candidates"):
            with db() as c:
                for _,row in alerts.iterrows():
                    c.execute("INSERT INTO workflow_tasks(created_at,title,owner,priority,status,due_date,notes) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now().isoformat(timespec="minutes"),f"Review {row.service} risk · {row.client}","Unassigned","High","Open",(datetime.now()+timedelta(days=1)).date().isoformat(),"Generated from demo risk heuristic; validate source event."))
            audit("WORKFLOW_TASKS_CREATED",len(alerts)); st.success(f"Created {len(alerts)} demo follow-up tasks."); st.rerun()
    st.markdown("#### Create a workflow task")
    with st.form("task_form"):
        title=st.text_input("Task title"); owner=st.text_input("Owner","Unassigned")
        priority=st.selectbox("Priority",["Low","Medium","High","Critical"])
        due=st.date_input("Due date",datetime.now().date()+timedelta(days=2))
        notes=st.text_area("Notes")
        submit=st.form_submit_button("Save task")
    if submit and title.strip():
        with db() as c: c.execute("INSERT INTO workflow_tasks(created_at,title,owner,priority,status,due_date,notes) VALUES(?,?,?,?,?,?,?)",(datetime.now().isoformat(timespec="minutes"),title.strip(),owner,priority,"Open",due.isoformat(),notes))
        audit("WORKFLOW_TASK_CREATED",title); st.success("Task saved."); st.rerun()
    tasks=pd.read_sql_query("SELECT * FROM workflow_tasks ORDER BY id DESC",db())
    if not tasks.empty:
        show_table(tasks)
        ids=tasks.id.astype(int).tolist()
        chosen=st.selectbox("Update task status",ids,format_func=lambda i:f"#{i} · {tasks.loc[tasks.id==i,'title'].iloc[0]}")
        status=st.selectbox("New status",["Open","In progress","Blocked","Completed"])
        if st.button("Update selected task"):
            with db() as c: c.execute("UPDATE workflow_tasks SET status=? WHERE id=?",(status,int(chosen)))
            audit("WORKFLOW_TASK_UPDATED",f"{chosen}: {status}"); st.success("Task updated."); st.rerun()

elif page=="V6 · Integration Hub":
    st.subheader("V6 · Integration Hub")
    st.warning("Integration framework only. The REST connector does not make network calls. Never paste production secrets into this demo.")
    required=["timestamp","client","service","region","cpu","memory","latency_ms","availability","incidents","severity","monthly_cost","sla_target","satisfaction"]
    up=st.file_uploader("Import approved telemetry CSV",type=["csv"])
    if up is not None:
        try:
            incoming=pd.read_csv(up); missing=[x for x in required if x not in incoming.columns]
            if missing: st.error("Missing columns: "+", ".join(missing))
            else:
                incoming=incoming[required].copy()
                numeric=["cpu","memory","latency_ms","availability","incidents","monthly_cost","sla_target","satisfaction"]
                for col in numeric: incoming[col]=pd.to_numeric(incoming[col],errors="raise")
                incoming["timestamp"]=pd.to_datetime(incoming["timestamp"],errors="raise").astype(str)
                incoming["source"]="Validated CSV import"
                if st.button("Confirm import",type="primary"):
                    with db() as c: incoming.to_sql("telemetry",c,if_exists="append",index=False)
                    audit("CSV_IMPORT",f"{len(incoming)} rows"); st.success(f"Imported {len(incoming)} rows."); st.rerun()
        except Exception as e: st.error(f"CSV validation failed: {e}")
    st.markdown("#### Pending connector configuration")
    with st.form("connector"):
        name=st.selectbox("Connector",["REST API Connector","Approved Monitoring Export","ITSM Connector"])
        endpoint=st.text_input("Approved endpoint / documentation reference")
        notes=st.text_area("Owner, approval and scope notes")
        save=st.form_submit_button("Save pending configuration")
    if save:
        with db() as c: c.execute("INSERT OR REPLACE INTO connector_config VALUES(?,?,?,?)",(name,endpoint,0,notes or "Pending security approval"))
        audit("CONNECTOR_CONFIG_SAVED",name); st.success("Saved as pending. No connection was made.")
    show_table(pd.read_sql_query("SELECT * FROM connector_config",db()))

elif page=="V7 · Security & Governance":
    st.subheader("V7 · Security & Governance")
    st.warning("Local demo sign-in is not production authentication. Replace with approved SSO/OIDC, MFA and managed secrets before deployment.")
    a,b,c=st.columns(3)
    a.metric("Current role",role); b.metric("Audit events",int(pd.read_sql_query("SELECT COUNT(*) n FROM audit_log",db()).iloc[0,0])); c.metric("Governance notes",int(pd.read_sql_query("SELECT COUNT(*) n FROM governance_notes",db()).iloc[0,0]))
    st.markdown("#### Governance register")
    with st.form("gov"):
        category=st.selectbox("Category",["Access review","Data quality","Risk acceptance","Change approval","Retention","Security review"])
        note=st.text_area("Record decision, owner and follow-up")
        add=st.form_submit_button("Add governance record")
    if add and note.strip():
        with db() as c: c.execute("INSERT INTO governance_notes(created_at,category,note,actor) VALUES(?,?,?,?)",(datetime.now().isoformat(timespec="minutes"),category,note,st.session_state.user))
        audit("GOVERNANCE_NOTE_ADDED",category); st.success("Governance record added."); st.rerun()
    show_table(pd.read_sql_query("SELECT * FROM governance_notes ORDER BY id DESC",db()))
    st.markdown("#### Audit trail")
    show_table(pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200",db()))

elif page=="V8 · Predictive Operations":
    st.subheader("V8 · Predictive Operations")
    st.caption("Statistical risk indicators and simple trend projections for demonstration. Not validated forecasts or predictive maintenance.")
    x=risk_frame(f)
    a,b,c=st.columns(3); a.metric("High risk",int((x.risk_band.astype(str)=="High").sum())); b.metric("Medium risk",int((x.risk_band.astype(str)=="Medium").sum())); c.metric("Mean heuristic score",f"{x.risk_score.mean():.1f}/100")
    import plotly.express as px
    fig=px.scatter(x,x="timestamp",y="risk_score",color="risk_band",hover_data=["client","service","region"]); fig.update_layout(template="plotly_dark",height=360)
    st.plotly_chart(fig,use_container_width=True)
    st.markdown("#### Capacity trend snapshot")
    trend=f.sort_values("timestamp").groupby(f.timestamp.dt.date).agg(CPU=("cpu","mean"),Memory=("memory","mean"),Latency=("latency_ms","mean")).reset_index()
    chart_line(trend,"timestamp",["CPU","Memory","Latency"],"Observed daily averages")
    show_table(x.sort_values("risk_score",ascending=False).head(30))

elif page=="V9 · Enterprise Command":
    st.subheader("V9 · Enterprise Command")
    st.caption("Multi-client view over the synthetic/demo tenant labels in this local database. Tenant isolation is not implemented.")
    portfolio=f.groupby("client").agg(Records=("id","count"),Availability=("availability","mean"),Incidents=("incidents","sum"),Mean_Cost=("monthly_cost","mean"),Satisfaction=("satisfaction","mean")).reset_index()
    portfolio["Availability"]=portfolio.Availability.round(3); portfolio["Satisfaction"]=portfolio.Satisfaction.round(2)
    show_table(portfolio)
    st.markdown("#### Incident register")
    with st.form("incident"):
        iclient=st.selectbox("Client",sorted(df.client.unique()))
        service=st.selectbox("Service",sorted(df.service.unique()))
        sev=st.selectbox("Severity",["Low","Medium","High","Critical"])
        summary=st.text_input("Incident summary")
        owner=st.text_input("Incident owner","Unassigned")
        create=st.form_submit_button("Create incident record")
    if create and summary.strip():
        with db() as c: c.execute("INSERT INTO incident_register(created_at,client,service,severity,summary,status,owner) VALUES(?,?,?,?,?,?,?)",(datetime.now().isoformat(timespec="minutes"),iclient,service,sev,summary,"Open",owner))
        audit("INCIDENT_REGISTER_CREATED",summary); st.success("Incident record saved."); st.rerun()
    incidents=pd.read_sql_query("SELECT * FROM incident_register ORDER BY id DESC",db())
    if not incidents.empty: show_table(incidents)

elif page=="V10 · Platform Control":
    st.subheader("V10 · Platform Control")
    st.markdown("#### Platform readiness")
    checks=[
        ("V3 analytics and filtered views","Available in demo"),
        ("V4 explainable rules analyst","Available; not a live LLM"),
        ("V5 task workflow register","Available; no external notifications"),
        ("V6 CSV import and pending connector registry","Available; no live API calls"),
        ("V7 local audit and governance register","Available; demo controls only"),
        ("V8 statistical risk indicators","Available; not validated forecasting"),
        ("V9 portfolio and incident register","Available; no tenant isolation"),
        ("V10 export and platform status","Available; local SQLite")
    ]
    show_table(pd.DataFrame(checks,columns=["Capability","Status"]))
    st.markdown("#### Environment and maintenance")
    st.code(f"Python app: Streamlit\nDatabase: {DB.name}\nTelemetry rows: {len(df)}\nCurrent user role: {role}\nEnvironment: local demo")
    st.download_button("Download full telemetry backup (CSV)",df.to_csv(index=False).encode(),"makwa_pulse_telemetry_backup.csv","text/csv")
    st.download_button("Download platform audit log (CSV)",pd.read_sql_query("SELECT * FROM audit_log",db()).to_csv(index=False).encode(),"makwa_pulse_audit.csv","text/csv")
    st.info("For production: implement managed database, secrets manager, SSO/MFA, tenant-level authorisation, backup/restore, retention, monitoring, security testing and approved integrations.")

elif page=="SLA Intelligence":
    st.subheader("SLA intelligence")
    f["met"]=f.availability>=f.sla_target
    st.metric("Sample attainment",f"{f.met.mean()*100:.1f}%")
    g=f.groupby("client").agg(Samples=("met","size"),Attainment=("met","mean"),Availability=("availability","mean")).reset_index(); g["Attainment"]*=100
    import plotly.express as px
    fig=px.bar(g,x="client",y="Attainment",color="Attainment"); fig.update_layout(template="plotly_dark",height=340)
    st.plotly_chart(fig,use_container_width=True); show_table(g)
    st.caption("Illustrative sample metric only. Production SLA calculations require signed contracts and agreed measurement rules.")

elif page=="Cloud Cost Intelligence":
    st.subheader("Cloud cost intelligence")
    g=f.groupby("client").agg(Avg_Monthly_Cost=("monthly_cost","mean"),CPU=("cpu","mean"),Memory=("memory","mean")).reset_index()
    st.metric("Illustrative monthly cost total",f"R{g.Avg_Monthly_Cost.sum():,.0f}")
    import plotly.express as px
    fig=px.bar(g,x="client",y="Avg_Monthly_Cost",color="Avg_Monthly_Cost"); fig.update_layout(template="plotly_dark",height=340)
    st.plotly_chart(fig,use_container_width=True); show_table(g)
    st.warning("Synthetic costs only; not invoices, savings or forecasts.")

elif page=="Customer Experience":
    st.subheader("Customer experience")
    g=f.groupby("client").agg(Satisfaction=("satisfaction","mean"),Incidents=("incidents","sum"),Availability=("availability","mean")).reset_index()
    st.metric("Average satisfaction",f"{f.satisfaction.mean():.2f}/5")
    import plotly.express as px
    fig=px.scatter(g,x="Incidents",y="Satisfaction",size="Availability",color="client"); fig.update_layout(template="plotly_dark",height=350)
    st.plotly_chart(fig,use_container_width=True); show_table(g)

elif page=="IT Operations":
    st.subheader("IT operations")
    kpis(f)
    l,r=st.columns(2)
    with l:
        t=f.groupby(f.timestamp.dt.date)[["cpu","memory"]].mean().reset_index()
        chart_line(t,"timestamp",["cpu","memory"],"Compute utilisation")
    with r:
        import plotly.express as px
        fig=px.scatter(f,x="latency_ms",y="cpu",color="severity",hover_data=["service","region"]); fig.update_layout(template="plotly_dark",height=330)
        st.plotly_chart(fig,use_container_width=True)
    show_table(f.sort_values("timestamp",ascending=False).head(50))

elif page=="Reports & Data":
    st.subheader("Reports & Data")
    st.download_button("Download filtered CSV for Excel / Power BI",f.to_csv(index=False).encode(),"makwa_pulse_filtered_export.csv","text/csv",type="primary")
    st.markdown("#### Dataset profile")
    st.write(f"{len(f):,} rows · {len(f.columns)} columns")
    show_table(f.describe(include="all").transpose())
    st.markdown("#### Recent audit log")
    show_table(pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100",db()))

st.divider()
st.caption("MAKWA PULSE V3–V10 · Independent concept demonstration · Synthetic data unless explicitly imported · Not an official MakwaIT product or connected production service.")
