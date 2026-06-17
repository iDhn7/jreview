// 📝 static/js/main_dashboard.js

// 카테고리 필터 및 검색 시 사용할 전역 변수 (Flask에서 받아온 데이터로 초기화)
let businesses = [];
let currentFilteredBusinesses = []; // 💡 [추가] 현재 필터링/검색되어 화면에 노출 대상인 데이터를 기억하는 배열

document.addEventListener("DOMContentLoaded", function () {
  // 1. Flask가 전달한 데이터를 시스템 포맷에 맞게 매핑
  if (typeof dbBusinesses !== 'undefined') {
    businesses = dbBusinesses.map(b => ({
      id: b.id,                 // 백엔드의 "id": biz.get('STORE_CODE') 와 매핑
      name: b.name,             // 백엔드의 "name": biz.get('STORE_NAME') 와 매핑
      category: b.category,     // 백엔드의 "category" 와 매핑
      location: b.location,     // 백엔드의 "location": biz.get('AREA') 와 매핑
      address: b.address || '', // 백엔드의 "address": biz.get('ADDRESS_DO') 와 매핑
      rating: b.rating || 0,    // 백엔드의 "rating" 와 매핑
      reviews: b.reviews || 0,  // 백엔드의 "reviews" 와 매핑
      imageUrl: b.image_url || '/static/img/default.jpg', // 백엔드의 "image_url" 와 매핑
      posRate: b.pos || 0       // 백엔드의 "pos" 와 매핑
    }));
  }

  // 2. 메인 페이지 초기 화면 그리기
  currentFilteredBusinesses = businesses.slice(0, 9);

  const sortSelect = document.getElementById('sortSelect');
  if (sortSelect) sortSelect.value = 'posRate'; // 기본값 긍정순 설정

  // 정렬을 한 번 실행해서 초기 화면 정렬 렌더링
  handleSort();

  // 3. 메인 페이지 하단 [전주 트렌드 분석] 그래프 그리기 호출
  if (typeof dbTrendArea !== 'undefined') {
    initMainTrendCharts(dbTrendArea, dbTrendSeason, dbTrendRecent);
  }
});

function initMainTrendCharts(areaData, seasonData, recentData) {
  console.log("메인 하단 상권 트렌드 데이터 로드 완료");
  // 차트 생성이나 통계치 동적 조작 플러그인이 있다면 여기에 추가 기술 가능
}

// -------------------------------------------------------------
// [MAIN PAGE] 카테고리 & 상권 필터링 시스템
function filterCategory(categoryOrArea) {
  // 활성화된 칩 스타일 초기화 처리
  document.querySelectorAll('.filter-chip').forEach(chip => chip.classList.remove('active'));
  
  // 💡 기타 카테고리를 판별하기 위한 기준 정의 (나머지 주요 카테고리 목록)
  const mainCategories = ['한식', '일식', '양식', '카페', '중식'];

  const filtered = businesses.filter(b => {
    // 1. '전체'를 누른 경우 모두 반환
    if (categoryOrArea === '전체') return true;
    
    // 2. 위치(상권) 필터링
    if (['전북대', '신시가지', '객사', '한옥마을'].includes(categoryOrArea)) {
      return b.location === categoryOrArea;
    } 
    
    // 3. 💡 '기타' 카테고리를 누른 경우 처리
    if (categoryOrArea === '기타') {
      // 업체를 분류할 때 주요 카테고리가 매칭되지 않는 항목들을 걸러냄
      return !mainCategories.some(mainCat => b.category.includes(mainCat));
    } 
    
    // 4. 일반 음식 카테고리 필터링 (한식, 일식, 양식, 카페, 중식)
    return b.category.includes(categoryOrArea);
  });

  // 필터링된 배열을 기억하고 정렬 기믹 호출
  currentFilteredBusinesses = filtered;

  // 📢 [추가] index_list.html의 제목과 검색 결과 건수를 동적으로 갱신합니다.
  const titleEl = document.getElementById('listSectionTitle');
  const countEl = document.getElementById('totalCount');
  
  if (titleEl) {
    if (categoryOrArea === '전체') {
      titleEl.textContent = '전체 업체 목록';
    } else {
      // 상권 키워드인지 카테고리 키워드인지에 따라 조사 분기 세팅
      const suffix = ['전북대', '신시가지', '객사', '한옥마을'].includes(categoryOrArea) ? ' 상권 분석 결과' : ' 분석 결과';
      titleEl.textContent = `"${categoryOrArea}"${suffix}`;
    }
  }
  if (countEl) {
    countEl.textContent = `총 ${filtered.length.toLocaleString()}개 업체`;
  }

  handleSort();
}

