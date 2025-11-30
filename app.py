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
당신은 프로페셔널 인스타툰 콘티 작가이자, 상세한 스토리보드 작가입니다.
사용자의 입력을 바탕으로 4컷 만화를 위한 매우 상세하고 구체적인 콘티를 작성하세요.
이 콘티는 나중에 실제 만화를 그릴 때 참고할 수 있도록 충분히 상세해야 합니다.

[콘티 작성 가이드 - 필수! 반드시 모든 항목을 상세히 작성하세요!]

각 컷마다 다음 정보를 반드시 포함하되, 각 항목을 최소 2-3문장으로 상세히 설명하세요:

1. **상황 설명**: 
   - 장면이 어디서 일어나는지 (구체적인 장소: 공항 대합실, 집 거실, 카페 등)
   - 시간대 (아침/점심/저녁, 계절 등)
   - 전체적인 분위기와 기분 (긴장감, 여유로움, 당황스러움 등)
   - 이전 컷과의 연결성

2. **캐릭터 위치**: 
   - 화면 내에서 정확한 위치 (왼쪽 상단, 중앙, 오른쪽 하단 등)
   - 캐릭터 간의 거리와 관계
   - 카메라 각도 (정면, 측면, 위에서 내려다봄 등)

3. **캐릭터 표정**: 
   - 구체적인 감정 상태 (예: "두더지는 눈이 크게 뜨이고 입이 벌어진 당황한 표정")
   - 눈의 모양 (크게 뜬 눈, 찡그린 눈, 웃는 눈 등)
   - 입의 모양 (벌어진 입, 찡그린 입, 웃는 입 등)
   - 얼굴 전체의 분위기

4. **캐릭터 포즈**: 
   - 신체의 자세 (서있음, 앉음, 뛰는 중, 구부린 자세 등)
   - 팔과 다리의 위치 (팔을 뻗음, 손을 머리에 대고 있음 등)
   - 몸의 방향 (정면, 측면, 뒤돌아봄 등)
   - 움직임이 있다면 그 방향과 속도감

5. **배경 요소**: 
   - 배경에 필요한 모든 소품 (테이블, 의자, 가방, 핸드폰, 표지판 등)
   - 각 소품의 위치와 크기
   - 배경의 색상과 분위기
   - 배경이 스토리에 미치는 영향

6. **구도**: 
   - 샷의 종류 (클로즈업: 얼굴만, 미디엄샷: 상반신, 풀샷: 전신, 와이드샷: 배경 포함 등)
   - 초점이 맞춰진 대상
   - 배경의 흐림 정도 (초점 밖의 배경은 흐리게)

7. **대사**: 
   - 누가 말하는지 명확히 표시 (두더지/페럿/기타 등장인물)
   - 대사의 톤과 감정 (큰 소리로, 작은 목소리로, 화가 나서 등)
   - 말풍선의 위치와 크기

8. **효과음/의성어**: 
   - 필요한 경우 효과음 (탕!, 쾅!, 휙! 등)
   - 효과음의 위치와 크기
   - 시각적 효과 (번쩍임, 먼지, 바람 등)

[SVG 그림 - 매우 중요! 반드시 읽고 따라하세요!]
SVG 그림은 단순한 스케치가 아니라, 위에서 설명한 모든 요소를 시각적으로 명확하게 표현해야 합니다.
사람이 보기에 이해할 수 있는 수준의 그림이어야 합니다.

- **좌표계:** 반드시 viewBox="0 0 400 400" 기준. (0~400 사이 좌표만 사용)
- **필수 요소:** 모든 SVG는 <rect width="400" height="400" fill="white"/> 로 시작해서 흰 배경을 깔아야 함.

- **배경:** 배경 요소를 먼저 그리고, 그 위에 캐릭터를 그려야 함. 배경이 없으면 단조로워 보임.
  예시: 공항이면 바닥(회색 사각형), 벽(연한 회색), 창문, 표지판 등

