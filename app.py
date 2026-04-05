import streamlit as st
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 1. CONFIGURARE API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1GZ_cZLcrirq5Jhw86ZOiw67I9GES8rLxa0UDJz2szEE'
PAGINI_PERMISE = ["1", "2", "3", "4", "5", "6", "7", "8", "PATISERIE 2", "TORTURI", "CASEROLE SI PUNGI "]

def get_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def este_numar_valid(valoare):
    if valoare is None: return None
    s_val = str(valoare).strip().replace(',', '.')
    if s_val == "" or s_val == "0" or s_val == "0.0": return None
    try:
        val = float(s_val)
        return val if val > 0 else None
    except ValueError:
        return None

# 2. DESIGN
st.set_page_config(layout="wide", page_title="Productie Laborator")

st.markdown("""
<style>
    .stApp { background-color: white; }
    .titlu-pagina { color: #cc0000; font-size: 30px !important; font-weight: 900; text-align: center; margin-bottom: 20px; }
    .header-produs-rosu { background-color: #cc0000; color: white; font-size: 22px !important; font-weight: bold; padding: 10px; margin: 20px 0 10px 0; text-align: center; border-radius: 5px; }
    .header-produs-verde { background-color: #28a745; color: white; font-size: 22px !important; font-weight: bold; padding: 10px; margin: 20px 0 10px 0; text-align: center; border-radius: 5px; }
    .container-lucru { background-color: #ffeded !important; padding: 12px !important; border-radius: 8px !important; margin-bottom: 8px !important; border-left: 8px solid #cc0000 !important; }
    .container-finalizat { background-color: #e8f5e9 !important; padding: 12px !important; border-radius: 8px !important; margin-bottom: 8px !important; border-left: 8px solid #28a745 !important; }
    .text-client { font-size: 18px !important; font-weight: 800; color: #1a1a1a; margin: 0 !important; }
    .text-cantitate-fixa { font-size: 20px !important; font-weight: 900; color: #2e7d32; }
    .stButton button { background-color: white !important; }
</style>
""", unsafe_allow_html=True)

if 'finalizate_date' not in st.session_state: st.session_state.finalizate_date = {} 
if 'modificari_cantitate' not in st.session_state: st.session_state.modificari_cantitate = {}
if 'idx_pag' not in st.session_state: st.session_state.idx_pag = 0

def get_data_fresh(nume_p):
    service = build('sheets', 'v4', credentials=get_creds())
    
    # REGULI DEFINITE DE TINE:
    if nume_p == "PATISERIE 2":
        ranges = [f"'{nume_p}'!C4:F4", f"'{nume_p}'!B5:B35", f"'{nume_p}'!C5:F35", f"'{nume_p}'!I5:I31", f"'{nume_p}'!J5:L31"]
    elif nume_p in ["3", "4", "7", "8", "CASEROLE SI PUNGI "]:
        # Clienti C3:K3, Cantitati C4:K37
        ranges = [f"'{nume_p}'!C3:K3", f"'{nume_p}'!B4:B37", f"'{nume_p}'!C4:K37"]
    elif nume_p in ["5", "6"]:
        # Clienti C3:L3, Cantitati C4:L37
        ranges = [f"'{nume_p}'!C3:L3", f"'{nume_p}'!B4:B37", f"'{nume_p}'!C4:L37"]
    else:
        # Default pentru restul (1, 2, TORTURI)
        ranges = [f"'{nume_p}'!C3:J3", f"'{nume_p}'!B4:B45", f"'{nume_p}'!C4:J45"]
        
    return service.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=ranges).execute()

