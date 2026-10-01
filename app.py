import streamlit as st
import pandas as pd
import plotly.express as px

from calculations import (
    calculate_recovery,
    calculate_compressor_duty,
    calculate_flare_reduction
)
from routes import evaluate_routes
from economics import calculate_economics

# 1. App Configuration
st.set_page_config(
    page_title="GASROUTE 2030",
    page_icon=":material/local_fire_department:",
    layout="wide"
)

# --- HEADER ---
st.title("GASROUTE 2030")
st.subheader("From flare data to gas-to-value decisions.")
st.caption("Strategic Screening MVP Prototype — Engineered for the NNPC / Renaissance / Total / Eni Joint Venture")
st.markdown("---")


# --- DATA STORAGE ENGINE ---
@st.cache_data
def load_base_database():
    try:
        df = pd.read_csv("data/facilities.csv")
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

base_df = load_base_database()


# --- SECTION: DATA REPOSITORY MANAGEMENT ---
st.markdown("### :material/database: Asset Repository Management")
col_upload, col_select = st.columns(2)

with col_upload:
    uploaded_file = st.file_uploader(
        "📥 Upload Custom Facility Dataset (CSV)", 
        type=["csv"],
        help="Upload an external asset roster matching our standard schema headers."
    )

db_df = base_df.copy()
if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        if not uploaded_df.empty and "facility_name" in uploaded_df.columns:
            db_df = pd.concat([uploaded_df, base_df], ignore_index=True).drop_duplicates(subset=["facility_name"])
            st.toast("Custom file parsed and appended successfully!", icon="✅")
        else:
            st.error("Uploaded CSV is missing the required 'facility_name' column header.")
    except Exception as e:
        st.error(f"Failed to read file: {e}")

# Clean up and strictly force types to strings/booleans
if not db_df.empty:
    if "facility_name" in db_df.columns:
        db_df["facility_name"] = db_df["facility_name"].astype(str).str.strip()
    if "asset_category" in db_df.columns:
        db_df["asset_category"] = db_df["asset_category"].astype(str).str.strip()


# --- SESSION STATE INITIALIZATION & RESET TRIGGER MECHANISM ---
if "active_preset" not in st.session_state:
    st.session_state["active_preset"] = "Manual Input Only"

# Fallback/Manual state default settings
default_vals = {
    "flare_in": 6.0, "ch4_in": 89, "dist_in": 80, "power_in": 2.0,
    "road_in": True, "reinj_in": False, "rich_in": False, "asset_cat": "Manual Sandbox Mode"
}

# Apply default values to session state if missing
for key, val in default_vals.items():
    if key not in st.session_state:
        st.session_state[key] = val


# --- CALLBACK ROUTINE: Triggered immediately when template dropdown shifts ---
def on_preset_change():
    chosen = st.session_state["preset_selector"]
    st.session_state["active_preset"] = chosen
    
    if chosen != "Manual Input Only" and not db_df.empty:
        matched = db_df[db_df["facility_name"] == chosen]
        if not matched.empty:
            row = matched.iloc[0]
            st.session_state["flare_in"] = float(row["flare_mmscfd"])
            st.session_state["ch4_in"] = int(row["ch4_percent"])
            st.session_state["dist_in"] = int(row["distance_km"])
            st.session_state["power_in"] = float(row["power_demand_mw"])
            st.session_state["road_in"] = str(row["road_access"]).strip().upper() == "TRUE"
            st.session_state["reinj_in"] = str(row["reinjection_suitable"]).strip().upper() == "TRUE"
            st.session_state["rich_in"] = str(row["gas_richness"]).strip().upper() == "TRUE"
            st.session_state["asset_cat"] = str(row["asset_category"])
    else:
        for key, val in default_vals.items():
            st.session_state[key] = val


with col_select:
    if not db_df.empty and "facility_name" in db_df.columns:
        preset_options = ["Manual Input Only"] + db_df["facility_name"].tolist()
        st.selectbox(
            "📂 Load Profile Template Target", 
            preset_options, 
            key="preset_selector", 
            on_change=on_preset_change
        )
    else:
        st.warning("Built-in database not detected. Running on local manual limits.")

st.markdown("---")


