# --------------------------------------------------
# 그래프 라벨 만들기
# --------------------------------------------------
df["공실률"] = df["EMPT_RM_RT"].apply(
    lambda value: f"{value * 100:.1f}%"
)

# 모든 사업대상지 정보는 마우스를 올렸을 때 표시합니다.
df["전체라벨"] = (
    df["BIZ_TRGT"].astype(str)
    + "<br>공실률 "
    + df["공실률"]
)

# 화면에는 공실이 1호 이상인 사업지만 라벨을 표시합니다.
# 공실이 0인 사업지는 마우스를 올리면 정보를 볼 수 있습니다.
df["표시라벨"] = df.apply(
    lambda row: (
        f"{row['BIZ_TRGT']}<br>공실률 {row['공실률']}"
        if row["EMPT_RM"] > 0
        else ""
    ),
    axis=1,
)


# --------------------------------------------------
# 라벨 위치를 점마다 다르게 지정
# --------------------------------------------------
# 같은 위치에 라벨이 몰리는 것을 줄이기 위해
# 위·아래·왼쪽·오른쪽 위치를 번갈아 사용합니다.
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
# Plotly 산포도 작성
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
        "전체라벨": False,
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
    # 각 점에 서로 다른 라벨 위치를 적용합니다.
    textposition=df["라벨위치"].tolist(),

    # 라벨 글자 크기를 줄여 겹침을 완화합니다.
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

    # 그래프 바깥쪽 라벨이 잘리지 않도록 여백을 늘립니다.
    margin={
        "l": 70,
        "r": 100,
        "t": 100,
        "b": 70,
    },

    # 라벨 위에 마우스를 올릴 때 정보를 보기 쉽게 합니다.
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
