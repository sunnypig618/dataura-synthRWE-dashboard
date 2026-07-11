import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="Dataura SynthRWE - Colon Cancer Sandbox",
    page_icon="🏥",
    layout="wide"
)

# ==========================================
# 标题和介绍
# ==========================================
st.title("🏥 Dataura SynthRWE: Colon Cancer Surgical Oncology Sandbox")
st.markdown("**Synthetic Real-World Evidence Dataset for Feasibility Testing & Study Design**")

st.markdown("""
This dashboard demonstrates a synthetic longitudinal dataset of 10,000 colorectal cancer patients,
mimicking US claims-like data with realistic patient selection patterns, treatment pathways,
and outcomes across robotic-assisted, laparoscopic, and open surgery approaches.
""")

st.divider()

# ==========================================
# 加载数据
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Dataura_SynthRWE_V2_ColonCancer_Microsimulation.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

# 如果数据不存在，提供文件上传选项
if df is None:
    st.warning("📁 Please upload your synthetic dataset CSV file:")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Data loaded successfully!")
    else:
        st.stop()

# ==========================================
# 侧边栏：筛选器
# ==========================================
st.sidebar.header(" Data Filters")

# 手术方式筛选
surgery_options = st.sidebar.multiselect(
    "Select Surgical Approaches:",
    options=df['Surgery_Type'].unique(),
    default=df['Surgery_Type'].unique()
)

# 年龄范围筛选
age_min, age_max = int(df['Age'].min()), int(df['Age'].max())
age_range = st.sidebar.slider(
    "Age Range:",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max)
)

# CCI评分筛选
cci_max = st.sidebar.slider(
    "Maximum CCI Score:",
    min_value=0,
    max_value=int(df['CCI_Score'].max()),
    value=int(df['CCI_Score'].max())
)

# 应用筛选
df_filtered = df[
    (df['Surgery_Type'].isin(surgery_options)) &
    (df['Age'] >= age_range[0]) &
    (df['Age'] <= age_range[1]) &
    (df['CCI_Score'] <= cci_max)
]

# ==========================================
# 关键指标展示 (KPI Cards)
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
# 图表 1：患者分布
# ==========================================
st.subheader(" Patient Distribution by Surgical Approach")

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
# 图表 2：基线特征对比
# ==========================================
st.subheader("📋 Baseline Characteristics by Surgical Approach")

baseline_cols = ['Age', 'CCI_Score', 'COPD', 'CHF', 'Diabetes_Uncomplicated']
baseline_df = df_filtered.groupby('Surgery_Type')[baseline_cols].mean().round(3).reset_index()

baseline_df_transposed = baseline_df.set_index('Surgery_Type').T
baseline_df_transposed.columns.name = 'Surgical Approach'

# 重新排序列
target_order = ['Non-Surgical Management', 'Open', 'Laparoscopic', 'Robotic']
# 只保留存在的列
existing_cols = [col for col in target_order if col in baseline_df_transposed.columns]
baseline_df_transposed = baseline_df_transposed[existing_cols]

st.dataframe(
    baseline_df_transposed,
    use_container_width=True,
    column_config={
        col: st.column_config.NumberColumn(
            col,
            format="%.3f"
        ) for col in baseline_df_transposed.columns
    }
)

st.caption("💡 Higher values are shaded darker. Note the selection bias: Robotic surgery patients are younger and have lower CCI scores.")

# ==========================================
# 图表 3：临床结局对比
# ==========================================
st.subheader(" Clinical Outcomes & Resource Utilization")

outcomes_cols = ['Length_of_Stay_Days', 'Has_30Day_Complication', 'Total_Cost_USD']
outcomes_df = df_filtered.groupby('Surgery_Type')[outcomes_cols].mean().round(2).reset_index()
outcomes_df['Complication_Rate_%'] = outcomes_df['Has_30Day_Complication'] * 100

# 重新排序
outcomes_df_transposed = outcomes_df.set_index('Surgery_Type').T
existing_cols_out = [col for col in target_order if col in outcomes_df_transposed.columns]
outcomes_df_transposed = outcomes_df_transposed[existing_cols_out]

col_out1, col_out2, col_out3 = st.columns(3)

with col_out1:
    st.markdown("#### Average Length of Stay (Days)")
    for col in existing_cols_out:
        st.text(f"{col}: {outcomes_df_transposed.loc['Length_of_Stay_Days', col]} days")

with col_out2:
    st.markdown("#### 30-Day Complication Rate (%)")
    for col in existing_cols_out:
        st.text(f"{col}: {outcomes_df_transposed.loc['Complication_Rate_%', col]}%")

with col_out3:
    st.markdown("#### Average Cost (USD)")
    for col in existing_cols_out:
        cost_val = outcomes_df_transposed.loc['Total_Cost_USD', col]
        st.text(f"{col}: ${cost_val:,.0f}")

# ==========================================
# 图表 4：成本 vs 并发症散点图
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
# 图表 5：LOS 分布箱线图
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
# 图表 6：合并症分析
# ==========================================
st.subheader("🫁 Comorbidity Profile Analysis")

comorbidity_cols = ['COPD', 'CHF', 'Cerebrovascular_Disease', 'Diabetes_Uncomplicated', 'Renal_Disease']
comorbidity_df = df_filtered.groupby('Surgery_Type')[comorbidity_cols].mean().round(3) * 100

# 转置并排序
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
# 数据下载
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
st.markdown("**Dataura SynthRWE** - Synthetic Real-World Evidence Data Engine")
st.markdown("*Generated for educational and feasibility testing purposes. Not for regulatory or clinical decision-making.*")
st.markdown("Seed: 20260711 | Dataset Version: V2.0 Microsimulation")
