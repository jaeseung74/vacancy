import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# --------------------------------------------------
# Streamlit 앱 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="역세권 청년주택 공공임대 공실 현황",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 역세권 청년주택 공공임대 공실 현황")
st.write(
    "공공임대 공급호수와 공실의 관계를 산포도로 확인할 수 있습니다."
)


# --------------------------------------------------
# 서울열린데이터광장 API 호출 함수
# --------------------------------------------------
@st.cache_data(ttl=3600)
def load_data(api_key):
    """
    서울열린데이터광장 API에서 데이터를 불러옵니다.

    ttl=3600은 같은 데이터를 1시간 동안 저장하여
    불필요한 API 재호출을 줄이는 설정입니다.
    """

    service_name = "tbYgmnPublicRntHouse"

    # 전체 데이터가 1,000건 이하이므로 1~1000 범위로 요청합니다.
    url = (
        f"http://openapi.seoul.go.kr:8088/"
        f"{api_key}/json/{service_name}/1/1000/"
    )

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        raise RuntimeError(
            "서울열린데이터광장 서버에 연결하지 못했습니다."
        ) from error

    except ValueError as error:
        raise RuntimeError(
            "API 응답을 JSON 형식으로 읽지 못했습니다."
        ) from error

    # 인증키 오류 등이 발생하면 faultInfo가 반환될 수 있습니다.
    if "faultInfo" in data:
        fault_info = data["faultInfo"]

        if isinstance(fault_info, dict):
            message = (
                fault_info.get("message")
                or fault_info.get("errorMessage")
                or "API 요청 중 오류가 발생했습니다."
            )
        else:
            message = "API 요청 중 오류가 발생했습니다."

        raise RuntimeError(message)

    service_data = data.get(service_name)

    if not isinstance(service_data, dict):
        raise RuntimeError(
            "API 응답에서 공공임대 공실 데이터를 찾지 못했습니다."
        )

    # API 처리 결과를 확인합니다.
    result = service_data.get("RESULT", {})
    result_code = result.get("CODE", "")
    result_message = result.get("MESSAGE", "")

    if result_code != "INFO-000":
        raise RuntimeError(
            f"{result_message} ({result_code})"
        )

    rows = service_data.get("row", [])

    # 데이터가 한 건일 경우에도 리스트 형식으로 맞춥니다.
    if isinstance(rows, dict):
        rows = [rows]

    return rows


# --------------------------------------------------
# Streamlit Secrets에서 인증키 불러오기
# --------------------------------------------------
try:
    seoul_key = st.secrets["SEOUL_KEY"]

except (KeyError, FileNotFoundError):
    st.error(
        "Streamlit 비밀 금고에 SEOUL_KEY가 없습니다. "
        "Streamlit Cloud의 Secrets 설정을 확인해 주세요."
    )
    st.stop()


# --------------------------------------------------
# API 데이터 불러오기
# --------------------------------------------------
try:
    with st.spinner("공공임대 공실 데이터를 불러오는 중입니다..."):
        rows = load_data(seoul_key)

except RuntimeError as error:
    st.error(str(error))
    st.stop()


if not rows:
    st.info("표시할 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# JSON 데이터를 데이터프레임으로 변환
# --------------------------------------------------
df = pd.DataFrame(rows)

required_columns = {
    "BIZ_TRGT",
    "RENT_SPLY_NO",
    "EMPT_RM",
    "EMPT_RM_RT",
}

if not required_columns.issubset(df.columns):
    st.error("API 응답에 그래프 작성에 필요한 항목이 없습니다.")
    st.stop()


# --------------------------------------------------
# 숫자 데이터 정리
# --------------------------------------------------
# 공공임대 공급호수를 숫자로 변환합니다.
df["RENT_SPLY_NO"] = pd.to_numeric(
    df["RENT_SPLY_NO"],
    errors="coerce",
)

# 공실 값이 비어 있으면 0으로 처리합니다.
df["EMPT_RM"] = pd.to_numeric(
    df["EMPT_RM"],
    errors="coerce",
).fillna(0)

# 공실률 값이 비어 있으면 0으로 처리합니다.
df["EMPT_RM_RT"] = pd.to_numeric(
    df["EMPT_RM_RT"],
    errors="coerce",
).fillna(0)

# 사업대상지 또는 공급호수가 없는 행은 제외합니다.
df = df.dropna(
    subset=["BIZ_TRGT", "RENT_SPLY_NO"]
).copy()

if df.empty:
    st.info("산포도에 표시할 수 있는 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 공실률을 백분율 문자로 변환
# --------------------------------------------------
df["공실률"] = df["EMPT_RM_RT"].apply(
    lambda value: f"{value * 100:.1f}%"
)

# 그래프의 각 점에 표시할 라벨을 만듭니다.
df["라벨"] = (
    df["BIZ_TRGT"].astype(str)
    + "<br>공실률 "
    + df["공실률"]
)


# --------------------------------------------------
# 주요 지표 표시
# --------------------------------------------------
total_supply = int(df["RENT_SPLY_NO"].sum())
total_vacancy = int(df["EMPT_RM"].sum())

if total_supply > 0:
    total_vacancy_rate = total_vacancy / total_supply * 100
else:
    total_vacancy_rate = 0


col1, col2, col3 = st.columns(3)

col1.metric(
    "사업대상지 수",
    f"{len(df):,}곳",
)

col2.metric(
    "전체 공공임대 공급호수",
    f"{total_supply:,}호",
)

col3.metric(
    "전체 공실률",
    f"{total_vacancy_rate:.1f}%",
)


# --------------------------------------------------
# Plotly 산포도 작성
# --------------------------------------------------
figure = px.scatter(
    df,
    x="RENT_SPLY_NO",
    y="EMPT_RM",
    text="라벨",
    hover_name="BIZ_TRGT",
    hover_data={
        "RENT_SPLY_NO": ":,.0f",
        "EMPT_RM": ":,.0f",
        "EMPT_RM_RT": False,
        "공실률": True,
        "라벨": False,
    },
    labels={
        "RENT_SPLY_NO": "공공임대 공급호수",
        "EMPT_RM": "공실",
        "BIZ_TRGT": "사업대상지",
        "공실률": "공실률",
    },
    title="공공임대 공급호수와 공실의 관계",
)

# 점의 크기와 투명도를 설정합니다.
figure.update_traces(
    marker={
        "size": 11,
        "opacity": 0.75,
        "line": {
            "width": 1,
            "color": "black",
        },
    },
    textposition="top center",
    cliponaxis=False,
)

figure.update_layout(
    height=750,
    xaxis_title="공공임대 공급호수",
    yaxis_title="공실",
    margin={
        "l": 30,
        "r": 30,
        "t": 80,
        "b": 30,
    },
)

figure.update_xaxes(
    rangemode="tozero",
    tickformat=",",
)

figure.update_yaxes(
    rangemode="tozero",
    tickformat=",",
)

st.plotly_chart(
    figure,
    use_container_width=True,
)


# --------------------------------------------------
# 원본 데이터 표
# --------------------------------------------------
with st.expander("공공임대 공실 데이터 표 보기"):
    display_df = df[
        [
            "BIZ_TRGT",
            "RENT_SPLY_NO",
            "EMPT_RM",
            "공실률",
        ]
    ].copy()

    display_df.columns = [
        "사업대상지",
        "공공임대 공급호수",
        "공실",
        "공실률",
    ]

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
    )