# --- SIDEBAR INTERACTIVE SIMULATION SIDE CONTROLS ---
st.sidebar.header(":material/tune: Simulation Controls")

flare = st.sidebar.number_input("Current Flare (MMSCFD)", min_value=0.0, key="flare_in")
gas_production = st.sidebar.number_input("Gas Production (MMSCFD)", min_value=0.0, value=flare * 3)
suction_pressure = st.sidebar.number_input("Suction Pressure (barg)", min_value=0.1, value=4.0)
discharge_pressure = st.sidebar.number_input("Required Discharge Pressure (barg)", min_value=1.0, value=20.0)
ch4 = st.sidebar.slider("CH4 Composition (%)", 50, 100, key="ch4_in")
distance = st.sidebar.number_input("Distance to Market (km)", min_value=0, key="dist_in")
power_demand = st.sidebar.number_input("Nearby Power Demand (MW)", min_value=0.0, key="power_in")
road_access = st.sidebar.checkbox("Road / Logistics Access Available", key="road_in")
reinjection = st.sidebar.checkbox("Reservoir Suitable for Reinjection", key="reinj_in")
gas_richness = st.sidebar.checkbox("Gas is Rich in NGL/LPG Components", key="rich_in")

asset_cat = st.session_state["asset_cat"]


# --- BACKEND PIPELINE PROCESSING ---
recovered_gas, residual_flare = calculate_recovery(flare)
flare_reduction = calculate_flare_reduction(recovered_gas, flare)
compressor_duty = calculate_compressor_duty(recovered_gas, suction_pressure, discharge_pressure)

facility_data = {
    "flare_mmscfd": flare, "ch4_percent": ch4, "distance_km": distance,
    "power_demand_mw": power_demand, "road_access": road_access,
    "reinjection_suitable": reinjection, "gas_richness": gas_richness
}
routes = evaluate_routes(facility_data)

route_table = pd.DataFrame([{"Route": r, "Screening Score": info["score"]} for r, info in routes.items()])
recommended_route = route_table.loc[route_table["Screening Score"].idxmax()]["Route"]
route_info = routes[recommended_route]

# Dynamic Scale CAPEX Engine
base_capex_per_mmscfd = {
    "CNG": 1_200_000, "LNG": 4_500_000, "POWER": 1_800_000, "LPG/NGL": 2_500_000, "REINJECTION": 1_400_000
}
total_project_capex = base_capex_per_mmscfd.get(recommended_route, 1_000_000) * flare
if distance <= 20 and recommended_route in ["CNG", "POWER"]:
    total_project_capex = total_project_capex * 0.8

# Split project allocations for options modeling
ren_solo_capex = total_project_capex
ren_solo_opex = ren_solo_capex * 0.08  # 8% maintenance and logistics footprint

# Option B: Third-Party Outsource Model (JV covers 20% tie-in, developer charges tariff)
ren_partner_capex = total_project_capex * 0.20

# --- RENAISSANCE JV STRATEGY & ESG FRAMEWORK DISPATCHER ---
eor_credit = 0.0
penalty_avoided = 0.0
strategic_reasoning_jv = ""
strategic_reasoning_outsource = ""
esg_impact = ""
boardroom_directive = ""

# Calculate Nigerian NUPRC / PIA Flare Penalty Avoided (\$2.00 per 1000 SCF)
penalty_avoided = recovered_gas * 1000 * 2.00 * 365

