"""DewaterIQ | Industrial process intelligence demonstration.

A read-only, simulation-first operations console. Neither this UI nor its AI
assistant issues physical equipment commands. No real sensor data are used.
"""
import json
import os
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dewateriq_backend.sim_runner import SCENARIOS, generate_and_store
from dewateriq_backend.historian import runs, get_run, get_events, add_note, get_notes
from dewateriq_backend.analytics import summary, similar_runs, offline_explanation
from dewateriq_backend.nebius import analyze

st.set_page_config(
    page_title="DewaterIQ | Solids Control Command Center",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A restrained industrial SCADA-inspired visual system; all process thresholds
# remain descriptive observations, never OEM-rated alarms or control limits.
BG = "#091720"
SURFACE = "#102633"
LINE = "#31505A"
TEXT = "#E9F4FA"
MUTED = "#91A9BA"
TEAL = "#41CFBA"
BLUE = "#8EB6E0"
AMBER = "#F3BE62"
RED = "#FF7383"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
  font-family:'DM Sans',sans-serif;
}
.stApp {background:#091720;color:#E9F4FA;}
.block-container {max-width:1560px;padding-top:1.0rem;padding-bottom:2.5rem;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0D2330 0%,#071720 100%);border-right:1px solid #23394B;}
[data-testid="stSidebar"] .block-container {padding-top:1.2rem;}
h1,h2,h3,[data-testid="stMetricLabel"] {font-family:'Space Grotesk','DM Sans',sans-serif;letter-spacing:-.02em;}
h1,h2,h3 {color:#ECF8FC;}
h1{font-size:2rem !important;}h2{font-size:1.3rem !important;}h3{font-size:1.02rem !important;}
p,small {color:#B9CCD8;}
[data-testid="stMetric"] {background:linear-gradient(170deg,#132535,#10202F);border:1px solid #254359;
 border-radius:15px;padding:16px 18px;min-height:118px;box-shadow:0 6px 18px rgba(0,0,0,.10);}
[data-testid="stMetricLabel"] {font-size:.82rem;color:#AFC5D4;}
[data-testid="stMetricValue"] {font-family:'Space Grotesk',sans-serif;font-size:1.66rem;color:#F3FAFF;}
[data-testid="stMetricDelta"] {font-size:.78rem;}
[data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#23394B;}
[data-baseweb="tab-list"] {gap:13px;}
button[data-baseweb="tab"]{border-radius:9px 9px 0 0;}
button[data-baseweb="tab"][aria-selected="true"]{color:#40D7D1;border-bottom-color:#40D7D1;}
.stButton>button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"]{
 background:linear-gradient(110deg,#1AAFAF,#25C9C0);border:0;color:#05242A;
 font-weight:800;border-radius:10px;}
.stButton>button:not([kind="primary"]),.stDownloadButton button {border-color:#2F5264;border-radius:10px;}
[data-testid="stAlert"]{border-radius:10px;}
[data-testid="stExpander"] {border:1px solid #244052;border-radius:12px;}
[data-testid="stDataFrame"] {border:1px solid #23394B;border-radius:10px;}
hr{border-color:#23394B;}
.diq-hero {padding:25px 28px 22px;border-radius:18px;border:1px solid #4C7273;
 background:radial-gradient(circle at 88% 9%, rgba(240,181,86,.13), transparent 36%),
 linear-gradient(125deg,#163747,#0A1E2A 74%);margin:6px 0 14px;}
.diq-eyebrow{font-size:.70rem;text-transform:uppercase;letter-spacing:2.2px;font-weight:700;color:#7CE6DC;margin-bottom:8px;}
.diq-title{font:700 2.35rem/1.07 'Space Grotesk',sans-serif;color:#F2FCFF;margin:0;letter-spacing:-.055em;}
.diq-sub{color:#B3C9D5;font-size:.94rem;margin-top:10px;max-width:950px;line-height:1.6;}
.diq-badges{display:flex;gap:9px;flex-wrap:wrap;margin-top:15px;}
.diq-badge{background:#102C37;border:1px solid #305D68;border-radius:999px;padding:5px 11px;color:#A8DEE3;font-size:.71rem;font-weight:700;letter-spacing:.04em;}
.diq-badge.warn{background:#302719;border-color:#69532A;color:#FFD18E;}
.diq-section{font:700 1.05rem 'Space Grotesk',sans-serif;color:#EAF6FB;margin:7px 0 8px;}
.diq-muted{font-size:.81rem;color:#9CB6C5;}
.diq-card {border:1px solid #294455;background:linear-gradient(160deg,#122839,#0E1D2B);
 border-radius:13px;padding:17px 18px;margin:6px 0 12px;}
.diq-card-title{font:700 .85rem 'Space Grotesk',sans-serif;color:#DCEEF7;letter-spacing:.02em;}
.diq-card-body{font-size:.81rem;color:#AFC7D2;margin-top:8px;line-height:1.65;}
.diq-status{display:inline-block;padding:5px 11px;border:1px solid #305D67;border-radius:999px;
 background:#10363C;color:#8EF3E2;font-size:.75rem;font-weight:700;}
.diq-status.amber{background:#372C1C;border-color:#7F5B2D;color:#FFCE8C;}
.diq-status.red{background:#36202A;border-color:#7A3948;color:#FFA9B6;}
.diq-footer{border-top:1px solid #253A4A;margin-top:22px;padding:13px 4px;color:#91A9BA;font-size:.76rem;line-height:1.8;}
@media(max-width:750px){.diq-hero{padding:20px}.diq-title{font-size:1.8rem}}

/* Field skid process mimic: explicit virtual process, not a real plant control panel */
.diq-flow-box {background:linear-gradient(150deg,#102C39,#102431);border:1px solid #31515B;
  border-radius:12px;min-height:127px;padding:14px 14px 12px;flex:1 1 155px;min-width:135px;}
.diq-flow-box.secondary {background:#102536;border-color:#355369;}
.diq-flow-top{color:#8BA9B8;letter-spacing:1.6px;font-size:.64rem;font-weight:800;text-transform:uppercase;}
.diq-flow-name{font:700 .94rem 'Space Grotesk',sans-serif;color:#ECF8F5;margin:8px 0 4px;}
.diq-flow-reading{font:700 1.12rem 'Space Grotesk',sans-serif;color:#59E0C8;margin-top:6px;}
.diq-flow-meta{color:#A9C0CE;font-size:.72rem;margin-top:5px;line-height:1.4;}
.diq-flow-arrow{color:#EFC176;font-size:1.4rem;font-weight:900;align-self:center;margin:0 3px;}
.diq-route{display:flex;align-items:stretch;gap:4px;flex-wrap:nowrap;margin:10px 0 12px;}
.diq-depart{display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;}
.diq-depart .diq-flow-box{flex:1;min-height:90px;}
.diq-context{background:#182C34;border:1px solid #526044;border-left:4px solid #E7B45C;
 border-radius:10px;padding:12px 16px;color:#C7D6D9;font-size:.82rem;line-height:1.6;margin:10px 0 17px;}
.diq-smallprint{font-size:.72rem;color:#8FA7AF;margin-top:6px;}
.diq-ref-row{display:grid;grid-template-columns:repeat(3, minmax(0,1fr));gap:10px;margin:10px 0 18px;}
.diq-ref{background:#102332;border:1px solid #304B54;border-radius:12px;padding:12px 15px;}
.diq-ref-label{color:#A4C2C9;font-size:.70rem;letter-spacing:.07em;text-transform:uppercase;}
.diq-ref-value{font:700 1.28rem 'Space Grotesk',sans-serif;color:#F3CC83;margin-top:5px;}
@media(max-width:880px){.diq-route{flex-wrap:wrap}.diq-flow-arrow{transform:rotate(90deg);margin:auto 4px}.diq-ref-row{grid-template-columns:1fr}}

</style>
""", unsafe_allow_html=True)


def nice(text):
    return str(text).replace("_", " ").replace("-", " ").title()


def tag(text, tone=""):
    return f'<span class="diq-status {tone}">{escape(str(text))}</span>'


def graph(df, series, title, colors=None, height=272, reference=None):
    """Shared styling for all telemetry charts; no arbitrary alarm bands."""
    fig = go.Figure()
    for idx, key in enumerate(series):
        if key not in df:
            continue
        fig.add_trace(go.Scatter(
            x=df.index, y=df[key], mode="lines", name=key,
            line=dict(color=(colors or [TEAL, BLUE, AMBER, RED])[idx % len(colors or [TEAL, BLUE, AMBER, RED])], width=2.7),
            hovertemplate="t=%{x}s · %{y:.2f}<extra>" + escape(key) + "</extra>",
        ))
    if reference is not None:
        fig.add_hline(y=reference, line_color=AMBER, line_dash="dot", opacity=.75,
                      annotation_text="Virtual setpoint", annotation_font_color=AMBER)
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="DM Sans"), x=.02, y=.95),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font=dict(color=MUTED, size=10),
        height=height, margin=dict(l=22, r=20, t=49, b=25),
        legend=dict(orientation="h", y=-.19, x=0, font=dict(size=10)),
        hovermode="x unified", hoverlabel=dict(bgcolor="#132B3C", font_color=TEXT),
        xaxis=dict(title="Simulation time (s)", gridcolor="#213748", zeroline=False, showline=False),
        yaxis=dict(gridcolor="#213748", zeroline=False, showline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False, "responsive":True})




def render_skid_flow(last, skid_reference):
    """Conceptual separation diagram sourced from the current *synthetic* record."""
    hp = last["hydraulic_process"]
    mach = last["machine"]
    chem = last["mud_chemistry"]
    out = last["output"]
    def block(num, title, reading, info, secondary=False):
        sec = ' secondary' if secondary else ''
        return (f'<div class="diq-flow-box{sec}">'
                f'<div class="diq-flow-top">{escape(num)}</div>'
                f'<div class="diq-flow-name">{escape(title)}</div>'
                f'<div class="diq-flow-reading">{escape(str(reading))}</div>'
                f'<div class="diq-flow-meta">{escape(info)}</div></div>')
    source = block("01 / FLUID STORAGE", "Source pit", f'{hp["source_pit_level_percent"]:.1f}%',
                   f'{hp["source_pit"]} · simulated inventory')
    pump = block("02 / TRANSFER", "Feed pump", f'{mach["simulated_feed_pump_rpm"]:,.0f} RPM',
                 f'{hp["actual_flow_gpm"]:.0f} GPM · virtual valve {hp["virtual_valve_position_percent"]:.0f}%')
    polymer = block("03 / CONDITIONING", "Polymer injection", f'{chem["simulated_polymer_dose_percent"]:.1f}%',
                    'Simulator index · NOT a chemical dose recipe',True)
    centrifuge = block("04 / SEPARATION", "Decanter centrifuge", f'{mach["simulated_actual_centrifuge_rpm"]:,.0f} RPM',
                       f'{mach["torque_percent"]:.0f}% torque · {mach["motor_current_a"]:.1f} A')
    effluent = block("05A / LIQUID ROUTE", "Destination pit / effluent", f'{hp["destination_pit_level_percent"]:.1f}%',
                     f'{hp["destination_pit"]} · downstream effluent quality not measured',True)
    solids = block("05B / SOLIDS ROUTE", "Separated solids", f'{out["simulated_solids_removal_percent"]:.1f}%',
                   f'Simulated removal metric · cut: {out["cut_quality"]}',True)
    flow = ('<div class="diq-route">' +
            '<span class="diq-flow-arrow">→</span>'.join([source,pump,polymer,centrifuge])+
            '</div><div class="diq-depart">' + effluent + solids + '</div>')
    st.markdown(flow, unsafe_allow_html=True)
    st.caption("Illustrative process topology only. All readouts come from synthetic simulator records. "
               "No physical polymer pump, liquid-quality sensor or solids discharge instrument is connected.")
    if skid_reference.startswith('Predator'):
        reference = 'Predator 2072 · 530 GPM published capacity'
    elif skid_reference.startswith('Mammoth'):
        reference = 'Mammoth 2276 · 660 GPM published capacity'
    else:
        reference = 'Generic synthetic skid · no assigned equipment make/model'
    st.markdown(f'<div class="diq-context"><b>EQUIPMENT REFERENCE · {escape(reference)}</b><br>'
                'Public OEM product capacities are for descriptive comparison only. This simulator does not ' 
                'implement Kayden machine curves, certified limits, or real skid control. '
                'The pictured workflow is a single-centrifuge teaching example; dual-skid support is conceptual.</div>',
                unsafe_allow_html=True)

def display_analysis(selected, data, matches):
    """Only calls Nebius on button press, never on page load or rerun."""
    st.markdown('''<div class="diq-section">NVIDIA Nemotron · AI Advisory</div>
    <div class="diq-muted">Evidence-grounded hypotheses from synthetic telemetry. No machine commands.</div>''', unsafe_allow_html=True)
    key_present=bool(os.getenv("NEBIUS_API_KEY") or os.getenv("NEBIUS_TOKEN_FACTORY_KEY"))
    if key_present:
        st.markdown(tag("API key configured · call on demand"), unsafe_allow_html=True)
    else:
        st.markdown(tag("Offline rules available", "amber"), unsafe_allow_html=True)
    st.write("")
    if st.button("✦ Analyze current run with Nemotron", key=f"analyze_{selected}", type="primary", use_container_width=True):
        with st.spinner("Analyzing simulated readings · one explicit Nebius request"):
            st.session_state[f"ai-{selected}"] = analyze(data, matches)
    result=st.session_state.get(f"ai-{selected}")
    if result:
        state=result.get("status")
        if state == "live_nebius":
            st.success("LIVE NEBIUS INFERENCE · NVIDIA NEMOTRON")
        elif state == "offline_api_unavailable":
            st.warning("Nebius unavailable · displaying offline rules, not a live response")
        else:
            st.info("Offline rule-based advisory · no live model call")
        st.caption(f"Status: {state} · Model: {result.get('model') or 'not called'}")
        st.markdown(result.get("text", "No response returned."))
        st.caption(result.get("note", ""))
    else:
        st.markdown('''<div class="diq-card"><div class="diq-card-title">Ready for your diagnostic briefing</div>
        <div class="diq-card-body">Run Nemotron to interpret flow, load, vibration and pit-level patterns.
        Your last AI response is retained when navigating tabs. The model is never called automatically.</div></div>''', unsafe_allow_html=True)
    with st.expander("Show deterministic baseline & comparable runs"):
        st.caption("Baseline generated locally, without invoking an AI model.")
        st.write(offline_explanation(data, matches))
        if matches:
            st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)
        else:
            st.caption("No comparable synthetic runs for this selection.")


with st.sidebar:
    st.markdown('''<div class="diq-eyebrow">DEWATERIQ / CONTROL DESK</div>
    <div style="font:700 1.4rem 'Space Grotesk',sans-serif;color:#F4FCFF">◈ Operations</div>
    <div class="diq-muted">Simulation workspace · v1.0</div>''', unsafe_allow_html=True)
    st.divider()
    st.markdown("**CREATE SIMULATION**")
    scenario=st.selectbox("Operating scenario", SCENARIOS, index=1,
                          format_func=nice, help="All scenarios generate simulated values only.")
    samples=st.slider("Duration · samples", 30, 240, 90, 10)
    seed=st.number_input("Replay seed", min_value=0, max_value=100000, value=7, step=1)
    if st.button("▶ Run simulation", type="primary", use_container_width=True):
        try:
            run_id, n=generate_and_store(scenario, samples, int(seed))
            st.session_state.selected_run=run_id
            st.success(f"Stored {n} synthetic readings")
        except Exception as exc:
            st.error(f"Simulation failed ({type(exc).__name__}): {exc}")
    if st.button("＋ Seed all 13 scenarios", use_container_width=True):
        with st.spinner("Compiling simulator and importing synthetic scenarios"):
            try:
                for name in SCENARIOS:
                    generate_and_store(name, 90, seed=int(seed))
                st.success("All scenarios historized")
            except Exception as exc:
                st.error(f"Unable to seed all scenarios: {type(exc).__name__}: {exc}")
    st.divider()
    st.markdown("**SKID REFERENCE (PUBLIC SPECIFICATIONS)**")
    skid_reference = st.selectbox(
        "Illustrative equipment reference",
        ["Generic simulation · no assigned OEM", "Predator 2072 · published 530 GPM", "Mammoth 2276 · published 660 GPM"],
        help="Reference labels only. This simulator is NOT a calibrated Kayden machine model."
    )
    st.caption("Published model names/capacities are comparison context, not operating limits. No OEM data link.")
    st.divider()
    st.markdown("**SYSTEM CONNECTIONS**")
    st.markdown(tag("LOCAL C99 + SQLITE", ""), unsafe_allow_html=True)
    st.write("")
    if os.getenv("NEBIUS_API_KEY") or os.getenv("NEBIUS_TOKEN_FACTORY_KEY"):
        st.markdown(tag("NEBIUS KEY DETECTED"), unsafe_allow_html=True)
    else:
        st.markdown(tag("NEBIUS OFFLINE", "amber"), unsafe_allow_html=True)
    st.caption("Key detection is not proof of a successful API call. See the advisory result for live verification.")
    st.divider()
    st.caption("SYNTHETIC SIGNALS ONLY")
    st.caption("No live PLC, sensors, VFD, valves, pumps, or chemical dosing interface.")

st.markdown('''<div class="diq-hero">
  <div class="diq-eyebrow">SOLIDS CONTROL / DEWATERING SKID / DIGITAL PROCESS TWIN</div>
  <div class="diq-title">DewaterIQ <span style="color:#F0C27C">/</span> Solids Control</div>
  <div class="diq-sub">Oilfield fluid-processing command center: simulated feed-pump transfer,
  polymer-conditioning context, decanter centrifuge separation, pit balance and AI-guided diagnostics.
  Workflow aligned with publicly described Kayden-style dewatering skids.</div>
  <div class="diq-badges"><span class="diq-badge">C99 TELEMETRY</span>
  <span class="diq-badge">DECANTER CENTRIFUGE</span><span class="diq-badge">POLYMER INJECTION</span>
  <span class="diq-badge">NVIDIA NEMOTRON / NEBIUS</span>
  <span class="diq-badge warn">SIMULATION · NOT OEM SOFTWARE</span></div>
</div>''', unsafe_allow_html=True)

catalog=runs()
if not catalog:
    st.markdown('''<div class="diq-card"><div class="diq-card-title">No historian runs yet</div>
    <div class="diq-card-body">Select an operating scenario in the left control desk and press
    <b>Run simulation</b> to begin. The dashboard works offline, without any industrial equipment.</div></div>''',
    unsafe_allow_html=True)
    st.stop()

ids=[x["run_id"] for x in catalog]
initial=st.session_state.get("selected_run")
col_sel, col_stat=st.columns([3.3,1.1], vertical_alignment="bottom")
with col_sel:
    selected=st.selectbox("ACTIVE HISTORIAN RUN", ids,
                          index=ids.index(initial) if initial in ids else 0,
                          format_func=lambda r: nice(r.replace("synthetic-", "")))
with col_stat:
    if st.button("↻ Refresh runs", use_container_width=True):
        st.rerun()

data=get_run(selected)
if not data:
    st.warning("No telemetry available for the selected historian run.")
    st.stop()
s=summary(data)
last=data[-1]
faults=get_events(selected)
selected_scenario=nice(s["scenario"])
st.markdown(f'<div class="diq-muted" style="padding:3px 0 16px">'
            f'RUN / {escape(selected)} &nbsp;&nbsp;·&nbsp;&nbsp; '
            f'{escape(selected_scenario)} &nbsp;&nbsp;·&nbsp;&nbsp; '
            f'{s["samples"]} synthetic samples &nbsp;&nbsp;·&nbsp;&nbsp; '
            f'{escape(nice(s["operating_mode"]))}</div>', unsafe_allow_html=True)

k1,k2,k3,k4,k5=st.columns(5)
k1.metric("Centrifuge speed", f'{s["latest_rpm"]:,.0f} RPM')
k2.metric("Process throughput", f'{s["latest_flow_gpm"]:,.1f} GPM',
          f'{s["flow_delta_gpm"]:+.1f} GPM vs first sample', delta_color="off")
k3.metric("Motor current", f'{s["latest_current_a"]:.1f} A',
          f'{s["current_delta_a"]:+.1f} A vs first sample', delta_color="off")
k4.metric("Solids removal · sim", f'{last["output"]["simulated_solids_removal_percent"]:.1f}%')
k5.metric("Scenario flag", "FLAGGED" if s["any_fault"] else "NONE",
          help="Synthetic scenario fault, not a validated OEM alarm")

if s["any_fault"]:
    st.markdown('''<div class="diq-card" style="border-color:#8D5661;background:#231B2A">
    <div style="color:#FFB6C0;font-size:.82rem;font-weight:700">◆ SYNTHETIC SCENARIO FLAG</div>
    <div class="diq-card-body">A generated fault label occurs in this simulation.
    It is not a verified alarm or an equipment safety decision.</div></div>''', unsafe_allow_html=True)

rows=[]
for r in data:
    m=r["machine"]
    h=r["hydraulic_process"]
    c=r["mud_chemistry"]
    o=r["output"]
    rows.append({
        "t (s)":r["timestamp_s"],
        "Centrifuge RPM":m["simulated_actual_centrifuge_rpm"],
        "Virtual RPM setpoint":m["commanded_virtual_centrifuge_rpm"],
        "Feed-pump RPM":m["simulated_feed_pump_rpm"],
        "Flow (GPM)":h["actual_flow_gpm"],
        "Virtual flow setpoint":h["commanded_virtual_flow_gpm"],
        "Current (A)":m["motor_current_a"],
        "Torque (%)":m["torque_percent"],
        "Vibration (mm/s)":m["vibration_mm_s"],
        "Bearing temp (°C)":m["bearing_temperature_c"],
        "Source pit (%)":h["source_pit_level_percent"],
        "Destination pit (%)":h["destination_pit_level_percent"],
        "Virtual VFD (Hz)":m["simulated_vfd_frequency_hz"],
        "pH":c["ph"],
        "Mud weight (ppg)":c["mud_weight_ppg"],
        "LGS (%)":c["lgs_percent"],
        "HGS (%)":c["hgs_percent"],
        "Solids removal (%)":o["simulated_solids_removal_percent"],
        "Quality index":o["process_quality_index"],
        "Polymer index (%)":c["simulated_polymer_dose_percent"],
        "Chemical index (%)":c["simulated_chemical_dose_percent"],
    })
df=pd.DataFrame(rows).set_index("t (s)")
other_records=[get_run(x["run_id"]) for x in catalog if x["run_id"]!=selected]
matches=similar_runs(data,other_records)

st.write("")
t_overview,t_machine,t_quality,t_logs,t_raw=st.tabs([
    "◈ Dewatering skid", "◉ Centrifuge & drives", "◐ Fluids & polymer", "≡ Events & notes", "⇩ Data & evidence"
])
with t_overview:
    st.markdown('<div class="diq-section">Dewatering skid · simulated material flow</div>', unsafe_allow_html=True)
    render_skid_flow(last, skid_reference)
    left,right=st.columns([1.42,1],gap="large")
    with left:
        st.markdown('<div class="diq-section">Feed flow & pit inventory</div>',unsafe_allow_html=True)
        graph(df,["Flow (GPM)","Virtual flow setpoint"],"Feed flow · process vs virtual setpoint",[TEAL,AMBER],295)
        graph(df,["Source pit (%)","Destination pit (%)"],"Source / effluent destination pit levels",[BLUE,TEAL],252)
    with right:
        display_analysis(selected,data,matches)
    st.markdown('<div class="diq-section">Separation & condition snapshot</div>',unsafe_allow_html=True)
    x1,x2,x3,x4=st.columns(4)
    x1.metric("Bearing temperature",f'{last["machine"]["bearing_temperature_c"]:.1f} °C')
    x2.metric("Vibration",f'{last["machine"]["vibration_mm_s"]:.2f} mm/s')
    x3.metric("Cut quality · simulated",nice(s["latest_cut"]))
    x4.metric("Events in run",str(len(faults)))

with t_machine:
    st.markdown('<div class="diq-section">Decanter centrifuge, feed pump & VFD · synthetic</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        graph(df,["Centrifuge RPM","Virtual RPM setpoint"],"Centrifuge speed tracking",[TEAL,AMBER],310)
        graph(df,["Current (A)"],"Motor current",[BLUE],270)
        graph(df,["Virtual VFD (Hz)"],"Virtual VFD frequency",[TEAL],255)
        graph(df,["Feed-pump RPM"],"Feed pump RPM",[BLUE],255)
    with b:
        graph(df,["Torque (%)"],"Drive torque",[AMBER],310)
        graph(df,["Vibration (mm/s)"],"Bearing vibration",[BLUE],270)
        graph(df,["Bearing temp (°C)"],"Bearing temperature",[TEAL],255)
    st.caption("Time-series values are synthetic. No OEM temperature, current or vibration safety thresholds have been applied.")

with t_quality:
    st.markdown('<div class="diq-section">Fluid properties, polymer-conditioning index & separation quality</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        graph(df,["Solids removal (%)"],"Simulated separation yield",[TEAL],290)
        graph(df,["pH"],"Simulated pH",[BLUE],270)
        graph(df,["LGS (%)","HGS (%)"],"Low / high gravity solids · synthetic",[AMBER,TEAL],270)
    with b:
        graph(df,["Quality index"],"Process-quality index · simulator scale",[AMBER],290)
        graph(df,["Mud weight (ppg)"],"Simulated mud weight",[TEAL],270)
        graph(df,["Polymer index (%)","Chemical index (%)"],"Virtual dosing indexes · NOT recipes",[AMBER,BLUE],270)
    with st.expander("Latest chemistry and separation readings", expanded=False):
        st.json({"synthetic_mud_chemistry":last["mud_chemistry"],"synthetic_separation_output":last["output"]})
    st.caption("All chemical and polymer percentages are simulator indexes, NOT calibrated dose rates, vendor setpoints, safe limits or operating recipes. No real chemical injection is performed.")

with t_logs:
    left,right=st.columns([1.1,1],gap="large")
    with left:
        st.markdown('<div class="diq-section">Historian event log</div>',unsafe_allow_html=True)
        if faults:
            st.dataframe(pd.DataFrame(faults),use_container_width=True,hide_index=True)
        else:
            st.info("No generated event labels in this synthetic run.")
        st.caption("These events are produced by the simulator, not by real PLC or plant alarms.")
    with right:
        st.markdown('<div class="diq-section">Operator observation</div>',unsafe_allow_html=True)
        with st.form("annotation_form",clear_on_submit=True):
            second=st.selectbox("Simulation time (s)",[r["timestamp_s"] for r in data],index=len(data)-1)
            quality=st.selectbox("Human-rated simulated cut",[
                "unknown","very_wet","wet","acceptable","dry","very_dry"])
            note=st.text_area("Observation",placeholder="Record a synthetic review note (no real rig or private data).")
            if st.form_submit_button("Save observation",type="primary",use_container_width=True):
                try:
                    add_note(selected,second,note,quality)
                    st.success("Note saved in local historian")
                except ValueError as exc:
                    st.error(str(exc))
        notes=get_notes(selected)
        if notes:
            st.dataframe(pd.DataFrame(notes),use_container_width=True,hide_index=True)

with t_raw:
    st.markdown('<div class="diq-section">Data lineage & export</div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.05,1],gap="large")
    with c1:
        st.markdown('''<div class="diq-card"><div class="diq-card-title">Traceable synthetic evidence</div>
        <div class="diq-card-body">Generated by an embedded-compatible C99 simulator, validated against
        the local schema, and historized in SQLite. No field sensors are connected.</div></div>''',unsafe_allow_html=True)
        st.dataframe(df.reset_index(),use_container_width=True,hide_index=True,height=380)
    with c2:
        st.write("**Run metadata**")
        st.json({"run_id":s["run_id"], "scenario":s["scenario"],
                 "source":s["sample_source"], "samples":s["samples"],
                 "operating_mode":s["operating_mode"],"sensor_valid":s["sensor_valid"],
                 "schema_version":last.get("schema_version","unknown")})
        ndjson="\n".join(json.dumps(x,separators=(",",":")) for x in data)+"\n"
        st.download_button("⬇ Export synthetic NDJSON",data=ndjson,
                           file_name=f"{selected}.ndjson",mime="application/x-ndjson",use_container_width=True)
        st.caption("All exports are synthetic, validated demonstration records.")

st.caption("Independent concept demonstrator informed by publicly available descriptions of [Kayden dewatering systems](https://www.kaydenindustries.com/energy-services/products-services/dewatering-systems/) and [decanter centrifuges](https://www.kaydenindustries.com/energy-services/products-services/centrifuges/). No association with Kayden Industries is claimed.")

st.markdown('''<div class="diq-footer"><b>SAFETY / SCOPE</b> &nbsp; Synthetic telemetry and advisory-only AI.
No physical PLC, VFD, centrifuge, valve, pump, dosing system, or safety-interlock connection is present.
Run simulations do not command real equipment. Nemotron interpretations are unverified hypotheses,
not operating instructions or industrial safety assessments.<br>
<b>REFERENCE</b> &nbsp; Kayden-style process workflow, independent demonstrator; not an OEM digital twin.<br>
<b>STACK</b> &nbsp; C99 · Python · SQLite · Streamlit · Plotly · NVIDIA Nemotron 3 Super via Nebius Token Factory</div>''',
unsafe_allow_html=True)