// 메인 Grid 렌더러 (index_list.html 연동)
function renderBusinessGrid(dataList) {
  const grid = document.getElementById('businessGrid');
  if (!grid) return;

  if (!dataList || dataList.length === 0) {
    grid.innerHTML = '<div class="no-data">조건에 맞는 업체가 없습니다.</div>';
    return;
  }

  grid.innerHTML = dataList.map(b => `
    <div class="business-card" onclick="goToDetail('${b.id}')">
      <div class="b-img-wrap">
        <img class="b-img" src="${b.imageUrl}" alt="${b.name}">
        <span class="b-category-badge">${b.category}</span>
      </div>
      <div class="b-info">
        <div class="b-name-row">
          <span class="b-name">${b.name}</span>
          <span class="b-rating">★ ${Number(b.rating).toFixed(1)}</span>
        </div>
        <div class="b-meta">
          <span>📍 ${b.location}</span>
          <span>•</span>
          <span>리뷰 ${b.reviews}개</span>
        </div>
        <div class="b-sentiment-bar-wrap">
          <div class="b-sentiment-bar" style="width: ${b.posRate}%"></div>
        </div>
        <div class="b-sentiment-labels">
          <span class="pos-lbl">긍정 ${b.posRate}%</span>
          <span class="neg-lbl">부정 ${100 - b.posRate}%</span>
        </div>
      </div>
    </div>
  `).join('');
}

// -------------------------------------------------------------
// [DETAIL PAGE] 비동기 데이터 로드 및 전환 연동 (view_*.html 연동)
function goToDetail(storeCode) { 
  // 1. 화면 전환 애니메이션 및 최상단 스크롤 (원래 기능 보존)
  showPage('detail');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // 2. 백엔드에서 실시간 상세 데이터 Fetch 요청 (?code= 형식 맞춤)
  fetch(`/api/store?code=${storeCode}`)
    .then(res => {
      if (!res.ok) throw new Error("네트워크 응답 에러");
      return res.json();
    })
    .then(data => {
      // 🚀 [수정] 렌더링 전 로그를 미리 출력하여 화면 에러 유무와 무관하게 데이터 흐름 추적이 가능하게 함
      console.log("====== DB 수신 데이터 검증 ======");
      console.log("가게 코드:", storeCode);
      console.log("넘어온 전체 JSON 객체:", data);
      console.log("=================================");

      // 비동기로 받아온 DB 데이터를 상세 UI 컴포넌트들에 주입
      renderStoreDetail(data);
    })
    .catch(err => {
      console.error("상세 정보 로드 실패:", err);
      alert("상세 데이터를 가져오는 중 오류가 발생했습니다.");
    });
}

// -------------------------------------------------------------
// [COMMON] 내부 페이지 라우팅 전환 함수 (원본 순수 기능)
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const targetPage = document.getElementById(`page-${pageId}`);
  if (targetPage) {
    targetPage.classList.add('active');
  }
}

// -------------------------------------------------------------
// [COMMON INTERACTION] 모달, 팝업, RAG UI 애니메이션 제어 (보존된 원본 핵심 기능)
function openReviewPopup() {
  const pop = document.getElementById('reviewPopup');
  const overlay = document.getElementById('ragOverlayBackdrop');
  if (pop) pop.classList.add('open');
  if (overlay) overlay.classList.add('open');
}

