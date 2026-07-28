import pandas as pd
import requests
import streamlit as st


# 페이지 기본 설정
st.set_page_config(
    page_title="역세권 청년주택 공실률 현황",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 역세권 청년주택 공공임대 공실률 현황")
st.caption("서울 열린데이터광장 OpenAPI의 JSON 데이터를 조회합니다.")


@st.cache_data(ttl=3600)
def load_data(api_key):
    """서울 열린데이터광장에서 공실률 데이터를 불러오는 함수"""

    service_name = "tbYgmnPublicRntHouse"
    start_index = 1
    end_index = 1000

    url = (
        f"http://openapi.seoul.go.kr:8088/"
        f"{api_key}/json/{service_name}/{start_index}/{end_index}/"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    return response.json()


try:
    # 인증키는 Streamlit 비밀 금고에서만 불러옵니다.
    api_key = st.secrets["SEOUL_KEY"]

    json_data = load_data(api_key)

    # 정상 응답의 경우 서비스 이름 아래에 실제 데이터가 들어 있습니다.
    service_data = json_data.get("tbYgmnPublicRntHouse")

    if service_data is None:
        # 인증키 오류 등으로 faultInfo가 반환된 경우
        fault_info = json_data.get("RESULT") or json_data.get("faultInfo")

        if isinstance(fault_info, dict):
            message = (
                fault_info.get("MESSAGE")
                or fault_info.get("message")
                or "API 요청에 실패했습니다."
            )
            st.error(message)
        else:
            st.error("API 응답에서 데이터를 찾을 수 없습니다.")

        st.stop()

    result = service_data.get("RESULT", {})
    result_code = result.get("CODE")
    result_message = result.get("MESSAGE", "")

    if result_code != "INFO-000":
        st.error(f"데이터 조회에 실패했습니다: {result_message}")
        st.stop()

    rows = service_data.get("row", [])
    df = pd.DataFrame(rows)

    # 숫자로 사용되는 열의 자료형을 숫자형으로 변환합니다.
    numeric_columns = ["SN", "RENT_SPLY_NO", "EMPT_RM", "EMPT_RM_RT"]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    # 비어 있는 공실 값은 0으로 처리합니다.
    if "EMPT_RM" in df.columns:
        df["EMPT_RM"] = df["EMPT_RM"].fillna(0).astype(int)

    # 보기 편하도록 한글 열 이름을 사용합니다.
    column_names = {
        "SN": "연번",
        "BIZ_TRGT": "사업대상지",
        "RENT_SPLY_NO": "공공임대 공급호수",
        "EMPT_RM": "공실",
        "EMPT_RM_RT": "공실률",
    }

    display_df = df.rename(columns=column_names)

    total_count = service_data.get("list_total_count", len(df))

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric("전체 데이터 건수", f"{int(total_count):,}건")
    metric2.metric("불러온 행", f"{len(display_df):,}행")
    metric3.metric("열 개수", f"{len(display_df.columns):,}개")

    st.subheader("데이터 표")
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("데이터 형태")

    tab1, tab2, tab3 = st.tabs(
        ["자료형", "데이터 요약", "원본 JSON"]
    )

    with tab1:
        data_types = pd.DataFrame(
            {
                "열 이름": display_df.columns,
                "자료형": display_df.dtypes.astype(str).values,
            }
        )
        st.dataframe(data_types, use_container_width=True, hide_index=True)

    with tab2:
        st.write(f"데이터 크기: `{display_df.shape}`")
        st.write(f"행 개수: `{display_df.shape[0]}`")
        st.write(f"열 개수: `{display_df.shape[1]}`")
        st.write("열 이름:")
        st.code(", ".join(display_df.columns))

    with tab3:
        st.json(json_data)


except KeyError:
    st.error(
        "Streamlit 비밀 금고에 SEOUL_KEY가 없습니다. "
        "앱 설정의 Secrets에 인증키를 등록해 주세요."
    )

except requests.exceptions.Timeout:
    st.error("서울 열린데이터광장 서버의 응답 시간이 초과되었습니다.")

except requests.exceptions.RequestException as error:
    st.error(f"API 요청 중 오류가 발생했습니다: {error}")

except ValueError:
    st.error("서버에서 올바른 JSON 형식의 응답을 받지 못했습니다.")

except Exception as error:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {error}")
