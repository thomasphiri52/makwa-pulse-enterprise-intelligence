# MAKWA PULSE — Production Foundation Stage 1

This is a separate production-foundation build. It is not connected to Makwa IT systems. Do not load Makwa IT confidential or personal information until written authorisation, approved scope, access permissions and security review are complete.

## Included
- Supabase Auth email/password sign-in (no hard-coded demo credentials)
- PostgreSQL schema for user profiles, services, incidents and audit events
- Row Level Security starter policies
- Role-aware Streamlit workspace
- Service register, incident creation and status updates
- Restricted audit-trail view
- Neon Glass Navy Blue interface

## Setup
1. Create a dedicated Supabase development project.
2. Run `supabase/schema.sql` in Supabase SQL Editor.
3. Create a test user in Supabase Authentication.
4. Copy that user's UUID and create a profile using the SQL comment at the end of `schema.sql`.
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and enter the Supabase URL and anon/publishable key. Never commit secrets.
6. Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

For Streamlit Community Cloud, add the same values in App -> Settings -> Secrets.

## Before production
Obtain written Makwa IT authorisation; confirm the data owner, hosting and data-residency requirements; review all RLS policies; implement MFA/SSO and account lifecycle controls; test backups/restores; perform security and privacy assessments; establish monitoring and incident response; and complete user acceptance testing.

The dashboard reads database records only. It does not create synthetic telemetry. This starter is not a security certification, POPIA compliance guarantee, or completed production deployment. The audit table is an application-level audit trail, not tamper-proof infrastructure logging. The starter policies need security review before organisational use.

Do not put a Supabase service-role key in Streamlit secrets or client code.
