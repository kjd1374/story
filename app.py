import streamlit as st
import google.generativeai as genai
import os

# 1. 페이지 설정 (모바일 친화적)
st.set_page_config(
    page_title="두더지와 페럿의 툰 공장",
    page_icon="🐭",
    layout="centered"
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

# 3. 시스템 프롬프트 (SVG 생성 포함)
SYSTEM_PROMPT = """
당신은 인스타툰 전문 콘티 작가이자, 매우 단순한 그림을 그리는 코더입니다.
사용자의 입력을 바탕으로 4컷 만화의 스토리와 각 장면의 SVG 코드를 작성하세요.

[그림 스타일: '졸라맨' 초단순 약식]
- 복잡한 묘사 금지. 유치원생 낙서처럼 검은색 선으로만 표현.
- 배경 없음 (투명).
- **남주(두더지):** 뚱뚱한 회색 덩어리(감자 모양). 가운데 큰 동그라미 코. 점 눈. 땀 흘리는 표현 자주 사용.
- **여주(페럿/담비):** 역삼각형 얼굴. 큰 동그라미 눈. 머리 뒤로 긴 선 몇 개(머리카락).

[출력 형식 엄수]
반드시 아래와 같은 구조로, 각 컷을 '|||' 구분자로 나누어 출력하세요. 마크다운이나 다른 사족을 달지 마세요.

제목: [재치 있는 제목]
|||
## 1컷 내용
**상황:** [상황 묘사]
**대사:** [캐릭터]: "대사"
---SVG_START---
<svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
(여기에 1컷 상황을 묘사하는 단순한 졸라맨 스타일의 SVG 코드 작성. 남주, 여주 특징 살릴 것)
</svg>
---SVG_END---
|||
## 2컷 내용
(위와 동일한 구조)...
|||
## 3컷 내용
(위와 동일한 구조)...
|||
## 4컷 내용
(위와 동일한 구조, 마지막 컷 반전/유머 필수)...
"""

def main():
    # 제목
    st.title("🐭 두더지와 페럿의 툰 공장")
    st.caption("Mobile Ver. 🏭 (with AI Illustrator)")

    # API Key 처리
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except FileNotFoundError:
        api_key = os.environ.get("GEMINI_API_KEY")
    
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
    if st.button("콘티 & 그림 뽑기 🎨", use_container_width=True):
        if not episode.strip():
            st.warning("내용을 입력해줘! ✍️")
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT
            )

            with st.spinner("🐭 두더지가 열심히 그림을 그리고 있어요... (약 10초)"):
                response = model.generate_content(episode)
                
                # 응답 파싱
                parts = response.text.split("|||")
                
                # 제목 출력 (첫 번째 파트)
                if len(parts) > 0:
                    st.success("생성 완료! 🎉")
                    st.markdown("---")
                    st.header(parts[0].strip())

                # 컷별 출력 (나머지 파트)
                for part in parts[1:]:
                    if "---SVG_START---" in part and "---SVG_END---" in part:
                        text_content, svg_content = part.split("---SVG_START---")
                        svg_code = svg_content.split("---SVG_END---")[0].strip()
                        
                        # 텍스트 표시
                        st.markdown(text_content.strip())
                        
                        # SVG 표시 (가운데 정렬)
                        st.html(f"""
                            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                                {svg_code}
                            </div>
                        """)
                        st.markdown("---")
                    else:
                        # SVG가 없는 경우 텍스트만 표시 (예외 처리)
                        st.markdown(part)

        except Exception as e:
            st.error(f"에러가 났어 ㅠㅠ: {e}")

if __name__ == "__main__":
    main()
