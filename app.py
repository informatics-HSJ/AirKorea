import streamlit as st
import pandas as pd
import plotly.express as px

# Data loading and preprocessing function, cached for performance
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('air_quality_data.csv', encoding='utf-8-sig')
    except FileNotFoundError:
        st.error("데이터 파일 'air_quality_data.csv'를 찾을 수 없습니다. 이전 셀에서 데이터를 저장했는지 확인해주세요.")
        return pd.DataFrame() # Return empty DataFrame on error

    df['측정일시'] = pd.to_datetime(df['측정일시'])

    # List of columns that represent measurable air quality values
    measurable_cols = [
        '아황산가스 농도', '일산화탄소 농도', '오존 농도', '이산화질소 농도',
        '미세먼지(PM10) 농도', '미세먼지(PM2.5) 농도'
    ]
    
    # Convert measurable columns to numeric, coercing errors to NaN and filling NaN with 0
    for col in measurable_cols:
        if col in df.columns:
            # Replace '-' with NaN before converting to numeric
            df[col] = df[col].replace('-', pd.NA)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df_renamed_app = load_data()

st.title('에어코리아 대기질 데이터 분석 웹앱')

if df_renamed_app.empty:
    st.warning("데이터가 없어 웹앱을 표시할 수 없습니다. 데이터를 먼저 로드해주세요.")
else:
    # Sidebar for filters
    st.sidebar.header('필터')

    # Select box for sidoName
    # Ensure unique sido names and sort them for better UI
    sido_options = sorted(df_renamed_app['시도명'].unique().tolist())
    selected_sido = st.sidebar.selectbox('시도 선택', sido_options)

    # Select box for measurable item
    measurable_items_all = [ # All possible measurable items based on the context
        '아황산가스 농도', '일산화탄소 농도', '오존 농도', '이산화질소 농도',
        '미세먼지(PM10) 농도', '미세먼지(PM2.5) 농도'
    ]
    # Filter for available and numeric items in the loaded data
    available_items = [item for item in measurable_items_all if item in df_renamed_app.columns and pd.api.types.is_numeric_dtype(df_renamed_app[item])]

    if not available_items:
        st.error("시각화할 수 있는 측정 항목이 없습니다. 데이터프레임 컬럼을 확인해주세요.")
    else:
        selected_item = st.sidebar.selectbox('항목 선택', available_items)

        # Filter data based on selections
        filtered_df = df_renamed_app[df_renamed_app['시도명'] == selected_sido].copy()

        # Group by '측정일시' and calculate mean for the selected item
        # Sort by '측정일시' for correct time series plotting
        daily_avg = filtered_df.groupby('측정일시')[selected_item].mean().reset_index().sort_values(by='측정일시')

        if daily_avg.empty:
            st.warning(f"{selected_sido}에 대한 {selected_item} 데이터가 없습니다. 다른 시도나 항목을 선택해보세요.")
        else:
            # Plotly Express time series visualization
            fig = px.line(daily_avg, x='측정일시', y=selected_item,
                          title=f'{selected_sido} {selected_item} 시간별 변화',
                          labels={'측정일시': '측정일시', selected_item: f'평균 {selected_item}'})

            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig)

            # Display descriptive statistics
            st.subheader(f'{selected_sido} {selected_item} 요약 통계:')
            st.write(daily_avg[selected_item].describe())