try:
    nume_p = PAGINI_PERMISE[st.session_state.idx_pag]

    # NAVIGARE
    c_titlu, c_ref = st.columns([4, 1.2])
    with c_titlu:
        st.markdown(f'<div class="titlu-pagina">PAGINA: {nume_p}</div>', unsafe_allow_html=True)
    with c_ref:
        if st.button("🔄 REFRESH DATE"):
            st.cache_data.clear()
            st.session_state.modificari_cantitate = {}
            st.rerun()
    
    c_prev, _, c_next = st.columns([1, 1, 1])
    if c_prev.button("⬅️ PRECEDENTA"):
        st.session_state.idx_pag = (st.session_state.idx_pag - 1) % len(PAGINI_PERMISE)
        st.rerun()
    if c_next.button("URMATOAREA ➡️"):
        st.session_state.idx_pag = (st.session_state.idx_pag + 1) % len(PAGINI_PERMISE)
        st.rerun()

    res = get_data_fresh(nume_p)
    v_ranges = res.get('valueRanges', [])
    comenzi_toate = []

    if nume_p == "PATISERIE 2":
        t1_cli = v_ranges[0].get('values', [[]])[0]
        t1_prod = v_ranges[1].get('values', [])
        t1_mat = v_ranges[2].get('values', [])
        t2_cli = v_ranges[3].get('values', [])
        t2_mat = v_ranges[4].get('values', [])
        nume_checuri = ["CHEC SIMPLU", "CHEC MARMORAT", "CHEC NEGRU"]
        for r_idx, row in enumerate(t1_prod):
            p_nume = row[0].strip().upper() if row else ""
            if not p_nume or p_nume.replace('.','').isdigit() or "TOTAL" in p_nume: continue
            for c_idx, c_nume in enumerate(t1_cli):
                val = este_numar_valid(t1_mat[r_idx][c_idx]) if r_idx < len(t1_mat) and c_idx < len(t1_mat[r_idx]) else None
                if val: comenzi_toate.append((p_nume, c_nume, val, f"T1_{r_idx}_{c_idx}"))
        for r_idx, row in enumerate(t2_cli):
            c_nume = row[0].strip().upper() if row else ""
            if not c_nume or "TOTAL" in c_nume: continue
            for c_idx, p_nume in enumerate(nume_checuri):
                val = este_numar_valid(t2_mat[r_idx][c_idx]) if r_idx < len(t2_mat) and c_idx < len(t2_mat[r_idx]) else None
                if val: comenzi_toate.append((p_nume, c_nume, val, f"T2_{r_idx}_{c_idx}"))
    else:
        clienti_list = v_ranges[0].get('values', [[]])[0]
        produse_list = v_ranges[1].get('values', [])
        matrice = v_ranges[2].get('values', [])
        for r_idx, row in enumerate(produse_list):
            p_nume = row[0].strip().upper() if row else ""
            if not p_nume or p_nume.isdigit() or "TOTAL" in p_nume: continue
            for c_idx, c_nume in enumerate(clienti_list):
                val = este_numar_valid(matrice[r_idx][c_idx]) if r_idx < len(matrice) and c_idx < len(matrice[r_idx]) else None
                if val: comenzi_toate.append((p_nume, c_nume, val, f"{r_idx}_{c_idx}"))

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h2 style='text-align: center; color: #cc0000;'>🔴 ÎN CURS</h2>", unsafe_allow_html=True)
        prod_active = sorted(list(set([x[0] for x in comenzi_toate])))
        for p in prod_active:
            items = [x for x in comenzi_toate if x[0] == p and f"{nume_p}_{x[0]}_{x[1]}_{x[3]}" not in st.session_state.finalizate_date]
            if items:
                st.markdown(f'<div class="header-produs-rosu">{p}</div>', unsafe_allow_html=True)
                for p_n, c_n, c_v, c_id in items:
                    uid = f"{nume_p}_{p_n}_{c_n}_{c_id}"
                    st.markdown('<div class="container-lucru">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([2.5, 0.8, 1])
                    c1.markdown(f'<p class="text-client">👤 {c_n}</p>', unsafe_allow_html=True)
                    curr_val = st.session_state.modificari_cantitate.get(uid, c_v)
                    n_cant = c2.text_input("buc", value=str(curr_val), key=f"ed_{uid}", label_visibility="collapsed")
                    if n_cant != str(curr_val):
                        st.session_state.modificari_cantitate[uid] = n_cant
                        st.rerun()
                    if c3.button("GATA", key=f"bt_{uid}"):
                        st.session_state.finalizate_date[uid] = n_cant
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("<h2 style='text-align: center; color: #28a745;'>🟢 FINALIZATE</h2>", unsafe_allow_html=True)
        f_curat = {k: v for k, v in st.session_state.finalizate_date.items() if k.startswith(f"{nume_p}_")}
        prod_f_unice = sorted(list(set([k.split("_")[1] for k in f_curat.keys()])))
        for p_f in prod_f_unice:
            st.markdown(f'<div class="header-produs-verde">{p_f}</div>', unsafe_allow_html=True)
            for k, val in f_curat.items():
                info = k.split("_")
                if info[1] == p_f:
                    st.markdown('<div class="container-finalizat">', unsafe_allow_html=True)
                    cx, cu = st.columns([3, 1])
                    cx.markdown(f"<p class='text-client'>✅ {info[2]} : <span class='text-cantitate-fixa'>{val}</span> BUC</p>", unsafe_allow_html=True)
                    if cu.button("ANULEAZĂ", key=f"un_{k}"):
                        del st.session_state.finalizate_date[k]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Eroare: {e}")