function closeReviewPopup() {
  const pop = document.getElementById('reviewPopup');
  const overlay = document.getElementById('ragOverlayBackdrop');
  if (pop) pop.classList.remove('open');
  if (overlay) overlay.classList.remove('open');
}

/* ===== 우상단 nav 검색 (기존의 단순 프론트 필터링 기능 유지) ===== */
function navSearch(q) {
  q = (q || '').trim();
  
  const titleEl = document.getElementById('listSectionTitle');
  const countEl = document.getElementById('totalCount');

  if (!q) {
    currentFilteredBusinesses = [...businesses]; // 전체 데이터로 초기화
    
    // 📢 [추가] 빈 검색어 입력 시 초기 타이틀 상태로 리셋 복구
    if (titleEl) titleEl.textContent = '전체 업체 목록';
    if (countEl) countEl.textContent = `총 ${businesses.length.toLocaleString()}개 업체`;
    
    handleSort(); // 현재 정렬 기준에 맞춰 전체 다시 그리기
    return;
  }

  showPage('main');

  const ql = q.toLowerCase();
  const filtered = businesses.filter(b =>
    b.name.toLowerCase().includes(ql) ||          // 1. 가게 이름 검색
    b.category.toLowerCase().includes(ql) ||      // 2. 카테고리 검색
    b.location.toLowerCase().includes(ql) ||         // 3. 상권명 검색
    (b.address && b.address.toLowerCase().includes(ql)) // 4. 주소 검색
  );

  // 검색 결과가 0개여도 전체 목록으로 튕기지 않고 빈 배열 그대로 전달
  currentFilteredBusinesses = filtered;

  // 📢 [추가/수정] 검색 단어 유입 시 index_list.html 헤더 문자열 연동 제어
  if (titleEl) {
    titleEl.textContent = `"${q}" 검색 결과`;
  }
  if (countEl) {
    if (filtered.length > 0) {
      countEl.textContent = `총 ${filtered.length.toLocaleString()}개 업체 조회`;
    } else {
      countEl.textContent = '검색 결과 없음';
    }
  }

  handleSort();
}

// [MAIN PAGE] 실시간 데이터 정렬 시스템 
function handleSort() {
  const sortSelect = document.getElementById('sortSelect');
  if (!sortSelect || !currentFilteredBusinesses || currentFilteredBusinesses.length === 0) {
    // 데이터가 없으면 정렬하지 않고 0개 화면 출력
    renderBusinessGrid(currentFilteredBusinesses);
    return;
  }

  const sortValue = sortSelect.value; // 'posRate', 'reviews', 'rating'

  // 원본 데이터가 훼손되지 않도록 복사본(...배열)을 만들어 정렬 진행 (내림차순 정렬 b - a)
  const sortedData = [...currentFilteredBusinesses].sort((a, b) => {
    if (sortValue === 'posRate') {
      return b.posRate - a.posRate;  // 긍정 비율 높은 순
    } else if (sortValue === 'reviews') {
      return b.reviews - a.reviews;  // 리뷰 많은 순
    } else if (sortValue === 'rating') {
      return b.rating - a.rating;    // 별점 높은 순
    }
    return 0;
  });

  // 정렬이 완료된 데이터셋으로 화면 갱신
  renderBusinessGrid(sortedData);
}

/* ===== RAG AI 어시스턴트 검색 및 인터랙션 오버레이 활성화 ===== */
/**
 * 1. 메인 화면의 메인 검색창(돋보기 버튼 등)에서 RAG 검색을 시작할 때 호출되는 진입 함수
 */
function ragSearch() {
  const input = document.getElementById('ragInput');
  if (!input) return;

  // 입력값이 있으면 그 값을 쓰고, 없으면 기본 디폴트 문구
  let query = input.value.trim();
  if (!query) {
    query = "전주 맛집 추천해줘"; // 기본 질문 입력
  }

  input.value = ''; // 메인 입력창 초기화

  // 오버레이 창을 열면서 질문 전달
  openRagOverlay(query);
}

/**
 * 2. RAG 오버레이 창을 열어주는 스위치 함수 (초기 질문이 담겨있다면 즉시 검색 실행)
 */
