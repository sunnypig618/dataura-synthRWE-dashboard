import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="Dataura V3.0 - Evidence-Calibrated",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# Header & Literature Context
# ==========================================
st.title("🧬 Dataura SynthRWE® V3.0")
st.markdown("### Evidence-Calibrated Microsimulation Engine")
st.markdown("""
This V3.0 dataset fuses fragmented literature into a cohesive, patient-level tokenized sandbox. 
It mathematically preserves real-world health disparities, treatment pathways, and cost structures.
""")

with st.expander("📚 View Literature Sources & Benchmarks (Click to Expand)"):
    st.markdown("""
    **1. Epidemiology & Staging (Siegel et al., CA Cancer J Clin 2026)**
    - US CRC projections, age/sex distributions, and stage at diagnosis.
    
    **2. SES & Survival Disparities (Zhu et al., SEER 2023)**
    - Median Household Income (MHI) impact on survival (High MHI HR=0.877 vs Low MHI).
    - Stage IV presentation rates by SES (Low: 10.5%, High: 7.8%).
    
    **3. Guideline Impact on Treatment (Bekaii-Saab et al., Optum Claims 2024)**
    - Regorafenib flexible dosing uptake post-NCCN guideline update (45.3%).
    
    **4. Economic Burden & Cost Drivers (Jafari et al., Systematic Review 2024)**
    - Direct medical cost drivers: Hospitalization (~36%), Drugs (~20%), Surgery (~16%).
    """)

st.divider()

# ==========================================
# Load Data
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Dataura_SynthRWE_V3_Evidence_Calibrated.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.warning("📁 V3.0 Dataset not found. Please upload `Dataura_SynthRWE_V3_Evidence_Calibrated.csv`:")
    uploaded_file = st.file_uploader("Choose the V3.0 CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ V3.0 Data loaded successfully!")
    else:
        st.stop()

# ==========================================
# Sidebar: Filters
# ==========================================
st.sidebar.header("🔍 Cohort Filters")

# Define strict categorical orders for consistency
ses_order = ['Low ($0-54k)', 'Medium ($55k-74k)', 'High ($75k+)']
stage_order = ['I', 'II', 'III', 'IV', 'Unknown']

ses_options = st.sidebar.multiselect(
    "Socioeconomic Status (MHI):",
    options=ses_order,
    default=ses_order
)

stage_options = st.sidebar.multiselect(
    "Stage at Diagnosis:",
    options=['I', 'II', 'III', 'IV'], # Exclude Unknown from filter for cleaner UI
    default=['I', 'II', 'III', 'IV']
)

loc_options = st.sidebar.multiselect(
    "Tumor Location:",
    options=df['Tumor_Location'].unique(),
    default=df['Tumor_Location'].unique()
)

# Apply filters
df_filtered = df[
    (df['SES_MHI_Category'].isin(ses_options)) &
    (df['Stage_at_Diagnosis'].isin(stage_options)) &
    (df['Tumor_Location'].isin(loc_options))
]

# ==========================================
# KPI Cards
# ==========================================
st.subheader("📊 Cohort Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Patients", f"{len(df_filtered):,}")
with col2:
    st.metric("Mean Age", f"{df_filtered['Age'].mean():.1f} years")
with col3:
    st.metric("Median Survival", f"{df_filtered['Survival_Months'].median():.1f} months")
with col4:
    avg_cost = df_filtered['Total_Direct_Medical_Cost'].mean()
    st.metric("Avg Direct Cost", f"${avg_cost:,.0f}")

st.divider()

# ==========================================
# Module 1: SES Disparities in Staging (Zhu et al.)
# ==========================================
st.subheader("📉 1. Health Disparities: SES Impact on Stage at Diagnosis")
st.caption("Benchmark: Zhu et al. (SEER) shows Low SES patients present with higher rates of Stage IV disease.")

# Calculate percentages for Stage IV by SES
stage_iv_rates = df_filtered[df_filtered['Stage_at_Diagnosis'] == 'IV'].groupby('SES_MHI_Category').size() / df_filtered.groupby('SES_MHI_Category').size() * 100
stage_iv_df = stage_iv_rates.reset_index(name='Stage_IV_Percentage')

col_disp1, col_disp2 = st.columns(2)

with col_disp1:
    fig_stage_ses = px.bar(
        stage_iv_df, 
        x='SES_MHI_Category', 
        y='Stage_IV_Percentage',
        color='SES_MHI_Category',
        title='Stage IV Presentation Rate by SES (%)',
        labels={'SES_MHI_Category': 'Median Household Income', 'Stage_IV_Percentage': '% Stage IV'},
        text_auto='.1f',
        # FIX 1: Enforce Low -> Medium -> High order
        category_orders={"SES_MHI_Category": ses_order} 
    )
    fig_stage_ses.update_layout(showlegend=False, yaxis_title="Percentage (%)")
    st.plotly_chart(fig_stage_ses, use_container_width=True)

with col_disp2:
    fig_stage_pie = px.pie(
        df_filtered, 
        names='Stage_at_Diagnosis', 
        title='Overall Stage Distribution',
        hole=0.4,
        category_orders={"Stage_at_Diagnosis": stage_order}
    )
    st.plotly_chart(fig_stage_pie, use_container_width=True)

# ==========================================
# Module 2: Survival Outcomes (Zhu et al.)
# ==========================================
st.subheader("⏳ 2. Survival Outcomes: The SES Gap")
st.caption("Benchmark: Zhu et al. Cox Regression shows High SES has significantly better Overall Survival (HR 0.877).")

