import os
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="MAKWA PULSE | Production", page_icon="◈", layout="wide")
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp{background:radial-gradient(ellipse at 85% 0%,rgba(45,116,214,.2),transparent 35%),linear-gradient(145deg,#050b17,#09172c 55%,#07101e);color:#eef5ff}
.block-container{max-width:1500px;padding-top:1.7rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;color:#f3f8ff!important}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1b33,#071326);border-right:1px solid #294665}
div[data-testid="stMetric"]{background:rgba(15,31,56,.8);border:1px solid #294665;border-radius:15px;padding:14px}
.stButton>button,.stFormSubmitButton>button{border:1px solid #397caa;border-radius:10px;background:linear-gradient(100deg,#173f68,#34285f);color:#fff;font-weight:700}
.pulse-hero{padding:22px;border:1px solid #315273;border-radius:18px;background:linear-gradient(110deg,rgba(21,55,91,.8),rgba(38,34,83,.6));margin-bottom:18px}
.kicker{color:#59e2ff;font-size:11px;font-weight:800;letter-spacing:.18em}
.pulse-title{font-family:'Space Grotesk';font-size:30px;font-weight:700;color:#f5f9ff}
.muted{color:#a9bed8;font-size:13px}
</style>
''', unsafe_allow_html=True)

def setting(k):
    try:
        return st.secrets.get(k, os.getenv(k))
    except Exception:
        return os.getenv(k)

@st.cache_resource
def sb():
    url, key = setting("SUPABASE_URL"), setting("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Configure SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets.")
    return create_client(url, key)

def audit(client, action, entity=None, entity_id=None, details=None):
    client.table("audit_logs").insert({
        "actor_id": st.session_state.user_id, "action": action,
        "entity_type": entity, "entity_id": entity_id, "details": details or {}
    }).execute()

def logout():
    try:
        sb().auth.sign_out()
    except Exception:
        pass
    for key in ("access_token", "refresh_token", "user_id", "email"):
        st.session_state.pop(key, None)
    st.rerun()

def login():
    st.markdown('<div class="pulse-hero"><div class="kicker">SECURE WORKSPACE</div><div class="pulse-title">MAKWA PULSE</div><div class="muted">Production foundation · Supabase authentication</div></div>', unsafe_allow_html=True)
    st.warning("Development environment only. Do not enter Makwa IT confidential data until written authorisation and security approval are in place.")
    with st.form("login"):
        email = st.text_input("Work email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in securely", use_container_width=True)
    if submit:
        try:
            result = sb().auth.sign_in_with_password({"email": email.strip(), "password": password})
            if not result.user or not result.session:
                st.error("Sign-in was not completed.")
                return
            st.session_state.access_token = result.session.access_token
            st.session_state.refresh_token = result.session.refresh_token
            st.session_state.user_id = result.user.id
            st.session_state.email = result.user.email
            st.rerun()
        except Exception as e:
            st.error(f"Sign-in failed: {e}")

def client_for_user():
    client = sb()
    client.postgrest.auth(st.session_state.access_token)
    return client

def get_profile(client):
    res = client.table("profiles").select("display_name,role,active").eq("id", st.session_state.user_id).maybe_single().execute()
    p = res.data
    if not p or not p.get("active"):
        st.error("No active user profile. Contact the authorised administrator.")
        logout()
    return p

def main():
    if not st.session_state.get("access_token"):
        login()
        st.stop()
    try:
        client = client_for_user()
        profile = get_profile(client)
        role = profile["role"]
        st.sidebar.markdown("## ◈ MAKWA PULSE")
        st.sidebar.caption("Production foundation")
        st.sidebar.write(st.session_state.email)
        page = st.sidebar.radio("WORKSPACE", ["Command Centre", "Service Management", "Incidents", "Audit Trail"])
        if st.sidebar.button("Sign out", use_container_width=True):
            logout()

        st.markdown(f'<div class="pulse-hero"><div class="kicker">ENTERPRISE OPERATIONS INTELLIGENCE</div><div class="pulse-title">{page}</div><div class="muted">Signed in as {st.session_state.email} · {role.replace("_"," ").title()}</div></div>', unsafe_allow_html=True)

        if page == "Command Centre":
            services = client.table("services").select("id,name,status,environment,updated_at").execute().data or []
            incidents = client.table("incidents").select("id,title,status,priority,created_at").execute().data or []
            open_items = [x for x in incidents if x["status"] not in ("resolved", "closed")]
            a,b,c,d = st.columns(4)
            a.metric("Registered services", len(services))
            b.metric("Healthy services", sum(x["status"] == "healthy" for x in services))
            c.metric("Open incidents", len(open_items))
            d.metric("Incident records", len(incidents))
            st.caption("Metrics are calculated from database records; no demo telemetry is generated.")
            l,r = st.columns([1.2,1])
            with l:
                st.subheader("Service register")
                st.dataframe(pd.DataFrame(services) if services else pd.DataFrame(columns=["name","status","environment"]), use_container_width=True, hide_index=True)
            with r:
                st.subheader("Incident status")
                if incidents:
                    counts = pd.DataFrame(incidents).groupby("status").size().reset_index(name="count")
                    fig = px.pie(counts, names="status", values="count", hole=.6)
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No incident records yet.")

        elif page == "Service Management":
            if role in ("platform_admin", "operations_manager"):
                with st.form("new_service"):
                    name = st.text_input("Service name")
                    env = st.selectbox("Environment", ["development","staging","production"])
                    status = st.selectbox("Status", ["unknown","healthy","degraded","outage"])
                    save = st.form_submit_button("Register service")
                if save:
                    if not name.strip():
                        st.error("Enter a service name.")
                    else:
                        row = client.table("services").insert({"name":name.strip(),"environment":env,"status":status}).execute().data[0]
                        audit(client, "service.created", "service", row["id"], {"name":name.strip()})
                        st.success("Service registered.")
                        st.rerun()
            else:
                st.info("Your role has read-only service access.")
            data = client.table("services").select("*").order("created_at", desc=True).execute().data or []
            st.dataframe(pd.DataFrame(data) if data else pd.DataFrame(), use_container_width=True, hide_index=True)

        elif page == "Incidents":
            services = client.table("services").select("id,name").execute().data or []
            service_map = {x["name"]:x["id"] for x in services}
            with st.form("new_incident"):
                title = st.text_input("Incident title")
                desc = st.text_area("Description")
                priority = st.selectbox("Priority", ["low","medium","high","critical"])
                service = st.selectbox("Related service", ["Unassigned"] + list(service_map))
                save = st.form_submit_button("Create incident")
            if save:
                if not title.strip():
                    st.error("Incident title is required.")
                else:
                    row = client.table("incidents").insert({
                        "title":title.strip(),"description":desc.strip(),"priority":priority,
                        "status":"open","service_id":service_map.get(service),"created_by":st.session_state.user_id
                    }).execute().data[0]
                    audit(client, "incident.created", "incident", row["id"], {"priority":priority})
                    st.success("Incident created.")
                    st.rerun()
            rows = client.table("incidents").select("*").order("created_at", desc=True).execute().data or []
            st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), use_container_width=True, hide_index=True)
            if role in ("platform_admin", "operations_manager") and rows:
                options = {f'{x["title"]} · {x["id"][:8]}':x["id"] for x in rows}
                selected = st.selectbox("Select incident to update", list(options))
                status = st.selectbox("New status", ["open","investigating","pending","resolved","closed"])
                if st.button("Update incident status"):
                    iid = options[selected]
                    client.table("incidents").update({"status":status,"updated_at":datetime.now(timezone.utc).isoformat()}).eq("id",iid).execute()
                    audit(client, "incident.status_changed", "incident", iid, {"status":status})
                    st.success("Incident updated.")
                    st.rerun()

        elif page == "Audit Trail":
            if role != "platform_admin":
                st.warning("Audit trail is restricted to platform administrators.")
            else:
                rows = client.table("audit_logs").select("*").order("created_at", desc=True).limit(250).execute().data or []
                st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), use_container_width=True, hide_index=True)

        st.divider()
        st.caption("MAKWA PULSE · Stage 1 production foundation · No Makwa IT production integrations enabled")
    except Exception as e:
        st.error(f"Workspace error: {e}")
        st.info("Check Supabase configuration, database schema, user profile and row-level security.")

if __name__ == "__main__":
    main()