function openRagOverlay(initialQuery = '') {
  const overlay = document.getElementById('ragOverlay');
  const backdrop = document.getElementById('ragOverlayBackdrop');
  
  if (overlay) overlay.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  
  // 만약 메인 검색창에서 질의어가 들어왔다면, 대화창을 초기화하고 즉시 RAG API 기동
  if (initialQuery.trim() !== '') {
    const body = document.getElementById('ragOverlayBody');
    if (body) body.innerHTML = ''; // 기존 대화 요소를 깔끔히 비움
    
    executeRagQuery(initialQuery);
  }
}

/**
 * 3. RAG 오버레이 팝업창 닫기 스위치
 */
function closeRagOverlay() {
  const overlay = document.getElementById('ragOverlay');
  const backdrop = document.getElementById('ragOverlayBackdrop');
  
  if (overlay) overlay.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
}

/**
 * 4. 챗봇 오버레이 창 내부 하단 푸터(Footer)의 [전송] 버튼이나 엔터 키 입력 시 추가 질의를 처리하는 함수
 */
function sendRagOverlayMessage() {
  const input = document.getElementById('ragOverlayInput');
  if (!input || !input.value.trim()) return;

  const query = input.value.trim();
  input.value = ''; // 챗봇 내부 입력창 비우기
  
  // 연속형 대화 형태로 기존 창에 누적하여 쿼리 실행
  executeRagQuery(query);
}

/**
 * 5. [핵심 엔진] Flask 블루프린트 백엔드와 비동기 통신하여 대화창 UI에 데이터를 동적 렌더링하는 함수
 */
