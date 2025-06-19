import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 직접 지정
plt.rcParams['axes.unicode_minus'] = False

# 직접 경로 설정 (Streamlit Cloud는 상대경로 사용)
font_path = "fonts/NanumGothic.ttf"
font_name = fm.FontProperties(fname=font_path).get_name()
plt.rcParams['font.family'] = font_name


st.set_page_config(page_title="매출 분석 대시보드", layout="wide")
st.title("💊 제약 매출 분석 대시보드")

# 한글 폰트 설정
# GitHub 업로드된 NanumGothic.ttf 폰트 직접 경로 지정
font_path = "fonts/NanumGothic.ttf"
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

font_path = fm.findSystemFonts(fontpaths=None, fontext='ttf')
korean_fonts = [f for f in font_path if 'malgun' in f.lower() or 'nanum' in f.lower()]
if korean_fonts:
    plt.rcParams['font.family'] = fm.FontProperties(fname=korean_fonts[0]).get_name()
plt.rcParams['axes.unicode_minus'] = False

uploaded_file = st.file_uploader("📁 매출 데이터 CSV 파일 업로드", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['기준년월'] = pd.to_datetime(df['기준년월'].astype(str), format='%Y%m')
    df['년월'] = df['기준년월'].dt.to_period('M')
    df['분기'] = df['기준년월'].dt.to_period('Q')

    df_main = df[~df['품목명'].str.contains('한미플루', na=False)]
    df_hanmi = df[df['품목명'].str.contains('한미플루', na=False)]

    total_sales = df_main['총매출'].sum()
    total_clients = df_main['거래처명'].nunique()
    total_products = df_main['품목명'].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("총 매출", f"{total_sales:,.0f} 원")
    col2.metric("거래처 수", total_clients)
    col3.metric("품목 수", total_products)

    st.subheader("📊 월별 총매출 추이")
    monthly_trend = df_main.groupby('기준년월')['총매출'].sum().reset_index()
    fig, ax = plt.subplots()
    sns.lineplot(data=monthly_trend, x='기준년월', y='총매출', ax=ax, marker='o')
    ax.set_ylabel("총매출")
    ax.set_xlabel("기준년월")
    st.pyplot(fig)

    st.subheader("🏢 거래처별 총매출")
    with st.expander("필터"):
        col1, col2 = st.columns(2)
        with col1:
            selected_rep_total = st.multiselect("담당자", options=df_main['담당자'].unique(), key="rep_total")
        with col2:
            selected_months_total = st.multiselect("기준년월", options=df_main['기준년월'].dt.strftime('%Y-%m').unique(), key="month_total")

    df_total_filtered = df_main.copy()
    if selected_rep_total:
        df_total_filtered = df_total_filtered[df_total_filtered['담당자'].isin(selected_rep_total)]
    if selected_months_total:
        selected_dt = pd.to_datetime(selected_months_total, format='%Y-%m')
        df_total_filtered = df_total_filtered[df_total_filtered['기준년월'].isin(selected_dt)]

    client_sales = df_total_filtered.groupby('거래처명')['총매출'].sum().reset_index().sort_values(by='총매출', ascending=False)
    st.dataframe(client_sales)

    st.subheader("🏷️ 거래처 매출 구간 분석 (월/분기 선택)")
    time_filter = st.radio("분석 단위 선택", ["월별", "분기별"])

    if time_filter == "월별":
        selected_month = st.selectbox("기준년월 선택", sorted(df['년월'].unique()), key="월선택")
        subset = df_main[df_main['년월'] == selected_month]
        title_unit = f"{selected_month}"
    else:
        selected_quarter = st.selectbox("기준분기 선택", sorted(df['분기'].unique()), key="분기선택")
        subset = df_main[df_main['분기'] == selected_quarter]
        title_unit = f"{selected_quarter} 평균"

    if time_filter == "월별":
        avg_df = subset.groupby('거래처명')['총매출'].sum().reset_index()
    else:
        month_count = subset['기준년월'].dt.to_period('M').nunique()
        avg_df = subset.groupby('거래처명')['총매출'].sum().div(month_count).reset_index()

        avg_df = avg_df[avg_df['총매출'] > 0]
        bins = [0, 300000, 1000000, 3000000, 5000000, 10000000, 20000000, 30000000, np.inf]
        labels = ['0~30만원', '30~100만원', '100~300만원', '300~500만원', '500~1000만원', '1000~2000만원', '2000~3000만원', '3000만원 이상']
        avg_df['매출구간'] = pd.cut(avg_df['총매출'], bins=bins, labels=labels, right=True)
        section_count = avg_df['매출구간'].value_counts(sort=False).reindex(labels, fill_value=0)

        fig4, ax4 = plt.subplots()
        sns.barplot(x=section_count.index, y=section_count.values, ax=ax4)
        ax4.set_title(f"{title_unit} 거래처 매출 구간 분포")
        ax4.set_ylabel("거래처 수")
        ax4.bar_label(ax4.containers[0])
        plt.xticks(rotation=45)
        st.pyplot(fig4)

    with st.expander("🗂️ 해당 구간 거래처 목록 보기"):
        for label in labels:
            st.markdown(f"**{label}**")
            matched = avg_df[avg_df['매출구간'] == label]
            st.dataframe(matched[['거래처명', '총매출']].sort_values(by='총매출', ascending=False))

    st.subheader("👤 담당자 매출 구간 분석 (월/분기 선택)")
    if time_filter == "월별":
        rep_df = subset.groupby('담당자')['총매출'].sum().reset_index()
    else:
        month_count = subset['기준년월'].dt.to_period('M').nunique()
        rep_df = subset.groupby('담당자')['총매출'].sum().div(month_count).reset_index()

        rep_df = rep_df[rep_df['총매출'] > 0]
        rep_bins = [0, 80000000, 110000000, 140000000, 170000000, 200000000, np.inf]
        rep_labels = ['~0.8억', '0.8~1.1억', '1.1~1.4억', '1.4~1.7억', '1.7~2.0억', '2.0억 이상']
        rep_df['매출구간'] = pd.cut(rep_df['총매출'], bins=rep_bins, labels=rep_labels, right=True)
        rep_section = rep_df['매출구간'].value_counts(sort=False).reindex(rep_labels, fill_value=0)

        fig_rep, ax_rep = plt.subplots()
        sns.barplot(x=rep_section.index, y=rep_section.values, ax=ax_rep)
        ax_rep.set_title(f"{title_unit} 담당자 매출 구간 분포")
        ax_rep.set_xlabel("매출구간")
        ax_rep.set_ylabel("담당자 수")
        ax_rep.bar_label(ax_rep.containers[0])
        plt.xticks(rotation=45)
        st.pyplot(fig_rep)

    with st.expander("🗂️ 해당 구간 담당자 목록 보기"):
        for label in rep_labels:
            st.markdown(f"**{label}**")
            matched = rep_df[rep_df['매출구간'] == label]
            st.dataframe(matched[['담당자', '총매출']].sort_values(by='총매출', ascending=False))

    st.subheader("💉 한미플루 매출 현황")
    if not df_hanmi.empty:
        col1, col2 = st.columns(2)
        with col1:
            selected_hanmi_rep = st.multiselect("담당자 선택", options=df_hanmi['담당자'].unique(), key="hanmi_rep")
        with col2:
            selected_hanmi_month = st.multiselect("기준년월 선택", options=df_hanmi['기준년월'].dt.strftime('%Y-%m').unique(), key="hanmi_month")

        filtered_hanmi = df_hanmi.copy()
        if selected_hanmi_rep:
            filtered_hanmi = filtered_hanmi[filtered_hanmi['담당자'].isin(selected_hanmi_rep)]
        if selected_hanmi_month:
            selected_dt = pd.to_datetime(selected_hanmi_month, format='%Y-%m')
            filtered_hanmi = filtered_hanmi[filtered_hanmi['기준년월'].isin(selected_dt)]

        if not filtered_hanmi.empty:
            hanmi_summary = filtered_hanmi.groupby(['기준년월', '담당자'])['총매출'].sum().reset_index()
            st.dataframe(hanmi_summary.sort_values(by='기준년월'))
        else:
        else:
            st.warning("선택한 조건에 해당하는 한미플루 매출 데이터가 없습니다.")
            st.info("한미플루 매출 데이터가 없습니다.")

# 🔍 상세 매출 필터 분석
st.subheader("🔍 상세 매출 필터 분석")

with st.expander("필터 조건 설정"):
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_rep = st.multiselect("담당자", options=df['담당자'].unique(), key="rep_filter")
        selected_group = st.multiselect("품목군", options=df['품목군'].unique() if '품목군' in df.columns else [], key="group_filter")
    with col2:
        selected_client = st.multiselect("거래처명", options=df['거래처명'].unique(), key="client_filter")
        selected_product = st.multiselect("품목명", options=df['품목명'].unique(), key="product_filter")
    with col3:
        selected_months = st.multiselect("기준년월", options=df['기준년월'].dt.strftime('%Y-%m').unique(), key="month_filter")

# 필터 적용
filtered_df = df.copy()
if selected_rep:
    filtered_df = filtered_df[filtered_df['담당자'].isin(selected_rep)]
if selected_client:
    filtered_df = filtered_df[filtered_df['거래처명'].isin(selected_client)]
if selected_group:
    filtered_df = filtered_df[filtered_df['품목군'].isin(selected_group)]
if selected_product:
    filtered_df = filtered_df[filtered_df['품목명'].isin(selected_product)]
if selected_months:
    filtered_df = filtered_df[filtered_df['기준년월'].dt.strftime('%Y-%m').isin(selected_months)]

# 테이블 출력
display_cols = ['기준년월', '담당자', '거래처명', '품목군', '품목명', '총수량', '총매출']
existing_cols = [col for col in display_cols if col in filtered_df.columns]

if not filtered_df.empty:
    st.dataframe(filtered_df[existing_cols])
else:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

# 📊 월별 매출 추이 (필터 포함)
st.subheader("📊 월별 매출 추이")

with st.expander("월별 매출 그래프 필터"):
    col1, col2, col3 = st.columns(3)
    with col1:
        graph_filter_type = st.selectbox("기준 선택", ["품목명", "거래처명", "담당자"])
    with col2:
        selected_groups = st.multiselect("품목군", options=df['품목군'].dropna().unique(), key="graph_group")
        selected_products = st.multiselect("품목명", options=df['품목명'].dropna().unique(), key="graph_product")
    with col3:
        graph_selected_months = st.multiselect("기준년월 선택", options=df['기준년월'].dt.strftime('%Y-%m').unique(), key="graph_month")

# 필터 적용
graph_df = df.copy()
if selected_groups:
    graph_df = graph_df[graph_df['품목군'].isin(selected_groups)]
if selected_products:
    graph_df = graph_df[graph_df['품목명'].isin(selected_products)]
if graph_selected_months:
    graph_df = graph_df[graph_df['기준년월'].dt.strftime('%Y-%m').isin(graph_selected_months)]

if not graph_df.empty:
    graph_df['기준년월_str'] = graph_df['기준년월'].dt.strftime('%Y-%m')

    label_col = graph_filter_type
    grouped = (
        graph_df.groupby(['기준년월_str', label_col])['총매출']
        .sum().reset_index().rename(columns={label_col: '구분'})
    )

    total_monthly = (
        graph_df.groupby('기준년월_str')['총매출']
        .sum().reset_index()
    )
    total_monthly['구분'] = '총합'

    plot_data = pd.concat([grouped, total_monthly], ignore_index=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=plot_data, x='기준년월_str', y='총매출', hue='구분', marker='o', ax=ax)
    ax.set_title(f"📈 {graph_filter_type} 기준 월별 매출 추이 (총합 포함)")
    ax.set_xlabel("기준년월")
    ax.set_ylabel("총매출")
    ax.legend(title="구분", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("선택한 조건에 해당하는 데이터가 없습니다.")



    # 자연어 질문 예시
    st.subheader("🧠 자연어 질문 예시")
    question = st.text_input("질문 입력 (예: '3월 매출이 가장 높은 거래처는?', '아모잘탄 매출은 얼마야?')")
    if question:
        q = question.replace(' ', '')
        if '3월' in q and '거래처' in q and '높' in q:
            top = df[df['기준년월'].dt.month == 3].groupby('거래처명')['총매출'].sum().idxmax()
            st.success(f"3월 매출이 가장 높은 거래처는 **{top}** 입니다.")
        elif '아모잘탄' in q and '매출' in q:
            amount = df[df['품목명'].str.contains('아모잘탄', na=False)]['총매출'].sum()
            st.success(f"아모잘탄 매출은 총 {amount:,.0f}원입니다.")
        elif '거래처' in q and '가장많이' in q:
            most = df.groupby('거래처명')['총매출'].sum().idxmax()
            st.success(f"가장 많이 판매된 거래처는 **{most}** 입니다.")
        elif '품목' in q and '가장많이' in q:
            most_item = df.groupby('품목명')['총매출'].sum().idxmax()
            st.success(f"가장 많이 팔린 품목은 **{most_item}** 입니다.")
        elif '총매출' in q and '합계' in q:
            st.success(f"전체 총매출은 {df['총매출'].sum():,.0f}원입니다.")
        elif '담당자' in q and '매출' in q:
            top_rep = df.groupby('담당자')['총매출'].sum().idxmax()
            top_rep_amt = df.groupby('담당자')['총매출'].sum().max()
            st.success(f"가장 높은 매출을 기록한 담당자는 **{top_rep}**이며, 총 {top_rep_amt:,.0f}원입니다.")
        else:
        st.warning("죄송합니다. 이 질문은 아직 지원되지 않아요.")
   
   
    # 다운로드
    st.subheader("⬇ 분석 결과 다운로드")
    export_df = filtered_df[existing_cols] if 'filtered_df' in locals() and not filtered_df.empty else pd.DataFrame(columns=display_cols)
    export_csv = export_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("엑셀 다운로드 (CSV 형식)", export_csv, file_name='filtered_sales.csv', mime='text/csv')
