import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="Dataura SynthRWE - Colon Cancer Sandbox",
    page_icon="🏥",
    layout="wide"
)

# ==========================================
# Title and Introduction
# ==========================================
st.title("🏥 Dataura SynthRWE®: Colon Cancer Surgical Oncology Sandbox")
st.markdown("**Synthetic Real-World Evidence Dataset for Feasibility Testing & Study Design**")

st.markdown("""
This dashboard demonstrates a synthetic longitudinal dataset of 10,000 colorectal cancer patients, 
mimicking US claims-like data with realistic patient selection patterns, treatment pathways, 
and outcomes across robotic-assisted, laparoscopic, and open surgery approaches.
""")

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

# If data doesn't exist, provide upload option
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

# Surgery type filter
surgery_options = st.sidebar.multiselect(
    "Select Surgical Approaches:",
    options=df['Surgery_Type'].unique(),
    default=df['Surgery_Type'].unique()
)

# Age range filter
age_min, age_max = int(df['Age'].min()), int(df['Age'].max())
age_range = st.sidebar.slider(
    "Age Range:",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max)
)

# CCI score filter
cci_max = st.sidebar.slider(
    "Maximum CCI Score:",
    min_value=0,
    max_value=int(df['CCI_Score'].max()),
    value=int(df['CCI_Score'].max())
)

# Apply filters
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
    avg_age = df_filtered['Age'].mean()
    st.metric("Mean Age", f"{avg_age:.1f} years")

with col3:
    avg_los = df_filtered['Length_of_Stay_Days'].mean()
    st.metric("Avg Length of Stay", f"{avg_los:.1f} days")

with col4:
    comp_rate = df_filtered['Has_30Day_Complication'].mean() * 100
    st.metric("30-Day Complication Rate", f"{comp_rate:.1f}%")

st.divider()

# ==========================================
# Chart 1: Patient Distribution
# ==========================================
st.subheader("👥 Patient Distribution by Surgical Approach")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_patient_count = px.bar(
        df_filtered.groupby('Surgery_Type').size().reset_index(name='Count'),
        x='Surgery_Type',
        y='Count',
        color='Surgery_Type',
        title='Patient Count by Surgery Type',
        color_discrete_map={
            'Robotic': '#00CC96',
            'Laparoscopic': '#636EFA',
            'Open': '#EF553B',
            'Non-Surgical Management': '#AB63FA'
        }
    )
    fig_patient_count.update_layout(showlegend=False, xaxis_title="", yaxis_title="Patient Count")
    st.plotly_chart(fig_patient_count, use_container_width=True)

with col_chart2:
    fig_pie = px.pie(
        df_filtered,
        names='Surgery_Type',
        title='Surgical Approach Distribution',
        color='Surgery_Type',
        color_discrete_map={
            'Robotic': '#00CC96',
            'Laparoscopic': '#636EFA',
            'Open': '#EF553B',
            'Non-Surgical Management': '#AB63FA'
        }
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# Chart 2: Baseline Characteristics (FIXED - with %)
# ==========================================
st.subheader("📋 Baseline Characteristics by Surgical Approach")

baseline_cols = ['Age', 'CCI_Score', 'COPD', 'CHF', 'Diabetes_Uncomplicated']
baseline_df = df_filtered.groupby('Surgery_Type')[baseline_cols].mean().reset_index()

# Convert comorbidities to percentages
baseline_df['COPD'] = (baseline_df['COPD'] * 100).round(1)
baseline_df['CHF'] = (baseline_df['CHF'] * 100).round(1)
baseline_df['Diabetes_Uncomplicated'] = (baseline_df['Diabetes_Uncomplicated'] * 100).round(1)

# Round other columns
baseline_df['Age'] = baseline_df['Age'].round(1)
baseline_df['CCI_Score'] = baseline_df['CCI_Score'].round(2)

# Transpose for display
baseline_df_transposed = baseline_df.set_index('Surgery_Type').T
baseline_df_transposed.columns.name = None

# Reorder columns
target_order = ['Non-Surgical Management', 'Open', 'Laparoscopic', 'Robotic']
existing_cols = [col for col in target_order if col in baseline_df_transposed.columns]
baseline_df_transposed = baseline_df_transposed[existing_cols]

# Reset index to make it a proper column
baseline_df_transposed = baseline_df_transposed.reset_index()
baseline_df_transposed = baseline_df_transposed.rename(columns={'index': 'Characteristic'})

# Display the dataframe
st.dataframe(
    baseline_df_transposed,
    use_container_width=True,
    hide_index=True
)

st.caption("💡 Comorbidities shown as prevalence (%). Note the selection bias: Robotic surgery patients are younger and have lower CCI scores.")

# ==========================================
# Chart 3: Clinical Outcomes
# ==========================================
st.subheader("🏥 Clinical Outcomes & Resource Utilization")

outcomes_cols = ['Length_of_Stay_Days', 'Has_30Day_Complication', 'Total_Cost_USD']
outcomes_df = df_filtered.groupby('Surgery_Type')[outcomes_cols].mean().reset_index()
outcomes_df['Complication_Rate_%'] = outcomes_df['Has_30Day_Complication'] * 100

# Transpose for display
outcomes_df_transposed = outcomes_df.set_index('Surgery_Type').T
outcomes_df_transposed.columns.name = None
existing_cols_out = [col for col in target_order if col in outcomes_df_transposed.columns]
outcomes_df_transposed = outcomes_df_transposed[existing_cols_out]

# Display in columns
col_out1, col_out2, col_out3 = st.columns(3)

with col_out1:
    st.markdown("#### Average Length of Stay (Days)")
    for col in existing_cols_out:
        val = outcomes_df[outcomes_df['Surgery_Type'] == col]['Length_of_Stay_Days'].mean()
        st.text(f"{col}: {val:.1f} days")

with col_out2:
    st.markdown("#### 30-Day Complication Rate (%)")
    for col in existing_cols_out:
        val = outcomes_df[outcomes_df['Surgery_Type'] == col]['Has_30Day_Complication'].mean() * 100
        st.text(f"{col}: {val:.1f}%")

with col_out3:
    st.markdown("#### Average Cost (USD)")
    for col in existing_cols_out:
        val = outcomes_df[outcomes_df['Surgery_Type'] == col]['Total_Cost_USD'].mean()
        st.text(f"{col}: ${val:,.0f}")

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
    color_discrete_map={
        'Robotic': '#00CC96',
        'Laparoscopic': '#636EFA',
        'Open': '#EF553B',
        'Non-Surgical Management': '#AB63FA'
    }
)

