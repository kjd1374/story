import streamlit as st
import google.generativeai as genai
import os

# 1. 페이지 설정 (모바일 친화적)
st.set_page_config(
    page_title="두더지와 페럿의 툰 공장",
    page_icon="🐭",
    layout="centered"  # 모바일에서 보기 좋게 중앙 정렬
)

# 2. 스타일링 (모바일 가독성 향상)
st.markdown("""
    <style>
    .stTextArea textarea {
        font-size: 16px !important;
    }
    div[data-testid="stMarkdownContainer"] h2 {
        font-size: 1.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 시스템 프롬프트
SYSTEM_PROMPT = """
너는 인스타툰 전문 콘티 작가야.

[캐릭터]
1. 남주(두더지): 회색 후드, 뚱뚱함, 큰 코, 억울한 표정, 땀 삐질.
2. 여주(페럿): 뾰족한 턱, 큰 눈, 긴 생머리, 예쁘지만 기가 셈.

[출력]
무조건 Markdown 형식으로 출력.
제목, 1~4컷(상황묘사/대사) 구성. 마지막 컷은 반전/유머 필수.
"""

def main():
    # 제목
    st.title("🐭 두더지와 페럿의 툰 공장")
    st.caption("Mobile Ver. 🏭")

    # API Key 처리 (st.secrets 우선 사용)
    try:
        api_key = st.secrets["AIzaSyDBZfdDnZ2PO2qSQ-2Ps9k8x9ftfwal56g"]
    except FileNotFoundError:
        # 로컬 테스트용 (secrets.toml 파일이 없을 때)
        api_key = os.environ.get("AIzaSyDBZfdDnZ2PO2qSQ-2Ps9k8x9ftfwal56g")
    
    if not api_key:
        st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해주세요.")
        st.stop()

    # 입력창
    st.markdown("### 오늘의 에피소드는?")
    episode = st.text_area(
        label="에피소드 입력",
        label_visibility="collapsed",
        placeholder="예: 여자친구랑 카페 갔는데 내가 커피 쏟아서 혼난 이야기...",
        height=200
    )

    # 실행 버튼
    if st.button("콘티 뽑기 🎨", use_container_width=True):
        if not episode.strip():
            st.warning("내용을 입력해줘! ✍️")
            return

        try:
            # Gemini 설정
            genai.configure(_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT
            )

            with st.spinner("🐭 두더지가 머리를 굴리는 중..."):
                response = model.generate_content(episode)
                
                st.success("완료! 🎉")
                st.markdown("---")
                st.markdown(response.text)
                st.markdown("---")
                st.markdown("캡처해서 그림 작가에게 전달하세요! 📸")

        except Exception as e:
            st.error(f"에러가 났어 ㅠㅠ: {e}")

if __name__ == "__main__":
    main()
