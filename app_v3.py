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
    surv_5yr = (df_filtered['Survival_Months'] >= 60).mean() * 100
    st.metric("5-Year Survival Rate", f"{surv_5yr:.1f}%")
with col4:
    avg_cost = df_filtered['Total_Direct_Medical_Cost'].mean()
    st.metric("Avg Direct Cost", f"${avg_cost:,.0f}")

st.divider()

# ==========================================
# Module 1: SES Disparities + Colon Anatomy Map
# ==========================================
st.subheader("📉 1. Health Disparities & Tumor Anatomy")
st.caption("Left: SES impact on Stage IV presentation (Zhu et al.). Right: Anatomical tumor location distribution (Siegel et al., 2026).")

# --- Calculate SES Stage IV rates ---
stage_counts = df_filtered.groupby(['SES_MHI_Category', 'Stage_at_Diagnosis']).size().unstack(fill_value=0)
if 'IV' in stage_counts.columns:
    stage_iv_df = (stage_counts['IV'] / stage_counts.sum(axis=1) * 100).reset_index()
    stage_iv_df.columns = ['SES_MHI_Category', 'Stage_IV_Percentage']
else:
    stage_iv_df = pd.DataFrame({'SES_MHI_Category': ses_order, 'Stage_IV_Percentage': 0.0})

col_disp1, col_disp2 = st.columns(2)

# --- LEFT: SES Bar Chart ---
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