function executeRagQuery(query) {
  const body = document.getElementById('ragOverlayBody');
  if (!body) return;

  // [STEP A] 사용자가 입력한 질문 블록을 대화창 화면에 추가
  const userMsgHtml = `
    <div class="chat-msg user">
      <div class="msg-box">${query}</div>
    </div>
  `;
  body.innerHTML += userMsgHtml;
  
  // 로딩 상태 박스를 제어하기 위한 고유 ID 발급
  const loadingId = 'loading_' + Date.now();
  
  // [STEP B] AI 빅데이터 연산 중임을 알리는 스켈레톤 로딩 애니메이션 추가
  const aiLoadingHtml = `
    <div class="chat-msg ai" id="${loadingId}">
      <div class="msg-box loading">
        ✦ AI가 리뷰 빅데이터 분석을 토대로 답변을 구성하고 있습니다...
      </div>
    </div>
  `;
  body.innerHTML += aiLoadingHtml;
  body.scrollTop = body.scrollHeight; // 새로운 대화 유입에 맞춰 스크롤을 맨 아래로 고정

  // [STEP C] Fetch API를 이용하여 새로 리팩토링한 블루프린트 라우터(/api/rag)로 비동기 POST 통신 요청
  fetch('/api/rag', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query: query })
  })
  .then(res => {
    if (!res.ok) throw new Error('네트워크 응답 시스템에 오류가 발생했습니다.');
    return res.json();
  })
  .then(data => {
    // 백엔드 응답이 완료되었으므로 로딩 애니메이션 엘리먼트 제거
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();

    // [STEP D] RAGManager가 돌려준 가공된 데이터 덩어리를 HTML 템플릿으로 구조화
    let aiResponseHtml = `
      <div class="chat-msg ai">
        <div class="msg-box">
          <div class="ai-answer" style="white-space: pre-wrap; line-height: 1.6; font-size: 13px;">${data.answer}</div>
    `;

    // 2) 출처 및 기반 데이터 (실제 고객 리뷰 팩트 체크 영역) 연동
    if (data.referenced_reviews && data.referenced_reviews.length > 0) {
      aiResponseHtml += `
        <div class="rag-reference-section" style="margin-top: 12px; padding-top: 8px; border-top: 1px dashed #e2e8f0;">
          <div style="font-size: 11px; font-weight: 700; color: #718096; margin-bottom: 4px;">🎯 분석에 참조된 실제 리뷰 근거:</div>
          <ul style="margin: 0; padding-left: 16px; font-size: 11px; color: #4a5568; display: flex; flex-direction: column; gap: 4px;">
            ${data.referenced_reviews.map(rev => `<li>"${rev}"</li>`).join('')}
          </ul>
        </div>
      `;
    }

    // 3) 추천 매장 카드 그리드 연동 (상권 및 긍정율 데이터 매핑)
    // 🚀 [수정 사항]: 클릭 시 상세페이지 전환 함수 'goToDetail'을 호출하고, 창을 닫도록 보완했습니다.
    if (data.recommendations && data.recommendations.length > 0) {
      aiResponseHtml += `
        <div class="rag-recommend-section" style="margin-top: 14px;">
          <div style="font-size: 11px; font-weight: 700; color: var(--primary, #C8530A); margin-bottom: 6px;">✨ 빅데이터 기반 추천 맛집:</div>
          <div class="rec-grid" style="display: flex; flex-direction: column; gap: 6px;">
            ${data.recommendations.map(store => `
              <div class="rec-store-item" 
                   onclick="closeRagOverlay(); goToDetail('${store.store_code}');" 
                   style="background: #fdfaf7; border: 1px solid #fbdcbd; border-radius: 6px; padding: 6px 10px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.2s;"
                   onmouseover="this.style.background='#fbf1e6'"
                   onmouseout="this.style.background='#fdfaf7'">
                <div>
                  <span style="font-weight: 700; font-size: 12px; color: var(--text, #2D3748);">${store.store_name}</span>
                  <span style="font-size: 10px; color: var(--text-3, #718096); margin-left: 4px;">| ${store.category} · ${store.address}</span>
                </div>
                <div style="font-size: 11px; font-weight: 700; color: var(--pos, #2ECC71);">👍 긍정율 ${store.pn_rate}%</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    // 4) 후속 유도용 AI 스마트 추천 질문 칩(Chip) 바인딩
    if (data.recommended_queries && data.recommended_queries.length > 0) {
      aiResponseHtml += `
        <div class="rag-chips-section" style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px;">
          ${data.recommended_queries.map(chipQuery => `
            <button class="rag-suggest-chip" onclick="executeRagQuery('${chipQuery.replace(/'/g, "\\'")}')" 
                    style="background: #ffffff; border: 1px solid #cbd5e0; border-radius: 14px; padding: 4px 10px; font-size: 11px; color: #4a5568; cursor: pointer; transition: all 0.2s; font-weight: 500;">
              💡 ${chipQuery}
            </button>
          `).join('')}
        </div>
      `;
    }

    aiResponseHtml += `
        </div>
      </div>
    `;

    // 컴포넌트를 조립한 최종 답변 덩어리를 채팅창에 추가하고 하단 스크롤
    body.innerHTML += aiResponseHtml;
    body.scrollTop = body.scrollHeight;
  })
  .then(() => {
    // 🚀 스크롤 동작이 유실되는 컴파일 구조를 방지하기 위해 한 번 더 스크롤 높이 세팅 보완
    body.scrollTop = body.scrollHeight;
  })
  .catch(err => {
    console.error("❌ RAG 엔진 비동기 통신 에러 발생:", err);
    // 예외 발생 시 로딩 지우고 에러 알림 처리
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();
    
    body.innerHTML += `
      <div class="chat-msg ai">
        <div class="msg-box" style="color: #E53E3E; font-weight: 600;">
          ⚠️ 서버와 실시간 데이터 분석을 연결하는 과정에서 일시적인 장애가 발생했습니다. 잠시 후 다시 시도해 주세요.
        </div>
      </div>
    `;
    body.scrollTop = body.scrollHeight;
  });
}

function ragPreset(el) {
  const txt = el.textContent || '';
  const input = document.getElementById('ragInput');
  if (input) {
    input.value = txt;
    ragSearch();
  }
}

function closeRagOverlay() {
  document.getElementById('ragOverlay').classList.remove('open');
  document.getElementById('ragOverlayBackdrop').classList.remove('open');
}