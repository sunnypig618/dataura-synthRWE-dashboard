import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# Dataura LIGHTER Gold/Brown/Yellow Palette
# ==========================================
# Much lighter and brighter than before
COLOR_ROBOTIC = '#FFD700'         # Bright Gold
COLOR_LAPAROSCOPIC = '#FFC125'    # Goldenrod 1 (Light Gold)
COLOR_OPEN = '#DAA520'            # Goldenrod (Standard Gold)
COLOR_NON_SURGICAL = '#F4A460'    # Sandy Brown (Light Brown)

SURGERY_COLORS = {
    'Robotic': COLOR_ROBOTIC,
    'Laparoscopic': COLOR_LAPAROSCOPIC,
    'Open': COLOR_OPEN,
    'Non-Surgical Management': COLOR_NON_SURGICAL
}

COMORBIDITY_COLORS = ['#FFD700', '#FFC125', '#DAA520', '#F4A460', '#DEB887']

# ==========================================
# Custom CSS (Base styles)
# ==========================================
st.markdown("""
<style>
/* Overall app font */
.stApp {
    font-size: 17px;
    color: #1E1E1E;
}

/* All body text darker and bigger */
p, div, span, label, li {
    font-size: 16px !important;
    color: #1E1E1E !important;
}

/* Sidebar text */
.stSidebar p, .stSidebar label, .stSidebar span {
    font-size: 15px !important;
    color: #1E1E1E !important;
}

/* Metric cards */
[data-testid="stMetricLabel"] {
    font-size: 16px !important;
    color: #8B4513 !important; /* Brown for labels */
    font-weight: bold !important;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    color: #B8860B !important; /* Dark Gold for values */
}

/* Tables */
table {
    font-size: 15px !important;
}

/* Download button */
.stButton > button {
    font-size: 16px !important;
    background-color: #DAA520 !important;
    color: white !important;
    border: none !important;
    padding: 10px 24px !important;
    border-radius: 6px !important;
    font-weight: bold !important;
}
.stButton > button:hover {
    background-color: #FFD700 !important;
    color: #1E1E1E !important;
}

/* Dividers */
hr {
    border-color: #DAA520 !important;
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
# Title - FORCED BIG and GOLD using HTML
# ==========================================
st.markdown(
    '<h1 style="color: #FFD700; font-size: 64px; font-weight: 900; margin-bottom: 0px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">'
    '🏥 Dataura SynthRWE®'
    '</h1>',
    unsafe_allow_html=True
)

st.markdown(
    '<h2 style="color: #DAA520; font-size: 36px; font-weight: bold; margin-top: 0px;">'
    'Colon Cancer Surgical Oncology Sandbox'
    '</h2>',
    unsafe_allow_html=True
)

st.markdown(
    '<p style="font-size: 19px; color: #1E1E1E;">'
    '<b>Synthetic Real-World Evidence Dataset for Feasibility Testing & Study Design</b></p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p style="font-size: 17px; color: #3E3E3E;">'
    'This dashboard demonstrates a synthetic longitudinal dataset of 10,000 colorectal cancer patients, '
    'mimicking US claims-like data with realistic patient selection patterns, treatment pathways, '
    'and outcomes across robotic-assisted, laparoscopic, and open surgery approaches.'
    '</p>',
    unsafe_allow_html=True
)

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
# Force sidebar header to be gold
st.sidebar.markdown('<h2 style="color: #DAA520; font-size: 28px;">📊 Data Filters</h2>', unsafe_allow_html=True)

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
# Helper Function for Gold Section Headers
# ==========================================
def gold_header(text, level=3):
    """Creates a gold header that Streamlit cannot override."""
    if level == 2:
        size = "32px"
    elif level == 3:
        size = "26px"
    else:
        size = "20px"
    st.markdown(f'<h{level} style="color: #DAA520; font-size: {size}; font-weight: bold;">{text}</h{level}>', unsafe_allow_html=True)

# ==========================================
# KPI Cards
# ==========================================
gold_header("📊 Cohort Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Patients", f"{len(df_filtered):,}")

with col2:
    st.metric("Mean Age", f"{df_filtered['Age'].mean():.1f} years")

with col3:
    st.metric("Avg Length of Stay", f"{df_filtered['Length_of_Stay_Days'].mean():.1f} days")

with col4:
    comp_rate = df_filtered['Has_30Day_Complication'].mean() * 100
    st.metric("30-Day Complication Rate", f"{comp_rate:.1f}%")

st.divider()

# ==========================================
# Chart 1: Patient Distribution
# ==========================================
gold_header("👥 Patient Distribution by Surgical Approach")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    count_df = df_filtered.groupby('Surgery_Type').size().reset_index(name='Count')
    fig_patient_count = px.bar(
        count_df,
        x='Surgery_Type',
        y='Count',
        color='Surgery_Type',
        title='Patient Count by Surgery Type',
        color_discrete_map=SURGERY_COLORS
    )
    fig_patient_count.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Patient Count",
        title_font_color='#DAA520',
        title_font_size=20,
        template='plotly_white'
    )
    st.plotly_chart(fig_patient_count, use_container_width=True)

with col_chart2:
    fig_pie = px.pie(
        df_filtered,
        names='Surgery_Type',
        title='Surgical Approach Distribution',
        color='Surgery_Type',
        color_discrete_map=SURGERY_COLORS
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(
        title_font_color='#DAA520',
        title_font_size=20,
        template='plotly_white'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# Chart 2: Baseline Characteristics Table
# ==========================================
gold_header("📋 Baseline Characteristics by Surgical Approach")

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
# Chart 3: Clinical Outcomes Table
# ==========================================
gold_header("🏥 Clinical Outcomes & Resource Utilization")

outcomes_agg = df_filtered.groupby('Surgery_Type').agg(
    Avg_LOS=('Length_of_Stay_Days', 'mean'),
    Complication_Rate=('Has_30Day_Complication', 'mean'),
    Avg_Cost=('Total_Cost_USD', 'mean'),
    Patient_N=('Patient_ID', 'count')
).reset_index()

outcomes_agg['Avg_LOS'] = outcomes_agg['Avg_LOS'].round(1)
outcomes_agg['Complication_Rate_%'] = (outcomes_agg['Complication_Rate'] * 100).round(1).astype(str) + '%'
outcomes_agg['Avg_Cost'] = '$' + outcomes_agg['Avg_Cost'].round(0).astype(int).astype(str).apply(lambda x: f"{int(x):,}")

outcomes_transposed = outcomes_agg[['Surgery_Type', 'Avg_LOS', 'Complication_Rate_%', 'Avg_Cost', 'Patient_N']].set_index('Surgery_Type').T
outcomes_transposed.columns.name = None
existing_cols_out = [col for col in target_order if col in outcomes_transposed.columns]
outcomes_transposed = outcomes_transposed[existing_cols_out]
outcomes_transposed = outcomes_transposed.reset_index()
outcomes_transposed = outcomes_transposed.rename(columns={'index': 'Outcome'})

row_labels = {
    'Avg_LOS': 'Avg Length of Stay (Days)',
    'Complication_Rate_%': '30-Day Complication Rate',
    'Avg_Cost': 'Avg Total Cost (USD)',
    'Patient_N': 'Patient Count'
}
outcomes_transposed['Outcome'] = outcomes_transposed['Outcome'].map(row_labels)

st.dataframe(
    outcomes_transposed,
    use_container_width=True,
    hide_index=True
)

st.divider()

# ==========================================
# Chart 4: Cost vs Complications Scatter
# ==========================================
gold_header("💰 Cost vs. Complication Rate Trade-off")

summary_scatter = df_filtered.groupby('Surgery_Type').agg(
    Avg_Cost=('Total_Cost_USD', 'mean'),
    Complication_Rate=('Has_30Day_Complication', 'mean'),
    Patient_Count=('Patient_ID', 'count')
).reset_index()

summary_scatter['Complication_Pct'] = summary_scatter['Complication_Rate'] * 100

fig_scatter = px.scatter(
    summary_scatter,
    x='Complication_Pct',
    y='Avg_Cost',
    size='Patient_Count',
    color='Surgery_Type',
    hover_name='Surgery_Type',
    title='Surgical Approach: Cost vs. 30-Day Complication Rate',
    labels={
        'Complication_Pct': '30-Day Complication Rate (%)',
        'Avg_Cost': 'Average Total Cost (USD)'
    },
    color_discrete_map=SURGERY_COLORS
)

fig_scatter.update_traces(
    marker=dict(line=dict(color='#8B4513', width=1.5)), # Brown border for visibility
    textposition='top center'
)
fig_scatter.update_layout(
    template='plotly_white',
    title_font_color='#DAA520',
    title_font_size=22,
    xaxis_title_font_color='#8B4513',
    yaxis_title_font_color='#8B4513',
    legend_title_font_color='#8B4513'
)

st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# Chart 5: LOS Box Plot
# ==========================================
gold_header("📦 Length of Stay Distribution")

fig_los = px.box(
    df_filtered,
    x='Surgery_Type',
    y='Length_of_Stay_Days',
    color='Surgery_Type',
    title='Distribution of Length of Stay by Surgical Approach',
    labels={'Length_of_Stay_Days': 'Length of Stay (Days)'},
    color_discrete_map=SURGERY_COLORS
)
fig_los.update_layout(
    showlegend=False,
    template='plotly_white',
    title_font_color='#DAA520',
    title_font_size=22,
    xaxis_title_font_color='#8B4513',
    yaxis_title_font_color='#8B4513'
)
st.plotly_chart(fig_los, use_container_width=True)

# ==========================================
# Chart 6: Comorbidity Grouped Bar
# ==========================================
gold_header("🫁 Comorbidity Profile Analysis")

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
        marker_color=COMORBIDITY_COLORS[i % len(COMORBIDITY_COLORS)],
        marker_line_color='#8B4513',
        marker_line_width=1
    ))

fig_comorbidity.update_layout(
    title='Comorbidity Prevalence by Surgical Approach (%)',
    title_font_color='#DAA520',
    title_font_size=22,
    xaxis_title='Surgical Approach',
    xaxis_title_font_color='#8B4513',
    yaxis_title='Prevalence (%)',
    yaxis_title_font_color='#8B4513',
    barmode='group',
    template='plotly_white',
    legend_title='Comorbidities',
    legend_title_font_color='#8B4513'
)

st.plotly_chart(fig_comorbidity, use_container_width=True)

# ==========================================
# Download
# ==========================================
st.divider()
gold_header("📥 Download Synthetic Dataset")

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Dataset as CSV",
    data=csv,
    file_name='Dataura_SynthRWE_Filtered_ColonCancer.csv',
    mime='text/csv',
)

# ==========================================
# Footer
# ==========================================
st.markdown("---")
st.markdown(
    '<h2 style="color: #DAA520; font-size: 32px; margin-bottom: 4px; font-weight: bold;">Dataura SynthRWE®</h2>'
    '<p style="font-size: 16px; color: #1E1E1E;">Synthetic Real-World Evidence Data Engine</p>'
    '<p style="font-size: 14px; color: #5E5E5E;"><i>Generated for educational and feasibility testing purposes. '
    'Not for regulatory or clinical decision-making.</i></p>'
    '<p style="font-size: 13px; color: #8B4513;">Seed: 20260711 | Dataset Version: V2.0 Microsimulation</p>',
    unsafe_allow_html=True
)