if recommended_route == "REINJECTION":
    gas_price = 0.0
    
    if reinjection: # EOR Project
        eor_oil_bbl_per_day = recovered_gas * 25 # Grounded conservative sweep efficiency
        eor_credit = eor_oil_bbl_per_day * 75 * 365
        strategic_reasoning_jv = f"The JV fully capitalizes the project via equity Cash Calls. The JV retains 100% of the **{eor_oil_bbl_per_day:.0f} bbl/day incremental oil sweep** value directly on its core books."
        strategic_reasoning_outsource = f"Outsource compression operations to a third-party midstream vendor via service contracts. Limits direct cash call exposure while capturing subsurface pressure benefits."
        esg_impact = "🌟 **AAA Rating:** Complete subsurface gas containment. Eradicates localized flares completely, preserving fragile swamp habitats."
        boardroom_directive = f"**PROCEED TO PRE-FEED:** Authorize reservoir injection engineering models for **{st.session_state['active_preset']}**. File the expenditure layout within the next NNPC (55%) / Renaissance (30%) JV budget optimization loop."
    else: # Pure Compliance Disposal
        strategic_reasoning_jv = f"The JV self-funds a dedicated disposal loop as a capital protection strategy to avoid federal field freeze mandates."
        strategic_reasoning_outsource = f"Lease modular skid units from third-party developers, mitigating **\${penalty_avoided/1_000_000:.2f}M in annual flaring fines** via a shared operating expense toll fee."
        esg_impact = "🟡 **AA Rating:** Eliminates soot fallout and community thermal pollution, but bypasses commercial hydrocarbon resource recycling."
        boardroom_directive = f"**COMPLIANCE INFRASTRUCTURE DISPATCH:** Deploy backup disposal skids at **{st.session_state['active_preset']}** to protect core oil streams. Finalize internal engineering reviews immediately."
elif asset_cat == "Non-AG_Forfeiture_Risk":
    gas_price = 7.5 if gas_richness else 4.0
    strategic_reasoning_jv = f"The JV coordinates full financing to build an internal midstream asset channel, capturing 100% of regional natural gas processing and monetization margins."
    strategic_reasoning_outsource = f"Assign the asset to an independent midstream developer under a BOOT concession. This satisfies NUPRC criteria, **blocking federal government NGFCP seizure** with zero capital strain on the JV."
    esg_impact = f"🌟 **AAA Rating:** Converts a structural waste liability into vital local economic solutions ({'LPG cooking gas cylinders' if gas_richness else 'clean virtual pipeline industrial energy'})."
    boardroom_directive = f"**ANTI-FORFEITURE DRILL:** Submit a formal intent framework to the NUPRC for **{st.session_state['active_preset']}** utilizing this modular **{recommended_route}** project profile to legally lock asset ownership."
else:
    # 🟢 FIXED INDENTATION IN THIS BLOCK BELOW
    gas_price = 7.5 if gas_richness else 4.0
    strategic_reasoning_jv = f"The JV finances the processing plant directly through proportional equity partner allocations, controlling downstream regional utility margins."
    strategic_reasoning_outsource = f"Onboard an external midstream developer to construct the facility under a long-term gas processing agreement, lowering direct JV capital exposure."
    
    if recommended_route == "POWER":
        esg_impact = "🌟 **AAA Rating [Social Impact Focus]:** Directly powers host communities, electrifying regional hospitals and micro-businesses. Drastically improves community relations and security footprint."
        boardroom_directive = f"**COMMUNITY ELECTRIFICATION DIRECTIVE:** Initiate a Gas-to-Wire technical study for {st.session_state['active_preset']}. Align with community stakeholders to secure corporate social responsibility (CSR) credits."
    else:
        esg_impact = "🌟 **AA Rating:** Substantially lowers net corporate carbon footprinting by converting methane waste streams into stable local industrial energy products."
        boardroom_directive = f"**COMMERCIALIZATION DISPATCH:** Advance {st.session_state['active_preset']} into formal midstream commercial review. Initiate third-party underwriting discussions."

# #️⃣ GROUNDED ENERGY FINANCE DISPATCH LOOP (Fines Avoided Are Separated From Direct Payback Cash Flow)
if recommended_route == "REINJECTION" and not reinjection:
    # Option A: Pure compliance play (Zero revenue, purely a cost load)
    econ_jv = {"annual_net_value": -ren_solo_opex, "payback_years": None}
    # Option B: Outsource compliance play (Fee model)
    econ_outsource = {"annual_net_value": -(total_project_capex * 0.15), "payback_years": None}
