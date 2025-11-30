import streamlit as st
import google.generativeai as genai
import os
import re
import json
from datetime import datetime
from pathlib import Path

# 저장 디렉토리 설정
STORAGE_DIR = Path("saved_stories")
STORAGE_DIR.mkdir(exist_ok=True)

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
사용자의 입력을 바탕으로 4컷 만화 스토리와 상세한 콘티, 그리고 SVG 코드를 작성하세요.

[콘티 작성 가이드 - 매우 중요!]
각 컷마다 반드시 다음 정보를 상세히 포함하세요:
1. **상황 설명**: 장면의 배경, 시간, 분위기
2. **캐릭터 위치**: 누가 어디에 있는지 (왼쪽/오른쪽/중앙 등)
3. **캐릭터 표정**: 기쁨/슬픔/화남/당황 등 구체적인 감정
4. **캐릭터 포즈**: 서있음/앉음/뛰는 중 등
5. **배경 요소**: 필요한 소품이나 배경 (테이블, 의자, 공항 등)
6. **구도**: 클로즈업/풀샷/미디엄샷 등
7. **대사**: 누가 말하는지 명시 (두더지/페럿/기타)
8. **효과음/의성어**: 필요한 경우

[그림 스타일 - 중요!]
- **좌표계:** 반드시 viewBox="0 0 400 400" 기준. (0~400 사이 좌표만 사용)
- **필수 요소:** 모든 SVG는 <rect width="400" height="400" fill="white"/> 로 시작해서 흰 배경을 깔아야 함.
- **단순화:** 복잡한 path 금지. <circle>, <rect>, <line>, <ellipse> 태그 위주로 사용.
- **캐릭터 디자인:**
  - 두더지: 회색 타원형 몸통 (<ellipse rx="60" ry="80" fill="#ddd"/>), 까만 코, 작은 눈
  - 페럿: 흰색 역삼각형 얼굴, 긴 머리카락, 날카로운 눈매
- **표정 표현:** 눈과 입 모양으로 감정 표현 (기쁨: 웃는 눈, 슬픔: 눈물, 화남: 찡그린 눈 등)

[출력 포맷]
반드시 아래 형식을 지키세요.

제목: [제목]
||||
## 1컷
**상황:** [상세한 상황 설명 - 배경, 시간, 분위기]
**캐릭터 위치:** [누가 어디에 있는지]
**표정:** [구체적인 감정과 표정]
**포즈:** [캐릭터의 자세]
**배경:** [필요한 소품이나 배경 요소]
**구도:** [클로즈업/풀샷/미디엄샷 등]
**대사:** [대사 내용 - 누가 말하는지 명시]
**효과음:** [필요한 경우]
```svg
<svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="white"/>
  <!-- 여기에 그림 코드 -->
</svg>
```
||||
## 2컷
(위와 동일 형식으로 상세히 작성)
...
"""

def save_story(title, episode, response_text, parts_data):
    """콘티를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{title[:20]}.json"
    filepath = STORAGE_DIR / filename
    
    story_data = {
        "title": title,
        "episode": episode,
        "created_at": datetime.now().isoformat(),
        "response_text": response_text,
        "parts": parts_data
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    return filepath

def load_saved_stories():
    """저장된 콘티 목록 불러오기"""
    stories = []
    if STORAGE_DIR.exists():
        for filepath in sorted(STORAGE_DIR.glob("*.json"), reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["filename"] = filepath.name
                    stories.append(data)
            except:
                continue
    return stories

def parse_story_parts(response_text):
    """응답 텍스트를 파싱하여 구조화된 데이터로 변환"""
    parts = response_text.split("|||")
    title = parts[0].strip() if len(parts) > 0 else "제목 없음"
    
    parsed_parts = []
    for i, part in enumerate(parts[1:], 1):
        # SVG 추출
        svg_match = None
        svg_code = None
        
        pattern1 = re.search(r'```svg\s*(<svg[\s\S]*?<\/svg>)\s*```', part, re.IGNORECASE | re.DOTALL)
        if pattern1:
            svg_code = pattern1.group(1).strip()
            svg_match = pattern1
        else:
            pattern2 = re.search(r'```xml\s*(<svg[\s\S]*?<\/svg>)\s*```', part, re.IGNORECASE | re.DOTALL)
            if pattern2:
                svg_code = pattern2.group(1).strip()
                svg_match = pattern2
            else:
                pattern3 = re.search(r'(<svg[\s\S]*?<\/svg>)', part, re.IGNORECASE | re.DOTALL)
                if pattern3:
                    svg_code = pattern3.group(1).strip()
                    svg_match = pattern3
        
        text_content = part.replace(svg_match.group(0), "").strip() if svg_match else part.strip()
        
        parsed_parts.append({
            "cut_number": i,
            "text_content": text_content,
            "svg_code": svg_code
        })
    
    return title, parsed_parts

def display_story(title, parts_data):
    """콘티를 화면에 표시"""
    st.header(title)
    st.markdown("---")
    
    for part in parts_data:
        st.subheader(f"{part['cut_number']}컷")
        st.markdown(part['text_content'])
        
        if part['svg_code']:
            st.markdown(f"""
                <div style="width: 100%; max-width: 400px; height: 400px; margin: 10px auto; border: 2px solid #eee; border-radius: 10px; overflow: hidden; background-color: white; display: flex; align-items: center; justify-content: center;">
                    {part['svg_code']}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

def main():
    # 탭 생성
    tab1, tab2 = st.tabs(["🎨 새 콘티 만들기", "📚 저장된 콘티 보기"])
    
    with tab1:
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
                    
                    # 응답 파싱
                    title, parts_data = parse_story_parts(response.text)
                    
                    # 콘티 표시
                    st.success("생성 완료! 🎉")
                    display_story(title, parts_data)
                    
                    # 저장 버튼
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 콘티 저장하기", use_container_width=True):
                            filepath = save_story(title, episode, response.text, parts_data)
                            st.success(f"저장 완료! 📁 {filepath.name}")
                    
                    with col2:
                        # 세션 상태에 저장 (임시로 다시 보기 가능)
                        st.session_state['last_story'] = {
                            'title': title,
                            'episode': episode,
                            'response_text': response.text,
                            'parts': parts_data
                        }
            
            except Exception as e:
                st.error(f"에러 발생: {e}")
    
    with tab2:
        st.title("📚 저장된 콘티 목록")
        
        saved_stories = load_saved_stories()
        
        if not saved_stories:
            st.info("저장된 콘티가 없습니다. 새 콘티를 만들어보세요! 🎨")
        else:
            st.markdown(f"총 {len(saved_stories)}개의 콘티가 저장되어 있습니다.")
            
            # 콘티 선택
            story_options = [f"{s['title']} ({s['created_at'][:10]})" for s in saved_stories]
            selected_idx = st.selectbox(
                "콘티 선택",
                range(len(story_options)),
                format_func=lambda x: story_options[x]
            )
            
            if selected_idx is not None:
                selected_story = saved_stories[selected_idx]
                
                # 삭제 버튼
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️ 삭제", key=f"delete_{selected_idx}"):
                        filepath = STORAGE_DIR / selected_story['filename']
                        if filepath.exists():
                            filepath.unlink()
                            st.success("삭제 완료!")
                            st.rerun()
                
                # 콘티 표시
                st.markdown("---")
                st.markdown(f"**원본 에피소드:** {selected_story['episode']}")
                st.markdown(f"**생성일시:** {selected_story['created_at']}")
                st.markdown("---")
                
                display_story(selected_story['title'], selected_story['parts'])

if __name__ == "__main__":
    main()