# FIX 2: Change from Boxplot to Kaplan-Meier (Survival Function)
# We use Plotly's ECDF with 'complementary' mode, which plots P(X > x), mathematically identical to KM when uncensored.
fig_surv = px.ecdf(
    df_filtered,
    x='Survival_Months',
    color='SES_MHI_Category',
    ecdfmode='complementary', # This creates the Survival Curve S(t)
    title='Survival Probability by SES (Kaplan-Meier Estimate)',
    labels={'Survival_Months': 'Survival (Months)', 'SES_MHI_Category': 'SES (MHI)'},
    category_orders={"SES_MHI_Category": ses_order}
)
fig_surv.update_layout(
    yaxis_title="Survival Probability",
    template='plotly_white',
    xaxis_title="Time (Months)"
)
st.plotly_chart(fig_surv, use_container_width=True)
st.caption("*Note: Because this synthetic dataset represents complete follow-up (no right-censoring), the empirical survival function plotted here is mathematically identical to a standard Kaplan-Meier estimate.*")

# ==========================================
# Module 3: Guideline Impact on Treatment (Bekaii-Saab)
# ==========================================
st.subheader("💊 3. Clinical Pathways: Guideline Impact on Late-Line Therapy")
st.caption("Benchmark: Bekaii-Saab et al. (Optum) shows 45.3% uptake of Regorafenib flexible dosing post-NCCN guidelines.")

mcr_df = df_filtered[(df_filtered['Stage_at_Diagnosis'] == 'IV') & (df_filtered['Received_Chemo'] == 1)]

col_guide1, col_guide2 = st.columns(2)

with col_guide1:
    if len(mcr_df) > 0:
        flex_rate = mcr_df['Regorafenib_Flexible_Dosing'].mean() * 100
        st.metric("Flexible Dosing Uptake (mCRC)", f"{flex_rate:.1f}%", delta="Target: 45.3% (Bekaii-Saab)")
        
        tx_rates = df_filtered.groupby('Stage_at_Diagnosis')[['Received_Surgery', 'Received_Chemo']].mean() * 100
        fig_tx = px.bar(
            tx_rates.reset_index().melt(id_vars='Stage_at_Diagnosis'),
            x='Stage_at_Diagnosis',
            y='value',
            color='variable',
            barmode='group',
            title='Treatment Receipt Rates by Stage (%)',
            labels={'value': 'Percentage (%)', 'variable': 'Treatment Type'},
            category_orders={"Stage_at_Diagnosis": ['I', 'II', 'III', 'IV']}
        )
        st.plotly_chart(fig_tx, use_container_width=True)
    else:
        st.warning("No Stage IV patients in current filter to calculate Regorafenib metrics.")

with col_guide2:
    fig_loc = px.pie(
        df_filtered, 
        names='Tumor_Location', 
        title='Tumor Location Distribution',
        color_discrete_sequence=px.colors.sequential.YlOrBr_r
    )
    st.plotly_chart(fig_loc, use_container_width=True)

# ==========================================
# Module 4: Economic Burden (Jafari et al.)
# ==========================================
st.subheader("💰 4. Economic Burden: Cost Drivers & Utilization")
st.caption("Benchmark: Jafari et al. Systematic Review identifies Hospitalization (~36%), Drugs (~20%), and Surgery (~16%) as primary drivers.")

col_cost1, col_cost2 = st.columns(2)

with col_cost1:
    total_hosp = df_filtered['Cost_Hospitalization'].sum()
    total_drugs = df_filtered['Cost_Drugs'].sum()
    total_surg = df_filtered['Cost_Surgery'].sum()
    total_other = df_filtered['Total_Direct_Medical_Cost'].sum() - (total_hosp + total_drugs + total_surg)
    
    cost_data = pd.DataFrame({
        'Category': ['Hospitalization', 'Drugs', 'Surgery', 'Other Care'],
        'Total_Cost': [total_hosp, total_drugs, total_surg, total_other]
    })
    
    fig_cost_pie = px.pie(
        cost_data, 
        values='Total_Cost', 
        names='Category', 
        title='Synthetic Cost Drivers vs. Jafari Benchmarks',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.PuBu_r
    )
    fig_cost_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_cost_pie, use_container_width=True)
    
    st.markdown("**Literature Benchmark (Jafari):**")
    st.markdown("- 🏥 Hospitalization: ~36%  \n- 💊 Drugs: ~20%  \n- 🔪 Surgery: ~16%")

with col_cost2:
    # FIX 3: Enforce Stage I -> II -> III -> IV order
    fig_cost_box = px.box(
        df_filtered[df_filtered['Stage_at_Diagnosis'] != 'Unknown'],
        x='Stage_at_Diagnosis',
        y='Total_Direct_Medical_Cost',
        color='Stage_at_Diagnosis',
        title='Total Direct Medical Cost by Stage (Right-Skewed)',
        labels={'Total_Direct_Medical_Cost': 'Total Cost (USD)'},
        category_orders={"Stage_at_Diagnosis": ['I', 'II', 'III', 'IV']}
    )
    fig_cost_box.update_layout(showlegend=False, yaxis_tickformat="$,")
    st.plotly_chart(fig_cost_box, use_container_width=True)

# ==========================================
# Footer & Data Download
# ==========================================
st.divider()
st.subheader("📥 Download V3.0 Tokenized Dataset")

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered V3.0 Dataset (CSV)",
    data=csv,
    file_name='Dataura_V3_Filtered_Evidence_Calibrated.csv',
    mime='text/csv',
)

st.markdown("---")
st.markdown("**Dataura SynthRWE® V3.0** | Evidence-Calibrated Microsimulation Engine")
st.markdown("*Fusing Siegel (Epi), Zhu (SES/Survival), Bekaii-Saab (Treatment), Jafari (Costs). For feasibility testing & model development.*")
