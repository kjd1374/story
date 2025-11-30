import streamlit as st
import google.generativeai as genai
import os
import re

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
당신은 인스타툰 전문 콘티 작가이자, SVG 코더입니다.
사용자의 입력을 바탕으로 4컷 만화 스토리와 SVG 코드를 작성하세요.

[그림 스타일 - 중요!]
- **좌표계:** 반드시 viewBox="0 0 400 400" 기준. (0~400 사이 좌표만 사용)
- **필수 요소:** 모든 SVG는 <rect width="400" height="400" fill="white"/> 로 시작해서 흰 배경을 깔아야 함.
- **단순화:** 복잡한 path 금지. <circle>, <rect>, <line> 태그 위주로 사용.
- **캐릭터:**
  - 두더지: 회색 타원형 몸통 (<ellipse rx="60" ry="80" fill="#ddd"/>), 까만 코.
  - 페럿: 흰색 역삼각형 얼굴, 긴 머리카락.

[출력 포맷]
반드시 아래 형식을 지키세요.

제목: [제목]
|||
## 1컷
**상황:** [상황]
**대사:** [대사]
```svg
<svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="white"/>
  <!-- 여기에 그림 코드 -->
  <circle cx="200" cy="200" r="100" fill="#ddd" stroke="black" stroke-width="3"/>
</svg>
```
|||
## 2컷
(위와 동일)
...
"""

def main():
    # 제목
    st.title("🐭 두더지와 페럿의 툰 공장")
    st.caption("Mobile Ver. 🏭 (AI Illustrator)")

    # API Key 처리
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except FileNotFoundError:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("🚨 API 키가 설정되지 않았습니다.")
        st.stop()

    # 입력창
    st.markdown("### 오늘의 에피소드는?")
    episode = st.text_area(
        label="에피소드 입력",
        label_visibility="collapsed",
        placeholder="예: 쌀국수 먹다 옷에 튀어서 페럿한테 혼난 이야기",
        height=150
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

            with st.spinner("🐭 두더지가 그림 그리는 중..."):
                response = model.generate_content(episode)
                
                # 디버깅: 원본 데이터 확인
                with st.expander("디버깅용 원본 데이터 (클릭해서 확인)"):
                    st.code(response.text)

                # 응답 파싱 (||| 기준 분리)
                parts = response.text.split("|||")
                
                # 제목 출력
                if len(parts) > 0:
                    st.success("생성 완료! 🎉")
                    st.markdown("---")
                    st.header(parts[0].strip())

                # 컷별 출력
                for i, part in enumerate(parts[1:], 1):
                    st.subheader(f"{i}컷")
                    
                    # 1. 텍스트와 SVG 분리 (Regex 사용)
                    # ```svg ... ``` 또는 <svg ... </svg> 패턴 찾기
                    # 여러 패턴 시도: 코드블록 안의 SVG, 직접 SVG 태그
                    svg_match = None
                    svg_code = None
                    
                    # 패턴 1: ```svg ... ``` 형태
                    pattern1 = re.search(r'```svg\s*(<svg[\s\S]*?<\/svg>)\s*```', part, re.IGNORECASE | re.DOTALL)
                    if pattern1:
                        svg_code = pattern1.group(1).strip()
                        svg_match = pattern1
                    else:
                        # 패턴 2: ```xml ... ``` 형태
                        pattern2 = re.search(r'```xml\s*(<svg[\s\S]*?<\/svg>)\s*```', part, re.IGNORECASE | re.DOTALL)
                        if pattern2:
                            svg_code = pattern2.group(1).strip()
                            svg_match = pattern2
                        else:
                            # 패턴 3: 직접 <svg> 태그
                            pattern3 = re.search(r'(<svg[\s\S]*?<\/svg>)', part, re.IGNORECASE | re.DOTALL)
                            if pattern3:
                                svg_code = pattern3.group(1).strip()
                                svg_match = pattern3
                    
                    if svg_match and svg_code:
                        text_content = part.replace(svg_match.group(0), "").strip() # SVG 부분을 뺀 나머지 텍스트
                        
                        # 텍스트 표시
                        st.markdown(text_content)
                        
                        # SVG 표시 (높이 강제 지정)
                        st.markdown(f"""
                            <div style="width: 100%; max-width: 400px; height: 400px; margin: 10px auto; border: 2px solid #eee; border-radius: 10px; overflow: hidden; background-color: white; display: flex; align-items: center; justify-content: center;">
                                {svg_code}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 디버깅: 추출된 SVG 코드 확인
                        with st.expander(f"{i}컷 SVG 코드 확인"):
                            st.code(svg_code, language='xml')
                            
                    else:
                        # SVG를 못 찾은 경우
                        st.markdown(part)
                        st.warning("⚠️ 이미지를 찾을 수 없습니다.")
                    
                    st.markdown("---")

        except Exception as e:
            st.error(f"에러 발생: {e}")

if __name__ == "__main__":
    main()
