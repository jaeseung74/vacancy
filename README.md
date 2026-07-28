# vacancy

스트림릿 앱 하나(main.py)를 만들어줘. 역세권 청년주택 공공임대 공실률 현황를 보여주는 앱을 만들거야. 
스트림릿 클라우드에 올릴 거야. 아래에 공식 API 문서에서 복사한 내용을 붙였어. 


- x 축이 "공공임대 공급호수", y축이 "공실"인 산포도를 plotly로 그려줘.
- 사업대상지와 공실률을 label로 추가해줘. 
- 인증키는 비밀 금고(secrets)의 SEOUL_KEY에서 불러와. 코드에는 절대 쓰지 마. 
- 필요한 라이브러리 목록(requirements.txt)도 같이 줘. 버전 숫자 없이 이름만 줘. 


──── 아래는 서울열린데이터 광장 공식 문서에서 복사한 부분 ────

샘플 URL
샘플 URL	역세권 청년주택 공공임대 공실률 현황
http://openapi.seoul.go.kr:8088/(인증키)/xml/tbYgmnPublicRntHouse/1/5/
예제	
<?xml version="1.0" encoding="UTF-8"?>
<tbYgmnPublicRntHouse>
<list_total_count>56</list_total_count>
<RESULT>
<CODE>INFO-000</CODE>
<MESSAGE>정상 처리되었습니다</MESSAGE>
</RESULT>
<row>
<SN>1</SN>
<BIZ_TRGT>서대문구 충정로3가 72-1 외7</BIZ_TRGT>
<RENT_SPLY_NO>49</RENT_SPLY_NO>
<EMPT_RM>2</EMPT_RM>
<EMPT_RM_RT>0.04</EMPT_RM_RT>
</row>
<row>
<SN>2</SN>
<BIZ_TRGT>성동구 용답동 233-1</BIZ_TRGT>
<RENT_SPLY_NO>22</RENT_SPLY_NO>
<EMPT_RM/>
<EMPT_RM_RT>0</EMPT_RM_RT>
</row>
<row>
<SN>3</SN>
<BIZ_TRGT>광진구 구의동 587-64</BIZ_TRGT>
<RENT_SPLY_NO>18</RENT_SPLY_NO>
<EMPT_RM/>
<EMPT_RM_RT>0</EMPT_RM_RT>
</row>
<row>
<SN>4</SN>
<BIZ_TRGT>마포구 서교동 395-43 외5</BIZ_TRGT>
<RENT_SPLY_NO>199</RENT_SPLY_NO>
<EMPT_RM>18</EMPT_RM>
<EMPT_RM_RT>0.09</EMPT_RM_RT>
</row>
<row>
<SN>5</SN>
<BIZ_TRGT>강서구 등촌동 648-5</BIZ_TRGT>
<RENT_SPLY_NO>19</RENT_SPLY_NO>
<EMPT_RM>4</EMPT_RM>
<EMPT_RM_RT>0.21</EMPT_RM_RT>
</row>
</tbYgmnPublicRntHouse>


요청인자
변수명	타입	변수설명	값설명
KEY	String(필수)	인증키	OpenAPI 에서 발급된 인증키
TYPE	String(필수)	요청파일타입	xml : xml, xml파일 : xmlf, 엑셀파일 : xls, json파일 : json
SERVICE	String(필수)	서비스명	tbYgmnPublicRntHouse
START_INDEX	INTEGER(필수)	요청시작위치	정수 입력 (페이징 시작번호 입니다 : 데이터 행 시작번호)
END_INDEX	INTEGER(필수)	요청종료위치	정수 입력 (페이징 끝번호 입니다 : 데이터 행 끝번호)
BIZ_TRGT	STRING(선택)	사업대상지	
출력값
No	출력명	출력설명
공통	list_total_count	총 데이터 건수 (정상조회 시 출력됨)
공통	RESULT.CODE	요청결과 코드 (하단 메세지설명 참고)
공통	RESULT.MESSAGE	요청결과 메시지 (하단 메세지설명 참고)
1	SN	연번
2	BIZ_TRGT	사업대상지
3	RENT_SPLY_NO	공공임대공급호수
4	EMPT_RM	공실
5	EMPT_RM_RT	공실률