- **캐릭터 디자인 - 두더지 (매우 중요!):**
  * 머리: 타원형, 중심 (cx="200" cy="120"), 크기 (rx="35" ry="40"), 색상 (#aaa 또는 #999)
  * 몸통: 타원형, 중심 (cx="200" cy="220"), 크기 (rx="50" ry="70"), 색상 (#999)
  * 코: 검은 원, 중심 (cx="200" cy="120"), 반지름 r="6"
  * 눈: 두 개의 원, 좌 (cx="185" cy="110"), 우 (cx="215" cy="110"), 반지름 r="5", 표정에 따라 모양 변경
    - 기쁨: 눈을 반원으로 (<path d="M 180 110 Q 185 105 190 110" stroke="black" fill="none" stroke-width="2"/>)
    - 당황: 큰 원 (r="8")
    - 화남: 작은 원 + 위쪽 선 (찡그린 눈)
  * 입: 표정에 따라
    - 기쁨: 웃는 입 (<path d="M 185 130 Q 200 140 215 130" stroke="black" fill="none" stroke-width="2"/>)
    - 당황: 벌어진 입 (타원형 <ellipse cx="200" cy="135" rx="8" ry="12" fill="black"/>)
  * 팔: <line x1="150" y1="200" x2="130" y2="180" stroke="#666" stroke-width="8" stroke-linecap="round"/>
  * 다리: <line x1="170" y1="290" x2="160" y2="350" stroke="#666" stroke-width="10" stroke-linecap="round"/>

- **캐릭터 디자인 - 페럿 (매우 중요!):**
  * 얼굴: 역삼각형, 중심 (cx="200" cy="130")
    <polygon points="200,80 160,150 240,150" fill="#fff" stroke="#333" stroke-width="2"/>
  * 머리카락: 긴 타원형 또는 여러 선
    <ellipse cx="200" cy="90" rx="45" ry="25" fill="#ffd700" opacity="0.8"/>
  * 눈: 날카로운 형태, 다각형 또는 타원
    <polygon points="185,120 190,115 195,120 190,125" fill="black"/>
  * 입: 작은 선 또는 다각형

- **표정 표현 (구체적 예시):**
  - 기쁨: 눈을 반원(^)으로, 입을 웃는 모양(∩)으로
  - 슬픔: 눈에 눈물 추가 (<circle cx="185" cy="115" r="2" fill="blue"/>), 입을 아래로(∩)
  - 화남: 눈을 찡그린 모양(/\ /\), 입을 크게 벌림
  - 당황: 눈을 크게 뜸(큰 원), 입을 벌림(타원형)

- **포즈 표현 (구체적 예시):**
  - 서있음: 다리를 똑바로, 팔을 몸통 옆에
  - 앉음: 다리를 구부림, 몸통을 낮춤
  - 뛰는 중: 다리를 앞뒤로, 팔을 뻗음, 몸을 앞으로 기울임
  - 손 뻗음: 팔을 특정 방향으로 <line>으로 표현

- **배경 요소 (구체적 예시):**
  - 테이블: <rect x="50" y="300" width="300" height="20" fill="#8B4513"/>
  - 의자: <rect x="100" y="280" width="60" height="80" fill="#654321"/>
  - 핸드폰: <rect x="180" y="200" width="40" height="60" fill="#333" rx="3"/>
  - 표지판: <rect x="300" y="50" width="80" height="100" fill="#fff" stroke="#000"/>
  - 원근감: 멀리 있는 것은 작고, 가까운 것은 크게

- **구도 표현:**
  - 클로즈업: 캐릭터를 크게 (머리만 또는 상반신만, 크기 200x200 정도)
  - 풀샷: 캐릭터 전체와 배경 포함 (전신, 크기 100x200 정도)
  - 미디엄샷: 상반신과 일부 배경 (상반신, 크기 150x200 정도)

[SVG 코드 작성 예시 - 반드시 참고하세요!]
```svg
<svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="400" fill="white"/>
  <!-- 배경: 공항 대합실 -->
  <rect x="0" y="300" width="400" height="100" fill="#ddd"/> <!-- 바닥 -->
  <rect x="0" y="0" width="400" height="300" fill="#e8f4f8"/> <!-- 벽 -->
  <rect x="50" y="50" width="100" height="150" fill="#87ceeb" opacity="0.3"/> <!-- 창문 -->
  <!-- 두더지: 당황한 표정 -->
  <ellipse cx="200" cy="220" rx="50" ry="70" fill="#999"/> <!-- 몸통 -->
  <ellipse cx="200" cy="120" rx="35" ry="40" fill="#aaa"/> <!-- 머리 -->
  <circle cx="200" cy="120" r="6" fill="black"/> <!-- 코 -->
  <circle cx="185" cy="110" r="8" fill="black"/> <!-- 왼쪽 눈 (큰 원) -->
  <circle cx="215" cy="110" r="8" fill="black"/> <!-- 오른쪽 눈 (큰 원) -->
  <ellipse cx="200" cy="135" rx="8" ry="12" fill="black"/> <!-- 벌어진 입 -->
  <line x1="150" y1="200" x2="130" y2="180" stroke="#666" stroke-width="8" stroke-linecap="round"/> <!-- 왼쪽 팔 -->
  <line x1="250" y1="200" x2="270" y2="180" stroke="#666" stroke-width="8" stroke-linecap="round"/> <!-- 오른쪽 팔 -->
  <line x1="170" y1="290" x2="160" y2="350" stroke="#666" stroke-width="10" stroke-linecap="round"/> <!-- 왼쪽 다리 -->
  <line x1="230" y1="290" x2="240" y2="350" stroke="#666" stroke-width="10" stroke-linecap="round"/> <!-- 오른쪽 다리 -->
</svg>
```

위 예시처럼 반드시 배경, 캐릭터의 모든 부위(머리, 몸통, 팔, 다리), 표정을 명확하게 그려야 합니다.

[출력 포맷]
반드시 아래 형식을 지키세요.

제목: [제목]
||||
## 1컷
**상황:** [최소 2-3문장으로 상세히: 장소, 시간, 분위기, 이전 컷과의 연결]
**캐릭터 위치:** [최소 2문장으로: 화면 내 위치, 캐릭터 간 거리, 카메라 각도]
**표정:** [최소 2문장으로: 구체적인 감정, 눈과 입의 모양, 얼굴 분위기]
**포즈:** [최소 2문장으로: 신체 자세, 팔과 다리 위치, 몸의 방향, 움직임]
**배경:** [최소 2-3문장으로: 모든 소품과 위치, 색상과 분위기, 스토리와의 연관성]
**구도:** [샷의 종류, 초점, 배경 처리]
**대사:** [누가 말하는지, 대사 내용, 톤과 감정]
**효과음:** [필요한 경우 위치와 크기]
```svg
<svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="400" fill="white"/>
  <!-- 배경 요소 먼저 그리기 -->
  <!-- 캐릭터 그리기 -->
  <!-- 표정과 포즈 표현 -->
  <!-- 효과음이나 시각적 효과 -->
</svg>
```
||||
## 2컷
(위와 동일 형식으로, 각 항목을 최소 2-3문장으로 상세히 작성)
...
"""

def save_story(title, episode, response_text, parts_data):
    """콘티를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 파일명에 사용할 수 없는 문자 제거
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title[:20])
    safe_title = safe_title.strip()
    if not safe_title:
        safe_title = "제목없음"
    filename = f"{timestamp}_{safe_title}.json"
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
    title_raw = parts[0].strip() if len(parts) > 0 else "제목 없음"
    # "제목:" 부분 제거
    if title_raw.startswith("제목:"):
        title = title_raw.replace("제목:", "").strip()
    else:
        title = title_raw
    if not title:
        title = "제목 없음"
    
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
                    
                    # 세션 상태에 저장 (저장 버튼에서 사용)
                    st.session_state['last_story'] = {
                        'title': title,
                        'episode': episode,
                        'response_text': response.text,
                        'parts': parts_data
                    }
                    
                    # 콘티 표시
                    st.success("생성 완료! 🎉")
                    display_story(title, parts_data)
                    
                    # 저장 버튼
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 콘티 저장하기", use_container_width=True, key="save_story"):
                            if 'last_story' in st.session_state:
                                story = st.session_state['last_story']
                                try:
                                    filepath = save_story(
                                        story['title'], 
                                        story['episode'], 
                                        story['response_text'], 
                                        story['parts']
                                    )
                                    st.success(f"✅ 저장 완료! 📁 {filepath.name}")
                                    st.info("💡 '저장된 콘티 보기' 탭에서 확인할 수 있습니다.")
                                    # 저장 성공 표시를 위해 세션 상태에 저장 완료 플래그 설정
                                    st.session_state['save_success'] = True
                                    st.session_state['saved_filename'] = filepath.name
                                except Exception as e:
                                    st.error(f"저장 중 오류 발생: {e}")
                                    st.exception(e)  # 상세한 에러 정보 표시
                            else:
                                st.warning("저장할 콘티가 없습니다.")
                    
                    # 저장 성공 시 디버깅 정보 표시
                    if st.session_state.get('save_success', False):
                        saved_filename = st.session_state.get('saved_filename', '')
                        with st.expander("🔍 저장 확인 (디버깅)", expanded=True):
                            st.write(f"✅ 저장 완료된 파일: {saved_filename}")
                            if STORAGE_DIR.exists():
                                files = list(STORAGE_DIR.glob("*.json"))
                                st.write(f"📁 저장된 파일 총 개수: {len(files)}")
                                if files:
                                    st.write("📋 최근 저장된 파일 목록:")
                                    for f in sorted(files, reverse=True)[:5]:
                                        st.write(f"  - {f.name}")
                                # 파일 경로 표시
                                st.write(f"📂 저장 경로: {STORAGE_DIR.absolute()}")
                            else:
                                st.error("❌ 저장 디렉토리가 없습니다!")
                                st.write(f"생성 시도: {STORAGE_DIR.absolute()}")
            
            except Exception as e:
                st.error(f"에러 발생: {e}")
    
    with tab2:
        st.title("📚 저장된 콘티 목록")
        
        # 새로고침 버튼
        if st.button("🔄 목록 새로고침", use_container_width=True):
            st.rerun()
        
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
