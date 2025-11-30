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

[필수 출력 형식]
반드시 아래 포맷을 그대로 따르세요. 태그(---SVG_START--- 등)를 절대 생략하지 마세요.

제목: [제목]
|||
## 1컷
**상황:** [묘사]
**대사:** [대사]
---SVG_START---
<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="white"/>
  <!-- 여기에 단순한 그림 코드 작성 -->
</svg>
---SVG_END---
|||
## 2컷
(위와 동일)
|||
## 3컷
(위와 동일)
|||
## 4컷
(위와 동일)
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
                
                # 디버깅용 원본 데이터 확인 (개발 단계에서 유용)
                with st.expander("디버깅: 원본 데이터 보기"):
                    st.text(response.text)

                # 응답 파싱
                parts = response.text.split("|||")
                
                # 제목 출력 (첫 번째 파트)
                if len(parts) > 0:
                    st.success("생성 완료! 🎉")
                    st.markdown("---")
                    st.header(parts[0].strip())

                # 컷별 출력 (나머지 파트)
                for i, part in enumerate(parts[1:], 1):
                    st.subheader(f"{i}컷") # 컷 번호 명시적으로 표시
                    
                    if "---SVG_START---" in part and "---SVG_END---" in part:
                        text_content, svg_content = part.split("---SVG_START---")
                        svg_code = svg_content.split("---SVG_END---")[0].strip()
                        
                        # 텍스트 표시
                        st.markdown(text_content.strip())
                        
                        # SVG 코드 정제 (가끔 마크다운 코드블럭 ```xml 등이 섞일 수 있음)
                        svg_code = svg_code.replace("```xml", "").replace("```svg", "").replace("```", "")
                        
                        # SVG 표시
                        st.html(f"""
                            <div style="display: flex; justify-content: center; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; padding: 10px;">
                                {svg_code}
                            </div>
                        """)
                    else:
                        # SVG가 없는 경우 텍스트만 표시
                        st.markdown(part)
                        st.warning("⚠️ 이 컷은 이미지가 생성되지 않았습니다.")
                    
                    st.markdown("---")

        except Exception as e:
            st.error(f"에러가 났어 ㅠㅠ: {e}")

if __name__ == "__main__":
    main()
