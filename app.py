import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# Custom CSS for Gold/Brown Branding & Massive Typography
# ==========================================
st.markdown("""
<style>
/* Global Font and Text Color */
.stApp {
    font-size: 18px;
    color: #2E2E2E;
}
p, div, span, label, li {
    font-size: 16px !important;
    color: #333333 !important;
}

/* MASSIVE GOLD HEADERS */
h1 {
    font-size: 60px !important;
    color: #B8860B !important; /* Dark Goldenrod */
    font-weight: 900 !important;
    line-height: 1.1 !important;
    margin-bottom: 0 !important;
}
h2, .st-emotion-cache-10trblm {
    font-size: 36px !important;
    color: #B8860B !important; 
    font-weight: 700 !important;
    margin-top: 20px !important;
}
h3 {
    font-size: 28px !important;
    color: #CD7F32 !important; /* Bronze */
    font-weight: 600 !important;
}
h4 {
    font-size: 20px !important;
    color: #8B4513 !important; /* Saddle Brown */
    font-weight: 600 !important;
}

/* Sidebar Headers */
.stSidebar h1, .stSidebar h2, .stSidebar h3 {
    color: #B8860B !important;
}

/* Metrics Styling */
.stMetric label {
    font-size: 18px !important;
    color: #555555 !important;
}
.stMetric value {
    font-size: 32px !important;
    color: #8B4513 !important; /* Brown for metric values */
    font-weight: bold !important;
}

/* Tables */
.dataframe {
    font-size: 16px !important;
}

/* Buttons */
.stButton>button {
    font-size: 16px !important;
    background-color: #DAA520;
    color: white !important;
    border: none;
    padding: 10px 24px;
    border-radius: 5px;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #B8860B;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="Dataura SynthRWE - Colon Cancer Sandbox",
    page_icon="🏥",
    layout="wide"
)

# ==========================================
# Gold/Brown Color Palette for ALL Charts
# ==========================================
gold_brown_palette = {
    'Robotic': '#D4AF37',                 # Metallic Gold
    'Laparoscopic': '#B8860B',            # Dark Goldenrod
    'Open': '#8B4513',                    # Saddle Brown
    'Non-Surgical Management': '#CD7F32'  # Bronze
}
palette_list = ['#D4AF37', '#B8860B', '#8B4513', '#CD7F32', '#DAA520']

# ==========================================
# Title and Introduction
# ==========================================
st.markdown('<h1>🏥 Dataura SynthRWE®</h1>', unsafe_allow_html=True)
st.markdown('<h2 style="font-size: 32px; margin-top: -10px; color: #8B4513;">Colon Cancer Surgical Oncology Sandbox</h2>', unsafe_allow_html=True)

st.markdown('<p style="font-size: 18px; color: #2E2E2E;"><b>Synthetic Real-World Evidence Dataset for Feasibility Testing & Study Design</b></p>', unsafe_allow_html=True)

st.markdown("""
<p style="font-size: 17px; color: #3E3E3E;">
This dashboard demonstrates a synthetic longitudinal dataset of 10,000 colorectal cancer patients, 
mimicking US claims-like data with realistic patient selection patterns, treatment pathways, 
and outcomes across robotic-assisted, laparoscopic, and open surgery approaches.
</p>
""", unsafe_allow_html=True)

st.divider()

# ==========================================
# Load Data
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Dataura_SynthRWE_V2_ColonCancer_Microsimulation.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.warning("📁 Please upload your synthetic dataset CSV file:")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Data loaded successfully!")
    else:
        st.stop()

# ==========================================
# Sidebar: Filters
# ==========================================
st.sidebar.header("📊 Data Filters")

surgery_options = st.sidebar.multiselect(
    "Select Surgical Approaches:",
    options=df['Surgery_Type'].unique(),
    default=df['Surgery_Type'].unique()
)

age_min, age_max = int(df['Age'].min()), int(df['Age'].max())
age_range = st.sidebar.slider(
    "Age Range:",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max)
)

cci_max = st.sidebar.slider(
    "Maximum CCI Score:",
    min_value=0,
    max_value=int(df['CCI_Score'].max()),
    value=int(df['CCI_Score'].max())
)

df_filtered = df[
    (df['Surgery_Type'].isin(surgery_options)) &
    (df['Age'] >= age_range[0]) &
    (df['Age'] <= age_range[1]) &
    (df['CCI_Score'] <= cci_max)
]

# ==========================================
# Key Metrics (KPI Cards)
# ==========================================
st.subheader("📊 Cohort Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Patients", f"{len(df_filtered):,}")
with col2:
    st.metric("Mean Age", f"{df_filtered['Age'].mean():.1f} years")
with col3:
    st.metric("Avg Length of Stay", f"{df_filtered['Length_of_Stay_Days'].mean():.1f} days")
with col4:
    st.metric("30-Day Complication Rate", f"{df_filtered['Has_30Day_Complication'].mean() * 100:.1f}%")

st.divider()

# ==========================================
# Chart 1: Patient Distribution
# ==========================================
st.subheader("👥 Patient Distribution by Surgical Approach")
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_patient_count = px.bar(
        df_filtered.groupby('Surgery_Type').size().reset_index(name='Count'),
        x='Surgery_Type', y='Count', color='Surgery_Type',
        title='Patient Count by Surgery Type',
        color_discrete_map=gold_brown_palette
    )
    fig_patient_count.update_layout(showlegend=False, xaxis_title="", yaxis_title="Patient Count", template='plotly_white')
    st.plotly_chart(fig_patient_count, use_container_width=True)

with col_chart2:
    fig_pie = px.pie(
        df_filtered, names='Surgery_Type', title='Surgical Approach Distribution',
        color='Surgery_Type', color_discrete_map=gold_brown_palette
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(template='plotly_white')
    st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# Chart 2: Baseline Characteristics
# ==========================================
st.subheader("📋 Baseline Characteristics by Surgical Approach")

baseline_cols = ['Age', 'CCI_Score', 'COPD', 'CHF', 'Diabetes_Uncomplicated']
baseline_df = df_filtered.groupby('Surgery_Type')[baseline_cols].mean().reset_index()

baseline_df['Age'] = baseline_df['Age'].round(1)
baseline_df['CCI_Score'] = baseline_df['CCI_Score'].round(2)
baseline_df['COPD'] = (baseline_df['COPD'] * 100).round(1).astype(str) + '%'
baseline_df['CHF'] = (baseline_df['CHF'] * 100).round(1).astype(str) + '%'
baseline_df['Diabetes_Uncomplicated'] = (baseline_df['Diabetes_Uncomplicated'] * 100).round(1).astype(str) + '%'

baseline_df_transposed = baseline_df.set_index('Surgery_Type').T
baseline_df_transposed.columns.name = None

target_order = ['Non-Surgical Management', 'Open', 'Laparoscopic', 'Robotic']
existing_cols = [col for col in target_order if col in baseline_df_transposed.columns]
baseline_df_transposed = baseline_df_transposed[existing_cols]

baseline_df_transposed = baseline_df_transposed.reset_index()
baseline_df_transposed = baseline_df_transposed.rename(columns={'index': 'Characteristic'})

st.dataframe(
    baseline_df_transposed,
    use_container_width=True,
    hide_index=True
)
st.caption("💡 Higher values indicate older age, higher CCI, or higher comorbidity prevalence. Note the selection bias in surgical approaches.")

# ==========================================
# Chart 3: Clinical Outcomes
# ==========================================
st.subheader("🏥 Clinical Outcomes & Resource Utilization")

outcomes_summary = df_filtered.groupby('Surgery_Type').agg(
    Avg_LOS=('Length_of_Stay_Days', 'mean'),
    Complication_Rate=('Has_30Day_Complication', 'mean'),
    Avg_Cost=('Total_Cost_USD', 'mean')
).reset_index()

outcomes_summary['Surgery_Type'] = pd.Categorical(outcomes_summary['Surgery_Type'], categories=target_order, ordered=True)
outcomes_summary = outcomes_summary.sort_values('Surgery_Type').dropna(subset=['Surgery_Type'])

col_out1, col_out2, col_out3 = st.columns(3)

with col_out1:
    st.markdown("#### Average Length of Stay (Days)")
    for _, row in outcomes_summary.iterrows():
        st.markdown(f"**{row['Surgery_Type']}**: {row['Avg_LOS']:.1f} days")

with col_out2:
    st.markdown("#### 30-Day Complication Rate")
    for _, row in outcomes_summary.iterrows():
        st.markdown(f"**{row['Surgery_Type']}**: {(row['Complication_Rate']*100):.1f}%")

with col_out3:
    st.markdown("#### Average Cost (USD)")
    for _, row in outcomes_summary.iterrows():
        st.markdown(f"**{row['Surgery_Type']}**: ${row['Avg_Cost']:,.0f}")

# ==========================================
# Chart 4: Cost vs Complications Scatter
# ==========================================
st.divider()
st.subheader("💰 Cost vs. Complication Rate Trade-off")

summary_scatter = df_filtered.groupby('Surgery_Type').agg(
    Avg_Cost=('Total_Cost_USD', 'mean'),
    Complication_Rate=('Has_30Day_Complication', 'mean'),
    Patient_Count=('Patient_ID', 'count')
).reset_index()
summary_scatter['Complication_Pct'] = summary_scatter['Complication_Rate'] * 100

fig_scatter = px.scatter(
    summary_scatter, x='Complication_Pct', y='Avg_Cost', size='Patient_Count',
    color='Surgery_Type', hover_name='Surgery_Type',
    title='Surgical Approach: Cost vs. 30-Day Complication Rate',
    labels={'Complication_Pct': '30-Day Complication Rate (%)', 'Avg_Cost': 'Average Total Cost (USD)'},
    color_discrete_map=gold_brown_palette
)
fig_scatter.update_traces(marker=dict(line=dict(color='black', width=1)))
fig_scatter.update_layout(template='plotly_white')
st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# Chart 5: LOS Distribution Box Plot
# ==========================================
st.subheader("📦 Length of Stay Distribution")

fig_los = px.box(
    df_filtered, x='Surgery_Type', y='Length_of_Stay_Days', color='Surgery_Type',
    title='Distribution of Length of Stay by Surgical Approach',
    labels={'Length_of_Stay_Days': 'Length of Stay (Days)'},
    color_discrete_map=gold_brown_palette
)
fig_los.update_layout(showlegend=False, template='plotly_white')
st.plotly_chart(fig_los, use_container_width=True)

# ==========================================
# Chart 6: Comorbidity Analysis
# ==========================================
st.subheader("🫁 Comorbidity Profile Analysis")

comorbidity_cols = ['COPD', 'CHF', 'Cerebrovascular_Disease', 'Diabetes_Uncomplicated', 'Renal_Disease']
comorbidity_df = df_filtered.groupby('Surgery_Type')[comorbidity_cols].mean() * 100

comorbidity_df_transposed = comorbidity_df.T
existing_cols_com = [col for col in target_order if col in comorbidity_df_transposed.columns]
comorbidity_df_transposed = comorbidity_df_transposed[existing_cols_com]

fig_comorbidity = go.Figure()

for i, idx in enumerate(comorbidity_df_transposed.index):
    fig_comorbidity.add_trace(go.Bar(
        name=idx.replace('_', ' '),
        x=comorbidity_df_transposed.columns,
        y=comorbidity_df_transposed.loc[idx],
        text=comorbidity_df_transposed.loc[idx].round(1).astype(str) + '%',
        textposition='auto',
        marker_color=palette_list[i % len(palette_list)] # Applying Gold/Brown palette
    ))

fig_comorbidity.update_layout(
    title='Comorbidity Prevalence by Surgical Approach (%)',
    xaxis_title='Surgical Approach', yaxis_title='Prevalence (%)',
    barmode='group', template='plotly_white', legend_title='Comorbidities'
)
st.plotly_chart(fig_comorbidity, use_container_width=True)

# ==========================================
# Data Download
# ==========================================
st.divider()
st.subheader("📥 Download Synthetic Dataset")

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Dataset as CSV",
    data=csv,
    file_name='Dataura_SynthRWE_Filtered_ColonCancer.csv',
    mime='text/csv',
)

st.markdown("---")
st.markdown('<h3 style="color: #B8860B;">Dataura SynthRWE®</h3>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 15px; color: #5E5E5E;"><i>Synthetic Real-World Evidence Data Engine. Generated for educational and feasibility testing purposes. Not for regulatory or clinical decision-making.</i></p>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 14px; color: #6E6E6E;">Seed: 20260711 | Dataset Version: V2.0 Microsimulation</p>', unsafe_allow_html=True)