# --- RIGHT: Colon Anatomy Map (NEW!) ---
with col_disp2:
    # Calculate actual tumor location distribution from filtered data
    loc_counts = df_filtered['Tumor_Location'].value_counts(normalize=True) * 100
    
    # Map to anatomical categories (Siegel 2026 benchmarks)
    proximal_pct = loc_counts.get('Colon', 0) * 0.55  # Approximate proximal share
    distal_pct = loc_counts.get('Colon', 0) * 0.45    # Approximate distal share
    rectal_pct = loc_counts.get('Rectum', 0)
    rectosigmoid_pct = loc_counts.get('Rectosigmoid', 0)
    
    # Use Siegel 2026 benchmarks as reference (per 100,000 incidence rates)
    # Proximal: 13.3, Distal: 8.7, Rectum: 11.1 → Total: 33.1
    # Proximal% = 13.3/33.1 = 40.2%, Distal% = 8.7/33.1 = 26.3%, Rectum% = 11.1/33.1 = 33.5%
    siegel_proximal = 40.2
    siegel_distal = 26.3
    siegel_rectum = 33.5
    
    # Build colon anatomy map using Plotly
    fig_colon = go.Figure()
    
    # Draw colon outline (anatomically-inspired shape)
    # Path: cecum (bottom-right) → ascending → hepatic flexure → transverse → splenic flexure → descending → sigmoid → rectum (bottom)
    t = np.linspace(0, 1, 40)
    
    # Ascending colon + hepatic flexure
    x_asc = 7.2 + 0.4 * np.sin(t * np.pi / 2)
    y_asc = 1.5 + 5.5 * t
    
    # Transverse colon
    x_trans = 7.2 - 4.4 * t
    y_trans = 7.0 + 0.3 * np.sin(t * np.pi)
    
    # Descending colon + splenic flexure
    x_desc = 2.8 - 0.4 * np.sin(t * np.pi / 2)
    y_desc = 7.0 - 5.5 * t
    
    # Sigmoid colon (S-curve)
    t_sig = np.linspace(0, 1, 20)
    x_sig = 2.4 + 0.7 * np.sin(t_sig * np.pi * 1.8)
    y_sig = 1.5 - 1.2 * t_sig
    
    # Rectum
    x_rect = [2.4, 2.4, 2.4]
    y_rect = [0.3, -0.3, -0.9]
    
    all_x = np.concatenate([x_asc, x_trans, x_desc, x_sig, x_rect])
    all_y = np.concatenate([y_asc, y_trans, y_desc, y_sig, y_rect])
    
    # Draw colon body
    fig_colon.add_trace(go.Scatter(
        x=all_x, y=all_y,
        mode='lines',
        line=dict(color='#D2691E', width=30, shape='spline'),
        name='Colon Anatomy',
        hoverinfo='skip'
    ))
    
    # Draw haustra (colon pouches) for anatomical detail
    haustra_x = all_x[::4]
    haustra_y = all_y[::4]
    fig_colon.add_trace(go.Scatter(
        x=haustra_x, y=haustra_y,
        mode='markers',
        marker=dict(size=10, color='#8B4513', opacity=0.4),
        hoverinfo='skip'
    ))
    
    # Highlight Proximal Colon (ascending + right transverse) - GREEN
    prox_x = [7.2, 7.3, 7.2, 6.5, 6, 5.5, 5, 4.5]
    prox_y = [2.5, 3.5, 4.5, 5.5, 6.5, 7, 7.2, 7.1]
    fig_colon.add_trace(go.Scatter(
        x=prox_x, y=prox_y,
        mode='markers',
        marker=dict(size=55, color='#2E8B57', opacity=0.7, line=dict(width=2, color='#1a5235')),
        name=f'Proximal Colon ({siegel_proximal:.1f}%)',
        hoverinfo='name'
    ))
    
    # Highlight Distal Colon (left transverse + descending + sigmoid) - BLUE
    dist_x = [4, 3.5, 3, 2.8, 2.6, 2.5, 2.4]
    dist_y = [7, 6.5, 6, 5, 4, 3, 2]
    fig_colon.add_trace(go.Scatter(
        x=dist_x, y=dist_y,
        mode='markers',
        marker=dict(size=55, color='#4682B4', opacity=0.7, line=dict(width=2, color='#2c5270')),
        name=f'Distal Colon ({siegel_distal:.1f}%)',
        hoverinfo='name'
    ))
    
    # Highlight Rectum - ORANGE
    fig_colon.add_trace(go.Scatter(
        x=[2.4, 2.4, 2.4], y=[0.3, -0.3, -0.9],
        mode='markers',
        marker=dict(size=50, color='#CD853F', opacity=0.8, line=dict(width=2, color='#8b5a2b')),
        name=f'Rectum ({siegel_rectum:.1f}%)',
        hoverinfo='name'
    ))
    
    # Add percentage annotations with arrows
    fig_colon.add_annotation(
        x=6.2, y=4.8,
        text=f"<b>Proximal Colon</b><br>{siegel_proximal:.1f}%<br><i>13.3 per 100k</i>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#2E8B57',
        font=dict(size=11, color='#1a5235', family='Arial'),
        bgcolor='rgba(46, 139, 87, 0.12)', bordercolor='#2E8B57', borderwidth=1, borderpad=8,
        ax=50, ay=-35
    )
    
    fig_colon.add_annotation(
        x=3.8, y=4.8,
        text=f"<b>Distal Colon</b><br>{siegel_distal:.1f}%<br><i>8.7 per 100k</i>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#4682B4',
        font=dict(size=11, color='#2c5270', family='Arial'),
        bgcolor='rgba(70, 130, 180, 0.12)', bordercolor='#4682B4', borderwidth=1, borderpad=8,
        ax=-50, ay=-35
    )
    
    fig_colon.add_annotation(
        x=0.6, y=-0.5,
        text=f"<b>Rectum</b><br>{siegel_rectum:.1f}%<br><i>11.1 per 100k</i>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#CD853F',
        font=dict(size=11, color='#8b5a2b', family='Arial'),
        bgcolor='rgba(205, 133, 63, 0.12)', bordercolor='#CD853F', borderwidth=1, borderpad=8,
        ax=35, ay=25
    )
    
    # Add anatomical landmark labels
    fig_colon.add_annotation(x=8.0, y=1.5, text="Cecum", showarrow=False, font=dict(size=9, color='gray', family='Arial'))
    fig_colon.add_annotation(x=8.0, y=7.0, text="Hepatic Flexure", showarrow=False, font=dict(size=9, color='gray', family='Arial'))
    fig_colon.add_annotation(x=1.8, y=7.3, text="Splenic Flexure", showarrow=False, font=dict(size=9, color='gray', family='Arial'))
    fig_colon.add_annotation(x=1.0, y=1.8, text="Sigmoid", showarrow=False, font=dict(size=9, color='gray', family='Arial'))
    fig_colon.add_annotation(x=1.0, y=-0.5, text="Rectum", showarrow=False, font=dict(size=9, color='gray', family='Arial'))
    
    fig_colon.update_layout(
        title='<b>Tumor Location Distribution</b><br><sup>Siegel et al., 2026 | US Incidence per 100,000</sup>',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 9.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2, 9]),
        plot_bgcolor='white',
        height=620,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5, font=dict(size=10))
    )
    
    st.plotly_chart(fig_colon, use_container_width=True)

