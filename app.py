import streamlit as st
import pandas as pd
import numpy as np
import skfuzzy as fuzz
import matplotlib.pyplot as plt

st.set_page_config(page_title="Smart Home Energy Management", page_icon="🏠", layout="wide")

# Fuzzy input ranges and membership functions
occupancy_range = np.arange(0, 11, 1)
temperature_range = np.arange(15, 36, 1)
light_range = np.arange(0, 101, 1)

occupancy_zero = fuzz.trapmf(occupancy_range, [0, 0, 0, 1])
occupancy_few = fuzz.trapmf(occupancy_range, [0, 1, 3, 5])
occupancy_many = fuzz.trapmf(occupancy_range, [3, 5, 10, 10])

temperature_cold = fuzz.trapmf(temperature_range, [15, 15, 19, 23])
temperature_normal = fuzz.trapmf(temperature_range, [20, 23, 26, 29])
temperature_hot = fuzz.trapmf(temperature_range, [26, 30, 35, 35])

light_dark = fuzz.trapmf(light_range, [0, 0, 20, 45])
light_dim = fuzz.trapmf(light_range, [30, 45, 55, 75])
light_bright = fuzz.trapmf(light_range, [60, 80, 100, 100])

# Create the same 27 rules used in the notebook
rules = []
for occupancy_label in ["Zero", "Few", "Many"]:
    for temperature_label in ["Cold", "Normal", "Hot"]:
        for light_label in ["Dark", "Dim", "Bright"]:
            if occupancy_label == "Zero":
                ac_power = 0
                lighting_power = 0
            else:
                if temperature_label == "Cold":
                    ac_power = 0
                elif temperature_label == "Normal":
                    ac_power = 0 if occupancy_label == "Few" else 50
                else:
                    ac_power = 50 if occupancy_label == "Few" else 100

                if light_label == "Dark":
                    lighting_power = 100
                elif light_label == "Dim":
                    lighting_power = 50
                else:
                    lighting_power = 0

            rules.append({
                "Occupancy": occupancy_label,
                "Temperature": temperature_label,
                "Natural Light": light_label,
                "AC Power": ac_power,
                "Lighting Power": lighting_power
            })

def calculate_fuzzy_output(occupancy, temperature, natural_light):
    occupancy_degrees = {
        "Zero": fuzz.interp_membership(occupancy_range, occupancy_zero, occupancy),
        "Few": fuzz.interp_membership(occupancy_range, occupancy_few, occupancy),
        "Many": fuzz.interp_membership(occupancy_range, occupancy_many, occupancy)
    }
    temperature_degrees = {
        "Cold": fuzz.interp_membership(temperature_range, temperature_cold, temperature),
        "Normal": fuzz.interp_membership(temperature_range, temperature_normal, temperature),
        "Hot": fuzz.interp_membership(temperature_range, temperature_hot, temperature)
    }
    light_degrees = {
        "Dark": fuzz.interp_membership(light_range, light_dark, natural_light),
        "Dim": fuzz.interp_membership(light_range, light_dim, natural_light),
        "Bright": fuzz.interp_membership(light_range, light_bright, natural_light)
    }

    weighted_ac = 0.0
    weighted_light = 0.0
    total_strength = 0.0

    for rule in rules:
        alpha = min(
            occupancy_degrees[rule["Occupancy"]],
            temperature_degrees[rule["Temperature"]],
            light_degrees[rule["Natural Light"]]
        )
        if alpha > 0:
            weighted_ac += alpha * rule["AC Power"]
            weighted_light += alpha * rule["Lighting Power"]
            total_strength += alpha

    if total_strength == 0:
        return 0.0, 0.0
    return weighted_ac / total_strength, weighted_light / total_strength

st.title("🏠 Smart Home Energy Management")
st.caption("Fuzzy Logic Controller • Interactive Simulation")
st.info("غيّر القيم من لوحة التحكم واضغط على زر حساب النتائج. هذه محاكاة لمستويات التحكم وليست قياسًا فعليًا لاستهلاك الكهرباء.")

with st.sidebar:
    st.header("Input Settings")
    occupancy = st.slider("Number of people", min_value=0, max_value=10, value=2, step=1)
    temperature = st.slider("Room temperature (°C)", min_value=15, max_value=35, value=30, step=1)
    natural_light = st.slider("Natural light (%)", min_value=0, max_value=100, value=40, step=1)
    calculate = st.button("Calculate", type="primary", use_container_width=True)

# Compute on each rerun so sliders work naturally; button is a visual cue.
ac_power, lighting_power = calculate_fuzzy_output(occupancy, temperature, natural_light)

st.subheader("Current Room Conditions")
c1, c2, c3 = st.columns(3)
c1.metric("People", f"{occupancy}")
c2.metric("Temperature", f"{temperature} °C")
c3.metric("Natural light", f"{natural_light}%")

st.subheader("Recommended Control Levels")
m1, m2 = st.columns(2)
m1.metric("❄️ AC power level", f"{ac_power:.1f}%")
m2.metric("💡 Lighting power level", f"{lighting_power:.1f}%")

g1, g2 = st.columns(2)
with g1:
    st.write("**Air Conditioner**")
    st.progress(int(np.clip(round(ac_power), 0, 100)))
    st.write(f"{ac_power:.1f}%")
with g2:
    st.write("**Lighting**")
    st.progress(int(np.clip(round(lighting_power), 0, 100)))
    st.write(f"{lighting_power:.1f}%")

st.subheader("Output Comparison")
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(["AC Power", "Lighting Power"], [ac_power, lighting_power])
ax.set_ylim(0, 100)
ax.set_ylabel("Control level (%)")
ax.grid(axis="y", alpha=0.25)
st.pyplot(fig, clear_figure=True)
plt.close(fig)

with st.expander("Show the 27 fuzzy rules"):
    st.dataframe(pd.DataFrame(rules), use_container_width=True, hide_index=True)

st.caption("Project note: output values are control percentages generated by the project's fuzzy rules, not real kWh consumption.")
