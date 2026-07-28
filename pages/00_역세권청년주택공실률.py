import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# --------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="역세권 청년주택 공실률",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 역세권 청년주택 공공임대 공실률 현황")
st.write(
    "공공임대 공급호수와 공실의 관계를 산포도로 확인할 수 있습니다."
)


# --------------------------------------------------
# 2. 서울열린데이터광장 API 호출
# --------------------------------------------------
@st.cache_data(ttl=3600)
def load_data(api_key):
    """
    역세권 청년주택 공공임대 공실률 데이터를 불러옵니다.
    같은 데이터는 1시간 동안 저장하여 API 재호출을 줄입니다.
    """

    service_name = "tbYgmnPublicRntHouse"

    # 전체 데이터가 1,000건 미만이므로 1~1000 범위로 요청합니다.
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
                or fault_info.get("MESSAGE")
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

    # 데이터가 1건일 때도 리스트 형태로 맞춥니다.
    if isinstance(rows, dict):
        rows = [rows]

    return rows


# --------------------------------------------------
# 3. Secrets에서 인증키 불러오기
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
# 4. API 데이터 불러오기
# --------------------------------------------------
try:
    with st.spinner("공공임대 공실 데이터를 불러오고 있습니다..."):
        rows = load_data(seoul_key)

except RuntimeError as error:
    st.error(str(error))
    st.stop()


if not rows:
    st.info("표시할 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 5. 여기에서 df를 먼저 생성합니다.
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
# 6. 숫자 데이터 정리
# --------------------------------------------------
# 공공임대 공급호수를 숫자로 바꿉니다.
df["RENT_SPLY_NO"] = pd.to_numeric(
    df["RENT_SPLY_NO"],
    errors="coerce",
)

# 빈 공실 값은 0으로 처리합니다.
df["EMPT_RM"] = pd.to_numeric(
    df["EMPT_RM"],
    errors="coerce",
).fillna(0)

# 빈 공실률 값은 0으로 처리합니다.
df["EMPT_RM_RT"] = pd.to_numeric(
    df["EMPT_RM_RT"],
    errors="coerce",
).fillna(0)

# 사업대상지나 공급호수가 없는 데이터는 제외합니다.
df = df.dropna(
    subset=["BIZ_TRGT", "RENT_SPLY_NO"]
).copy()

if df.empty:
    st.info("산포도에 표시할 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 7. 공실률과 라벨 만들기
# --------------------------------------------------
df["공실률"] = df["EMPT_RM_RT"].apply(
    lambda value: f"{value * 100:.1f}%"
)

# 마우스를 올렸을 때 표시할 전체 정보입니다.
df["호버라벨"] = (
    df["BIZ_TRGT"].astype(str)
    + "<br>공실률 "
    + df["공실률"]
)

# 공실이 있는 사업대상지만 그래프에 고정 라벨로 표시합니다.
# 공실이 0인 지점은 마우스를 올리면 정보를 확인할 수 있습니다.
df["표시라벨"] = df.apply(
    lambda row: (
        f"{row['BIZ_TRGT']}<br>공실률 {row['공실률']}"
        if row["EMPT_RM"] > 0
        else ""
    ),
    axis=1,
)


# --------------------------------------------------
# 8. 라벨 위치를 분산시켜 겹침 완화
# --------------------------------------------------
text_positions = [
    "top center",
    "bottom center",
    "middle left",
    "middle right",
    "top left",
    "top right",
    "bottom left",
    "bottom right",
]

df["라벨위치"] = [
    text_positions[index % len(text_positions)]
    for index in range(len(df))
]


# --------------------------------------------------
# 9. 주요 지표
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
    "공공임대 공급호수",
    f"{total_supply:,}호",
)

col3.metric(
    "전체 공실률",
    f"{total_vacancy_rate:.1f}%",
)


# --------------------------------------------------
# 10. Plotly 산포도
# --------------------------------------------------
figure = px.scatter(
    df,
    x="RENT_SPLY_NO",
    y="EMPT_RM",
    text="표시라벨",
    hover_name="BIZ_TRGT",
    hover_data={
        "RENT_SPLY_NO": ":,.0f",
        "EMPT_RM": ":,.0f",
        "공실률": True,
        "EMPT_RM_RT": False,
        "호버라벨": False,
        "표시라벨": False,
        "라벨위치": False,
    },
    labels={
        "RENT_SPLY_NO": "공공임대 공급호수",
        "EMPT_RM": "공실",
        "공실률": "공실률",
    },
    title="공공임대 공급호수와 공실의 관계",
)

figure.update_traces(
    # 각 라벨의 위치를 다르게 지정합니다.
    textposition=df["라벨위치"].tolist(),

    # 글자 크기를 줄여 겹침을 완화합니다.
    textfont={
        "size": 10,
    },

    marker={
        "size": 11,
        "opacity": 0.75,
        "line": {
            "width": 1,
            "color": "black",
        },
    },

    cliponaxis=False,
)

figure.update_layout(
    height=750,
    xaxis_title="공공임대 공급호수",
    yaxis_title="공실",
    margin={
        "l": 70,
        "r": 100,
        "t": 100,
        "b": 70,
    },
    hoverlabel={
        "bgcolor": "white",
        "font_size": 13,
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
# 11. 데이터 표
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
