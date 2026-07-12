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

# Define strict categorical orders
ses_order = ['Low ($0-54k)', 'Medium ($55k-74k)', 'High ($75k+)']
stage_order = ['I', 'II', 'III', 'IV', 'Unknown']

ses_options = st.sidebar.multiselect(
    "Socioeconomic Status (MHI):",
    options=ses_order,
    default=ses_order
)

stage_options = st.sidebar.multiselect(
    "Stage at Diagnosis:",
    options=stage_order,
    default=stage_order
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

if len(df_filtered) == 0:
    st.error("No data matches the current filters. Please adjust your selection.")
    st.stop()

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
    # Calculate 5-year survival rate for the KPI card
    surv_5yr = (df_filtered['Survival_Months'] >= 60).mean() * 100
    st.metric("5-Year Survival Rate", f"{surv_5yr:.1f}%")
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
stage_counts = df_filtered.groupby(['SES_MHI_Category', 'Stage_at_Diagnosis']).size().unstack(fill_value=0)
if 'IV' in stage_counts.columns:
    stage_iv_df = (stage_counts['IV'] / stage_counts.sum(axis=1) * 100).reset_index()
    stage_iv_df.columns = ['SES_MHI_Category', 'Stage_IV_Percentage']
else:
    stage_iv_df = pd.DataFrame({'SES_MHI_Category': ses_order, 'Stage_IV_Percentage': 0.0})

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
# Module 2: Survival Outcomes (Zhu et al.) - 5-YEAR VIEW
# ==========================================
st.subheader("⏳ 2. Survival Outcomes: The SES Gap (5-Year View)")
st.caption("Benchmark: Zhu et al. Cox Regression shows High SES has significantly better Overall Survival (HR 0.877).")

# Draw a robust Kaplan-Meier step chart capped at 60 months
fig_surv = go.Figure()
colors_map = {'Low ($0-54k)': '#EF553B', 'Medium ($55k-74k)': '#636EFA', 'High ($75k+)': '#00CC96'}

for ses in ses_order:
    original_df = df_filtered[df_filtered['SES_MHI_Category'] == ses]['Survival_Months'].dropna()
    if len(original_df) == 0: continue
    
    # Cap survival times at 60 months (5 years) to focus on meaningful early differences
    sub_df = original_df.clip(upper=60)
    
    n = len(sub_df)
    unique_times = np.unique(sub_df)
    # Calculate survival probability at each time point
    survival_probs = [(n - np.sum(sub_df <= t)) / n for t in unique_times]
    
    fig_surv.add_trace(go.Scatter(
        x=unique_times,
        y=survival_probs,
        mode='lines',
        name=ses,
        line=dict(shape='hv', color=colors_map.get(ses, 'gray'), width=2),
        hovertemplate=f'{ses}<br>Time: %{x:.0f} months<br>Survival: %{y:.1%}<extra></extra>'
    ))

fig_surv.update_layout(
    title='5-Year Survival Probability by SES',
    xaxis_title='Time (Months)',
    yaxis_title='Survival Probability',
    template='plotly_white',
    # Limit X-axis to 60 months, with ticks every 12 months (1 year) for a clean look
    xaxis=dict(range=[0, 60], dtick=12), 
    yaxis=dict(range=[0, 1.05]),
    legend_title='SES (MHI)'
)
st.plotly_chart(fig_surv, use_container_width=True)
st.caption("*Note: Curves are capped at 60 months (5 years) to highlight early survival disparities. Step curves represent the empirical survival function.*")

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
            category_orders={"Stage_at_Diagnosis": stage_order}
        )
        st.plotly_chart(fig_tx, use_container_width=True)
    else:
        st.warning("No Stage IV patients in current filter to calculate Regorafenib metrics.")

with col_guide2:
    fig_loc = px.pie(
        df_filtered, 
        names='Tumor_Location', 
        title='Tumor Location Distribution'
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
        hole=0.4
    )
    fig_cost_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_cost_pie, use_container_width=True)
    
    st.markdown("**Literature Benchmark (Jafari):**")
    st.markdown("- 🏥 Hospitalization: ~36%  \n- 💊 Drugs: ~20%  \n- 🔪 Surgery: ~16%")

with col_cost2:
    fig_cost_box = px.box(
        df_filtered,
        x='Stage_at_Diagnosis',
        y='Total_Direct_Medical_Cost',
        color='Stage_at_Diagnosis',
        title='Total Direct Medical Cost by Stage (Right-Skewed)',
        labels={'Total_Direct_Medical_Cost': 'Total Cost (USD)'},
        category_orders={"Stage_at_Diagnosis": stage_order}
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
