import streamlit as st
import google.generativeai as genai
import pandas as pd

# =========================================
# 1. API KEY CONFIGURATION
# =========================================
# Your active Gemini API Key
GOOGLE_API_KEY = "AIzaSyAvlQYLnZUH1-QE8wzIv2Y2otsBDfTuBjg"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# =========================================
# 2. PAGE INITIALIZATION
# =========================================
st.set_page_config(page_title="AI Power Quality Compliance", layout="wide")
st.title("📉 AI-Driven Power Quality Health Check & Compliance System")
st.markdown("Automated grid monitoring mapping live parameters against IEC, IEEE, and Indian Electricity Grid Codes.")
st.markdown("---")

# =========================================
# 3. SIDEBAR TELEMETRY INPUTS
# =========================================
st.sidebar.header("🔌 Live Substation Meter Inputs")
nominal_v = st.sidebar.number_input("Nominal Voltage (V)", value=415.0)
base_measured_v = st.sidebar.number_input("Measured Line Voltage (V)", value=412.0)
v_unbalance = st.sidebar.slider("Voltage Unbalance (%)", 0.0, 5.0, 1.2)
i_unbalance = st.sidebar.slider("Current Unbalance (%)", 0.0, 30.0, 8.0)
frequency = st.sidebar.number_input("Grid Frequency (Hz)", value=49.85, format="%.2f")
power_factor = st.sidebar.number_input("Power Factor (PF)", value=0.91, min_value=0.0, max_value=1.0)
v_thd = st.sidebar.slider("Voltage Harmonic Distortion (THD %)", 0.0, 15.0, 6.5)

# --- UPGRADED: Transient Event Injection with State Tracking ---
st.sidebar.markdown("---")
st.sidebar.subheader("💥 Transient Event Injection")

# Initialize persistent tracking so buttons don't reset when auditing
if "transient_mode" not in st.session_state:
    st.session_state.transient_mode = "Normal"

col_sag, col_swell = st.sidebar.columns(2)
if col_sag.button("📉 Inject Sag"):
    st.session_state.transient_mode = "Sag"
if col_swell.button("📈 Inject Swell"):
    st.session_state.transient_mode = "Swell"
if st.sidebar.button("🔄 Reset to Normal"):
    st.session_state.transient_mode = "Normal"

# Override measured voltage dynamically based on injection selection
if st.session_state.transient_mode == "Sag":
    measured_v = nominal_v * 0.4  # Forces voltage to 0.4 per-unit (pu)
    st.sidebar.warning("⚠️ Active Simulation: 0.4 pu Voltage Sag Injected!")
elif st.session_state.transient_mode == "Swell":
    measured_v = nominal_v * 1.4  # Forces voltage to 1.4 per-unit (pu)
    st.sidebar.warning("⚠️ Active Simulation: 1.4 pu Voltage Swell Injected!")
else:
    measured_v = base_measured_v

# =========================================
# 4. DETERMINISTIC COMPLIANCE RULES
# =========================================
violations = []

# Calculate per-unit metrics and deviation thresholds 
v_pu = measured_v / nominal_v
v_dev = abs((measured_v - nominal_v) / nominal_v) * 100

# Upgraded Transient & Voltage Standard Checks 
if v_pu < 0.90:
    violations.append(f"Critical Voltage Sag Detected ({v_pu:.2f} pu) - Matches IEEE 1159 grid event ")
elif v_pu > 1.10:
    violations.append(f"Critical Voltage Swell Detected ({v_pu:.2f} pu) - Matches IEEE 1159 grid event ")
elif v_dev > 10.0:
    violations.append(f"Voltage Deviation ({v_dev:.1f}%) crosses 10% limit (IEC 60038 / IS 12360) ")

# Check Voltage Unbalance (Tolerance: preferred <=2%, industrial <=3%) 
if v_unbalance > 2.0:
    violations.append(f"Voltage Unbalance ({v_unbalance}%) exceeds optimal 2% limit (IEC 61000-2-2) ")

# Check Current Unbalance (Alert at >10%, Critical at >20%) 
if i_unbalance > 10.0:
    violations.append(f"Current Unbalance ({i_unbalance}%) triggers NEMA/IEEE Warning threshold ")

# Check Frequency (India Grid Band: 49.90 - 50.05 Hz) 
if not (49.90 <= frequency <= 50.05):
    violations.append(f"Grid Frequency ({frequency} Hz) violated CERC/Indian Electricity Grid Code band ")

# Check Power Factor (Target >=0.95 lag) 
if power_factor < 0.95:
    violations.append(f"Power Factor ({power_factor}) is below 0.95 target. CEA/DISCOM tariff penalty active! ")

# Check Harmonic Distortion (Tolerance: Usually <=5% or <=8%) 
if v_thd > 5.0:
    violations.append(f"Voltage THD ({v_thd}%) violates IEEE 519 baseline limit (<=5%) ")

# =========================================
# 5. DASHBOARD LAYOUT
# =========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Compliance Status Metrics")
    
    st.metric("Grid Frequency", f"{frequency} Hz", delta="OUTSIDE CERC BAND" if not (49.90 <= frequency <= 50.05) else "Normal", delta_color="inverse")
    st.metric("Power Factor", f"{power_factor}", delta="PENALTY ACTIVE" if power_factor < 0.95 else "Optimal", delta_color="inverse")
    st.metric("Voltage Distortion (THD)", f"{v_thd} %", delta="IEEE 519 Violation" if v_thd > 5.0 else "Clean", delta_color="inverse")
    
    # Live updates if you override standard voltage reading via simulation buttons
    if st.session_state.transient_mode != "Normal":
        st.metric("Simulated Voltage", f"{measured_v:.1f} V ({v_pu:.2f} pu)", delta=f"Injected {st.session_state.transient_mode}", delta_color="inverse")

    st.markdown("### ⚠️ Active Compliance Alerts")
    if violations:
        for alert in violations:
            st.error(alert)
    else:
        st.success("🟢 Complete Power Quality Grid Compliance. System is clean.")

with col2:
    st.subheader("🤖 Agentic AI PQ Engineering Auditor")
    
    if st.button("🔬 Generate Comprehensive Compliance Audit"):
        prompt = f"""
        You are an advanced industrial Power Quality engineering auditing agent. 
        Analyze the following system measurements and active violations against global standards:
        - Nominal Supply: {nominal_v}V, Measured Supply: {measured_v}V (Per-Unit: {v_pu:.2f} pu, Deviation: {v_dev:.1f}%)
        - Voltage Unbalance: {v_unbalance}%, Current Unbalance: {i_unbalance}%
        - Operating Frequency: {frequency} Hz
        - Operating Power Factor: {power_factor}
        - Voltage Total Harmonic Distortion (THD): {v_thd}%
        
        Active Rules Flashed: {violations}

        Generate a high-level engineering compliance report detailing:
        1. Non-Compliance Analysis: Clearly explain which exact standards (such as IEC 60038, IEEE 519, IEEE 1159, or CERC guidelines) are breached based on the measurements.
        2. Root Cause Estimation: What typical substation conditions cause these signatures (e.g., non-linear loads like VFDs causing the THD spike, or sudden heavy motor startups causing a voltage sag).
        3. Corrective System Mitigation Action Plan: Direct, detailed technical recommendations for plant engineers (e.g., tuned harmonic filters, APFC bank stage switching, phase load balancing).
        Keep your structure clean, professional, and mapping directly back to standard codes.
        """
        
        with st.spinner("AI Engine auditing waveforms and parsing standards..."):
            response = model.generate_content(prompt)
            st.markdown(response.text)