else:
    # Option A: JV 100% Self-Funded Payback (Driven exclusively by Gas revenue or EOR Oil sales)
    econ_jv = calculate_economics(
        recovered_gas_mmscfd=recovered_gas, residual_flare_mmscfd=residual_flare,
        gas_value_per_mmbtu=gas_price, capex=ren_solo_capex, annual_opex=ren_solo_opex,
        eor_oil_credit_annual=eor_credit, flare_penalty_avoided_annual=0
    )
    # Option B: Third-Party Outsource (Factoring a structural \$1.75/MMBtu midstream developer lease fee tariff)
    mmbtu_per_mmscfd_day = 365
    annual_processed_mmbtu = recovered_gas * mmbtu_per_mmscfd_day * 1000
    midstream_tariff_fee = annual_processed_mmbtu * 1.75
    ren_partner_opex = (total_project_capex * 0.05) + midstream_tariff_fee
    econ_outsource = calculate_economics(
        recovered_gas_mmscfd=recovered_gas, residual_flare_mmscfd=residual_flare,
        gas_value_per_mmbtu=gas_price, capex=ren_partner_capex, annual_opex=ren_partner_opex,
        eor_oil_credit_annual=eor_credit, flare_penalty_avoided_annual=0
    )

# ==========================================
# SECTION 1: FACILITY PROFILE
# ==========================================
st.header(":material/fact_check: SECTION 1: FACILITY PROFILE", divider="blue")
with st.container(border=True):
    prof_col1, prof_col2, prof_col3 = st.columns(3)
    with prof_col1:
        st.markdown("### :material/propane_tank: Gas & Flare")
        st.write(f"**Gas Production:** `{gas_production:.1f} MMSCFD`")
        st.write(f"**Flare Volume:** `{flare:.1f} MMSCFD`")
    with prof_col2:
        st.markdown("### :material/settings: Pressure & Fluid")
        st.write(f"**Suction Pressure:** `{suction_pressure:.1f} barg`")
        st.write(f"**Discharge Pressure:** `{discharge_pressure:.1f} barg`")
        st.write(f"**Composition (CH4):** `{ch4}%`")
        st.write(f"**Gas Richness (NGLs):** {'[Yes]' if gas_richness else '[No]'}")
    with prof_col3:
        st.markdown("### :material/map: Market & Access")
        st.write(f"**Distance to Market:** `{distance} km`")
        st.write(f"**Road Logistics:** {'[Available]' if road_access else '[None]'}")
        st.write(f"**Nearby Power Demand:** `{power_demand:.1f} MW`")
        st.write(f"**Reservoir Reinjection:** {'[Suitable]' if reinjection else '[Unsuitable]'}")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# SECTION 2: ROUTE ENGINE
# ==========================================
st.header(":material/analytics: SECTION 2: ROUTE EVALUATION ENGINE", divider="blue")
st.markdown("Evaluating cross-functional technical viability matrix for asset alignment:")
fig = px.bar(
    route_table, x="Route", y="Screening Score", range_y=[0, 100],
    title="Comparative Feasibility Score Mapping",
    color="Screening Score",
    color_continuous_scale=["#FF4B4B", "#F1C40F", "#2ECC71"],
    text="Screening Score"
)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#31333F",
    xaxis=dict(showgrid=False, title="Monetization Strategy"),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", title="Feasibility Score (%)")
)
fig.update_traces(textposition="outside", cliponaxis=False)
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# ==========================================
# SECTION 3: BOARDROOM OPTIONS & ECONOMIC METRICS
# ==========================================
st.header(":material/assignment_turned_in: SECTION 3: BOARDROOM OPTIONS & ECONOMIC METRICS", divider="blue")
st.success(f"### :material/emoji_events: Recommended Strategy Pathway: **{recommended_route}**")

col_infra, col_esg = st.columns(2)
with col_infra:
    st.markdown("#### :material/precision_manufacturing: Required Equipment Skids:")
    st.write(" → " + " | ".join(route_info["infrastructure"]))
with col_esg:
    st.markdown("#### :material/eco: ESG Governance & Corporate Image Metric:")
    st.write(esg_impact)

st.markdown("<br>", unsafe_allow_html=True)

