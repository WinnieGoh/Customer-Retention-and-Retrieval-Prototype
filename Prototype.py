import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lead Profile Prototype", layout="wide")

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
BLUE = "#1F4B8E"
LIGHT_BLUE = "#5B87B5"
SIDEBAR_BG = "#CFDAEA"

TITLES = ["Mr", "Ms", "Mrs", "Dr", "Dato'", "Datin", "Tan Sri", "Puan", "Encik"]

# Mock insurance catalogue (replace with your own lists if needed)
PLANS = {
    "Life Insurance": ["Term Life", "Whole Life", "Endowment"],
    "Medical Insurance": ["Medical Basic", "Medical Standard", "Medical Premier"],
    "Critical Illness": ["CI Essential", "CI Plus"],
    "Investment-Linked": ["Growth Fund Plan", "Balanced Fund Plan"],
    "Personal Accident": ["PA Basic", "PA Plus"],
}

# Every field that is kept in the draft. Widget key = "f_" + field name.
LEAD_FIELDS = ["title", "first_name", "last_name", "contact", "email"]
INS_FIELDS = ["ins_type", "ins_plan", "policy_term", "beneficiary", "coverage", "premium"]
ALL_FIELDS = LEAD_FIELDS + INS_FIELDS
BLANK = {f: None for f in ALL_FIELDS}
for _f in ("first_name", "last_name", "contact", "email", "beneficiary"):
    BLANK[_f] = ""


# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    [data-testid="stApp"] {{ background: #F3F6FB; }}
    .block-container {{ max-width: 960px; background: white; border-radius: 20px;
                       box-shadow: 0 4px 24px rgba(31, 75, 142, .10);
                       padding: 2rem 2.5rem 2.5rem; margin-top: 1.5rem; margin-bottom: 2rem; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{ background-color: {SIDEBAR_BG}; }}
    [data-testid="stSidebarNav"] {{ display: none; }}
    [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"] {{
        padding-left: 1rem; padding-right: 1rem; }}
    .brand {{ font-size: 2rem; font-weight: 800; color: {BLUE}; padding: .5rem .5rem 1rem;
              margin-bottom: 1rem; border-bottom: 2px solid {BLUE}33; }}

    h1.page-title {{ text-align: center; color: {BLUE}; font-size: 2.6rem;
                    font-weight: 800; line-height: 1.2; margin: 0 0 .25rem 0; padding: .5rem 0 0 0; }}
    .section-title {{ color: #3B6AA0; font-size: 1.4rem; font-weight: 700; margin: 1rem 0 .25rem;
                      padding-bottom: .4rem; border-bottom: 2px solid #E1E9F5; }}
    .sub-title {{ text-align: center; color: #3B6AA0; font-weight: 600; margin-bottom: 1.5rem; }}

    /* field labels */
    [data-testid="stWidgetLabel"] p {{ color: {LIGHT_BLUE}; font-weight: 700; font-size: 1.05rem; }}

    /* rounded inputs */
    div[data-baseweb="input"], div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {{ border-radius: 14px !important; background: white !important; }}
    div[data-baseweb="input"], div[data-baseweb="select"] > div {{
        border: 1px solid #C5D3E8 !important; }}
    /* tighter, even spacing between form fields */
    [data-testid="stVerticalBlock"] {{ gap: .9rem; }}

    /* buttons: full width, rounded, dark blue */
    div[data-testid="stButton"],
    div[data-testid="stElementContainer"]:has(> div[data-testid="stButton"]) {{ width: 100% !important; }}
    .stButton > button {{ width: 100%; border-radius: 14px; font-weight: 700;
                         padding: .65rem 1rem; font-size: 1.05rem; }}
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {{
        background-color: {BLUE}; border-color: {BLUE}; color: white; }}
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {{
        border-color: {BLUE}; color: {BLUE}; }}

    /* sidebar nav buttons */
    [data-testid="stSidebar"] .stButton > button {{
        justify-content: flex-start; text-align: left; border: none; background: transparent;
        color: {BLUE}; font-size: 1.05rem; font-weight: 600; padding: .7rem 1rem;
        border-left: 4px solid transparent; border-radius: 10px; }}
    [data-testid="stSidebar"] .stButton > button > div,
    [data-testid="stSidebar"] .stButton > button p {{
        width: 100%; justify-content: flex-start; text-align: left; }}
    [data-testid="stSidebar"] .stButton > button:hover {{ background-color: #E3EAF6; }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{
        background-color: white; color: {BLUE}; border-left: 4px solid {BLUE}; }}

    /* stepper */
    .stepper {{ display: flex; align-items: center; margin: 1rem 0 1.5rem; }}
    .step {{ display: flex; align-items: center; gap: 10px; padding: 6px 20px;
             border-radius: 24px; border: 2px solid {BLUE}; color: {BLUE};
             font-weight: 700; white-space: nowrap; background: white; }}
    .step.active {{ background: {BLUE}; color: white; }}
    .step-line {{ flex: 1; height: 3px; background: {BLUE}; margin: 0 6px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Session state helpers
# ----------------------------------------------------------------------------
def init_state():
    ss = st.session_state
    if "leads" not in ss:
        # Mock data so the Lead Records table is not empty on first run
        ss.leads = [
            dict(BLANK, lead_id="L001", title="Ms", first_name="Aisyah", last_name="Rahman",
                 contact="+60123456789", email="aisyah@example.com", ins_type="Life Insurance",
                 ins_plan="Term Life", policy_term=20, beneficiary="Ahmad Rahman",
                 coverage=300000.0, premium=250.0),
            dict(BLANK, lead_id="L002", title="Mr", first_name="Daniel", last_name="Tan",
                 contact="+60198765432", email="daniel.tan@example.com",
                 ins_type="Medical Insurance", ins_plan="Medical Standard", policy_term=10,
                 beneficiary="Tan Mei Ling", coverage=500000.0, premium=180.0),
            dict(BLANK, lead_id="L003", title="Dr", first_name="Kumar", last_name="Raj",
                 contact="+60171234567", email="kumar.raj@example.com",
                 ins_type="Critical Illness", ins_plan="CI Plus", policy_term=25,
                 beneficiary="Priya Kumar", coverage=250000.0, premium=320.0),
        ]
    ss.setdefault("next_id", len(ss.leads) + 1)
    ss.setdefault("page", "Profile")
    ss.setdefault("step", 1)  # 1 = Lead Information, 2 = Insurance Details
    ss.setdefault("draft", dict(BLANK))
    ss.setdefault("editing_id", None)
    ss.setdefault("pending_delete", None)
    ss.setdefault("table_ver", 0)


def sync_draft_from_widgets():
    """Copy current widget values into the draft (runs at the top of every rerun)."""
    for f in ALL_FIELDS:
        key = f"f_{f}"
        if key in st.session_state:
            st.session_state.draft[f] = st.session_state[key]


def init_widget_keys(fields):
    """Make sure widgets start from the draft value when they (re)appear."""
    for f in fields:
        key = f"f_{f}"
        if key not in st.session_state:
            st.session_state[key] = st.session_state.draft[f]


def set_draft(data):
    """Replace the draft and reset all widget keys so they reload from it."""
    for f in ALL_FIELDS:
        st.session_state.pop(f"f_{f}", None)
    st.session_state.draft = {f: data.get(f, BLANK[f]) for f in ALL_FIELDS}


def go(page, step=None):
    st.session_state.page = page
    if step is not None:
        st.session_state.step = step


def lead_name(d):
    return " ".join(p for p in [d.get("title") or "", d["first_name"], d["last_name"]] if p).strip()


# ----------------------------------------------------------------------------
# UI building blocks
# ----------------------------------------------------------------------------
def page_title(text):
    st.markdown(f'<h1 class="page-title">{text}</h1>', unsafe_allow_html=True)


def stepper(step):
    a1 = "active" if step == 1 else ""
    a2 = "active" if step == 2 else ""
    st.markdown(
        f"""<div class="stepper">
              <div class="step {a1}">Lead Information</div>
              <div class="step-line"></div>
              <div class="step {a2}">Insurance Details</div>
            </div>""",
        unsafe_allow_html=True,
    )


def sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">Allianz</div>', unsafe_allow_html=True)
        for name in ("Profile", "Lead Records"):
            active = st.session_state.page == name
            if st.button(name, key=f"nav_{name}", **S,
                         type="primary" if active else "secondary"):
                go(name)
                st.rerun()


def stretch_kwargs():
    """Newer Streamlit uses width='stretch'; older uses use_container_width."""
    try:
        major, minor = (int(x) for x in st.__version__.split(".")[:2])
    except ValueError:
        major, minor = 1, 0
    if (major, minor) >= (1, 50):
        return {"width": "stretch"}
    return {"use_container_width": True}


S = stretch_kwargs()  # applied to every button so it fills its column


# ----------------------------------------------------------------------------
# Profile page - step 1: Lead Information
# ----------------------------------------------------------------------------
def lead_info_step():
    init_widget_keys(LEAD_FIELDS)
    st.markdown('<div class="section-title">General Information</div>', unsafe_allow_html=True)

    st.selectbox("Title", TITLES, index=None, placeholder="E.g: Mr, Ms, Dr....", key="f_title")

    c1, c2 = st.columns(2)
    c1.text_input("First Name", placeholder="Enter First Name", key="f_first_name")
    c2.text_input("Last Name", placeholder="Enter Last Name", key="f_last_name")

    st.text_input("Contact Number", placeholder="E.g: +60123456789", key="f_contact")
    st.text_input("Email", placeholder="E.g: natasha@gmail.com", key="f_email")

    st.write("")
    cont, _, _ = st.columns([1, 1, 2])
    if cont.button("Continue", type="primary", key="btn_continue", **S):
        sync_draft_from_widgets()
        d = st.session_state.draft
        errors = []
        if not d["first_name"].strip():
            errors.append("First name is required.")
        if not d["last_name"].strip():
            errors.append("Last name is required.")
        if not re.fullmatch(r"\+?\d{9,13}", d["contact"].replace(" ", "").replace("-", "")):
            errors.append("Enter a valid contact number, e.g. +60123456789.")
        if d["email"].strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", d["email"].strip()):
            errors.append("Enter a valid email address.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            go("Profile", 2)
            st.rerun()


# ----------------------------------------------------------------------------
# Profile page - step 2: Insurance Details (+ read-only general info on top)
# ----------------------------------------------------------------------------
def reset_plan():
    st.session_state["f_ins_plan"] = None


def insurance_step():
    init_widget_keys(INS_FIELDS)
    d = st.session_state.draft

    # --- General information: scrollable, read-only -------------------------
    st.markdown('<div class="section-title">General Information</div>', unsafe_allow_html=True)
    with st.container(height=230, border=True):
        st.text_input("Title", value=d["title"] or "-", disabled=True, key="ro_title")
        r1, r2 = st.columns(2)
        r1.text_input("First Name", value=d["first_name"], disabled=True, key="ro_first")
        r2.text_input("Last Name", value=d["last_name"], disabled=True, key="ro_last")
        st.text_input("Contact Number", value=d["contact"], disabled=True, key="ro_contact")
        st.text_input("Email", value=d["email"] or "-", disabled=True, key="ro_email")

    # --- Insurance details ---------------------------------------------------
    st.markdown('<div class="section-title">Insurance Details</div>', unsafe_allow_html=True)

    st.selectbox("Insurance Type", list(PLANS), index=None,
                 placeholder="E.g: Life Insurance, Medical Insurance....",
                 key="f_ins_type", on_change=reset_plan)

    ins_type = st.session_state.get("f_ins_type")
    plan_options = PLANS.get(ins_type, [])
    if st.session_state.get("f_ins_plan") not in plan_options:
        st.session_state["f_ins_plan"] = None
    st.selectbox("Insurance Plan", plan_options, index=None,
                 placeholder="Select an insurance type first" if not ins_type else "E.g: Term Life....",
                 disabled=not ins_type, key="f_ins_plan")

    st.number_input("Policy Term (years)", min_value=1, max_value=99, step=1, value=None,
                    placeholder="E.g: 20", key="f_policy_term")
    st.text_input("Beneficiary Name", placeholder="Enter Beneficiary Name", key="f_beneficiary")

    c1, c2 = st.columns(2)
    c1.number_input("Coverage Amount (RM)", min_value=0.0, step=1000.0, format="%.2f",
                    value=None, placeholder="E.g: 300000.00", key="f_coverage")
    c2.number_input("Premium Amount (RM)", min_value=0.0, step=10.0, format="%.2f",
                    value=None, placeholder="E.g: 250.00", key="f_premium")

    st.write("")
    b1, b2, _ = st.columns([1, 1, 2])
    if b1.button("Back", key="btn_back", **S):
        sync_draft_from_widgets()  # keep what was typed so far
        go("Profile", 1)
        st.rerun()

    if b2.button("Done", type="primary", key="btn_done", **S):
        sync_draft_from_widgets()
        d = st.session_state.draft
        if not d["ins_type"] or not d["ins_plan"]:
            st.error("Please select the insurance type and plan.")
        else:
            save_lead()
            go("Lead Records", 1)
            st.rerun()


def save_lead():
    ss = st.session_state
    record = dict(ss.draft)
    if ss.editing_id:  # update existing lead
        record["lead_id"] = ss.editing_id
        ss.leads = [record if l["lead_id"] == ss.editing_id else l for l in ss.leads]
        ss.flash = f"Lead {ss.editing_id} updated."
    else:  # create new lead
        record["lead_id"] = f"L{ss.next_id:03d}"
        ss.next_id += 1
        ss.leads.append(record)
        ss.flash = f"Lead {record['lead_id']} saved."
    ss.editing_id = None
    set_draft(BLANK)


def profile_page():
    page_title("Profile")
    ss = st.session_state

    if ss.editing_id:
        msg, btn = st.columns([4, 1])
        msg.info(f"Editing lead **{ss.editing_id}**. Changes are saved when you click Done.")
        if btn.button("Cancel edit", key="btn_cancel_edit", **S):
            ss.editing_id = None
            set_draft(BLANK)
            go("Lead Records", 1)
            st.rerun()

    stepper(ss.step)
    if ss.step == 1:
        lead_info_step()
    else:
        insurance_step()


# ----------------------------------------------------------------------------
# Lead Records page
# ----------------------------------------------------------------------------
def lead_records_page():
    ss = st.session_state
    page_title("Lead Records")
    st.markdown('<div class="sub-title">Choose one of the leads to retrieve details</div>',
                unsafe_allow_html=True)

    if "flash" in ss:
        st.success(ss.pop("flash"))

    if not ss.leads:
        st.info("No leads saved yet. Add one from the Profile page.")
        return

    df = pd.DataFrame(
        [
            {
                "LeadID": l["lead_id"],
                "Lead Name": lead_name(l),
                "Insurance Type": l["ins_type"],
                "Insurance Plan": l["ins_plan"],
                "Contact Number": l["contact"],
            }
            for l in ss.leads
        ]
    )

    event = st.dataframe(
        df,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"lead_table_{ss.table_ver}",
        **stretch_kwargs(),
    )
    rows = event.selection.rows
    selected_id = df.iloc[rows[0]]["LeadID"] if rows else None

    if selected_id:
        st.caption(f"Selected: **{selected_id}** - {df.iloc[rows[0]]['Lead Name']}")
    else:
        st.caption("Click a row to select a lead.")

    left, right, _ = st.columns([1, 1, 2])
    delete_clicked = left.button("Delete", type="primary", key="btn_delete", **S)
    retrieve_clicked = right.button("Retrieve", type="primary", key="btn_retrieve", **S)

    if delete_clicked:
        if selected_id:
            ss.pending_delete = selected_id
        else:
            st.warning("Please select a lead first.")

    if retrieve_clicked:
        if selected_id:
            lead = next(l for l in ss.leads if l["lead_id"] == selected_id)
            set_draft(lead)
            ss.editing_id = selected_id
            ss.pending_delete = None
            go("Profile", 1)
            st.rerun()
        else:
            st.warning("Please select a lead first.")

    # Delete confirmation
    if ss.pending_delete:
        st.warning(f"Delete lead **{ss.pending_delete}**? This cannot be undone.")
        y, n, _ = st.columns([1, 1, 3])
        if y.button("Yes, delete", type="primary", key="btn_confirm_delete", **S):
            ss.leads = [l for l in ss.leads if l["lead_id"] != ss.pending_delete]
            ss.flash = f"Lead {ss.pending_delete} deleted."
            ss.pending_delete = None
            ss.table_ver += 1  # clears the row selection
            st.rerun()
        if n.button("Cancel", key="btn_cancel_delete", **S):
            ss.pending_delete = None
            st.rerun()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
init_state()
sync_draft_from_widgets()
sidebar()

if st.session_state.page == "Profile":
    profile_page()
else:
    lead_records_page()