# ==========================================
# Module 2: Survival Outcomes (5-Year KM)
# ==========================================
st.subheader("⏳ 2. Survival Outcomes: The SES Gap (5-Year View)")
st.caption("Benchmark: Zhu et al. Cox Regression shows High SES has significantly better Overall Survival (HR 0.877).")

fig_surv = go.Figure()
colors_map = {'Low ($0-54k)': '#EF553B', 'Medium ($55k-74k)': '#636EFA', 'High ($75k+)': '#00CC96'}

for ses in ses_order:
    sub_df = df_filtered[df_filtered['SES_MHI_Category'] == ses]['Survival_Months'].dropna()
    if len(sub_df) == 0: continue
    
    sub_df = sub_df.clip(upper=60)
    n = len(sub_df)
    unique_times = np.unique(sub_df)
    survival_probs = [(n - np.sum(sub_df <= t)) / n for t in unique_times]
    
    hover_text = ses + '<br>Time: %{x:.0f} months<br>Survival: %{y:.1%}<extra></extra>'
    
    fig_surv.add_trace(go.Scatter(
        x=unique_times,
        y=survival_probs,
        mode='lines',
        name=ses,
        line=dict(shape='hv', color=colors_map.get(ses, 'gray'), width=2),
        hovertemplate=hover_text
    ))

fig_surv.update_layout(
    title='5-Year Survival Probability by SES',
    xaxis_title='Time (Months)',
    yaxis_title='Survival Probability',
    template='plotly_white',
    xaxis=dict(range=[0, 60], dtick=12), 
    yaxis=dict(range=[0, 1.05]),
    legend_title='SES (MHI)'
)
st.plotly_chart(fig_surv, use_container_width=True)
st.caption("*Note: Curves are capped at 60 months (5 years) to highlight early survival disparities. Step curves represent the empirical survival function.*")

# ==========================================
# Module 3: Guideline Impact on Treatment
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
    # Show actual tumor location distribution from filtered data as a simple bar chart
    loc_dist = df_filtered['Tumor_Location'].value_counts(normalize=True).reset_index()
    loc_dist.columns = ['Location', 'Percentage']
    loc_dist['Percentage'] = loc_dist['Percentage'] * 100
    
    fig_loc = px.bar(
        loc_dist,
        x='Location',
        y='Percentage',
        color='Location',
        title='Tumor Location Distribution (Filtered Cohort)',
        labels={'Percentage': 'Percentage (%)', 'Location': 'Tumor Location'},
        text_auto='.1f'
    )
    fig_loc.update_layout(showlegend=False)
    st.plotly_chart(fig_loc, use_container_width=True)

# ==========================================
# Module 4: Economic Burden
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
st.subheader(" Download V3.0 Tokenized Dataset")

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