# #️⃣ Comparative Options Layout Grid
opt_col1, opt_col2 = st.columns(2)
with opt_col1:
    with st.container(border=True):
        st.markdown("### 🏛️ OPTION A: JV Cash Call Funded (100% Internal)")
        st.write(strategic_reasoning_jv)
        st.markdown("---")
        st.markdown("**Proportional JV Partner CAPEX Equity Allocation:**")
        st.write(f"🔹 **NNPC Share (55%):** `\${(total_project_capex * 0.55)/1_000_000:.2f}M`")
        st.write(f"🔹 **Renaissance Share (30%):** `\${(total_project_capex * 0.30)/1_000_000:.2f}M` *(Consortium Shared)*")
        st.write(f"🔹 **TotalEnergies Share (10%):** `\${(total_project_capex * 0.10)/1_000_000:.2f}M`")
        st.write(f"🔹 **Eni Share (5%):** `\${(total_project_capex * 0.05)/1_000_000:.2f}M`")
        st.markdown("---")
        m1, m2 = st.columns(2)
        m1.metric("Total JV CAPEX", f"\${total_project_capex/1_000_000:.1f}M")
        m2.metric("Total Annual OPEX", f"\${ren_solo_opex/1_000_000:.2f}M")
        st.metric("Total JV Net Value (Annual Project Return)", f"\${econ_jv['annual_net_value']/1_000_000:.1f}M")
        st.markdown("---")
        if econ_jv["payback_years"] is not None:
            if econ_jv["payback_years"] < 1.0:
                months = econ_jv["payback_years"] * 12
                st.metric("🎯 Full Equity Payback Period", f"{months:.1f} Months")
            else:
                st.metric("🎯 Full Equity Payback Period", f"{econ_jv['payback_years']:.1f} Years")
        else:
            st.metric("🎯 Full Equity Payback Period", "N/A (Regulatory Compliance Cost Play)", delta=f"Avoids \${penalty_avoided/1_000_000:.1f}M/Yr Fines", delta_color="normal")

with opt_col2:
    with st.container(border=True):
        st.markdown("### 🤝 OPTION B: Third-Party Midstream Outsource")
        st.write(strategic_reasoning_outsource)
        st.markdown("---")
        st.markdown("**Mitigated JV Tie-In Lease Share Allocations:**")
        st.write(f"🔹 **Total JV Connection CAPEX (20%):** `\${(total_project_capex * 0.20)/1_000_000:.2f}M`")
        st.write(f"🔹 **NNPC Share (55% of Loop):** `\${(total_project_capex * 0.20 * 0.55)/1_000_000:.2f}M`")
        st.write(f"🔹 **Renaissance Share (30% of Loop):** `\${(total_project_capex * 0.20 * 0.30)/1_000_000:.2f}M`")
        st.write(f"🔹 **Total (10%) & Eni (5%) Loop Shares:** `\${(total_project_capex * 0.20 * 0.15)/1_000_000:.2f}M`")
        st.markdown("---")
        m1, m2 = st.columns(2)
        m1.metric("Third-Party BOOT CAPEX", f"\${(total_project_capex * 0.80)/1_000_000:.1f}M")
        m2.metric("JV Direct CAPEX Exposure", f"\${(total_project_capex * 0.20)/1_000_000:.1f}M")
        st.metric("Outsourced Net Value (Annual Project Return)", f"\${econ_outsource['annual_net_value']/1_000_000:.1f}M")
        st.markdown("---")
        if econ_outsource["payback_years"] is not None:
            if econ_outsource["payback_years"] < 1.0:
                months = econ_outsource["payback_years"] * 12
                st.metric("🎯 Outsourced Simple Payback", f"{months:.1f} Months", delta="Capital Risks Diverted")
            else:
                st.metric("🎯 Outsourced Simple Payback", f"{econ_outsource['payback_years']:.1f} Years", delta="Capital Risks Diverted")
        else:
            st.metric("🎯 Outsourced Simple Payback", "N/A (Regulatory Compliance Cost Play)", delta="Partner Insulated", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# #️⃣ Full-width container for executive actions
with st.container(border=True):
    st.markdown("### :material/gavel: Boardroom Action Directive")
    st.warning(boardroom_directive)

st.markdown("---")

with st.expander(":material/shield: View MVP Operating Philosophy & Safeguards"):
    st.write("""
    * **Normal Operation:** Recovery → Conditioning → Metering → Selected Offtake
    * **Compressor Trip:** Automatic Isolation → Flare Fallback → Alarm → Controlled Restart
    * **Recovery Capacity Saturated:** Cap Recovery → Excess Gas to Safety Flare
    * **Upstream Pressure Constraint:** Reduce Recovery Rate → Protect Oil Production
    """)