fig_scatter.update_traces(
    marker=dict(line=dict(color='black', width=1)),
    textposition='top center'
)
fig_scatter.update_layout(template='plotly_white')

st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# Chart 5: LOS Distribution Box Plot
# ==========================================
st.subheader("📦 Length of Stay Distribution")

fig_los = px.box(
    df_filtered,
    x='Surgery_Type',
    y='Length_of_Stay_Days',
    color='Surgery_Type',
    title='Distribution of Length of Stay by Surgical Approach',
    labels={'Length_of_Stay_Days': 'Length of Stay (Days)'},
    color_discrete_map={
        'Robotic': '#00CC96',
        'Laparoscopic': '#636EFA',
        'Open': '#EF553B',
        'Non-Surgical Management': '#AB63FA'
    }
)
fig_los.update_layout(showlegend=False, template='plotly_white')
st.plotly_chart(fig_los, use_container_width=True)

# ==========================================
# Chart 6: Comorbidity Analysis
# ==========================================
st.subheader("🫁 Comorbidity Profile Analysis")

comorbidity_cols = ['COPD', 'CHF', 'Cerebrovascular_Disease', 'Diabetes_Uncomplicated', 'Renal_Disease']
comorbidity_df = df_filtered.groupby('Surgery_Type')[comorbidity_cols].mean() * 100  # Convert to %

# Transpose and sort
comorbidity_df_transposed = comorbidity_df.T
existing_cols_com = [col for col in target_order if col in comorbidity_df_transposed.columns]
comorbidity_df_transposed = comorbidity_df_transposed[existing_cols_com]

fig_comorbidity = go.Figure()

for idx in comorbidity_df_transposed.index:
    fig_comorbidity.add_trace(go.Bar(
        name=idx.replace('_', ' '),
        x=comorbidity_df_transposed.columns,
        y=comorbidity_df_transposed.loc[idx],
        text=comorbidity_df_transposed.loc[idx].round(1).astype(str) + '%',
        textposition='auto'
    ))

fig_comorbidity.update_layout(
    title='Comorbidity Prevalence by Surgical Approach (%)',
    xaxis_title='Surgical Approach',
    yaxis_title='Prevalence (%)',
    barmode='group',
    template='plotly_white',
    legend_title='Comorbidities'
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
st.markdown("**Dataura SynthRWE®** - Synthetic Real-World Evidence Data Engine")
st.markdown("*Generated for educational and feasibility testing purposes. Not for regulatory or clinical decision-making.*")
st.markdown("Seed: 20260711 | Dataset Version: V2.0 Microsimulation")
