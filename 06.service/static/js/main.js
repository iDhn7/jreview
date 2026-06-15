// static/js/main.js

// 카테고리 필터 및 검색 시 사용할 전역 변수 (Flask에서 받아온 데이터로 초기화)
let businesses = [];

document.addEventListener("DOMContentLoaded", function () {
  // 1. Flask가 전달한 데이터를 시스템 포맷에 맞게 매핑
  if (typeof dbBusinesses !== 'undefined') {
    businesses = dbBusinesses.map(b => ({
      id: b.STORE_CODE,
      name: b.STORE_NAME,
      category: b.CATEGORY,
      location: b.AREA, // '전북대', '신시가지', '객사', '한옥마을' 등 상권 정보
      rating: b.STAR || 0,
      reviews: b.REVIEW_CNT || 0,
      imageUrl: b.STORE_IMAGE_URL || '/static/img/default.jpg',
      posRate: b.PN_RATE || 0
    }));
  }

  // 2. 메인 페이지 초기 화면 그리기
  renderBusinessGrid(businesses);

  // 3. 메인 페이지 하단 [전주 트렌드 분석] 그래프 그리기 호출
  if (typeof dbTrendArea !== 'undefined') {
    initMainTrendCharts(dbTrendArea, dbTrendSeason, dbTrendRecent);
  }
});

function initMainTrendCharts(areaData, seasonData, recentData) {
  console.log("메인 하단 상권 트렌드 데이터 로드 완료");
  // 차트 생성이나 통계치 동적 조작 플러그인이 있다면 여기에 추가 기술 가능
}

// -------------------------------------------------------------\n// [MAIN PAGE] 카테고리 & 상권 필터링 시스템
function filterCategory(categoryOrArea) {
  // 활성화된 칩 스타일 초기화 처리
  document.querySelectorAll('.filter-chip').forEach(chip => chip.classList.remove('active'));
  
  const filtered = businesses.filter(b => {
    if (categoryOrArea === '전체') return true;
    
    // 위치(상권) 또는 음식 카테고리에 매칭되는지 검사
    if (['전북대', '신시가지', '객사', '한옥마을'].includes(categoryOrArea)) {
      return b.location === categoryOrArea; // 상권 필터링
    } else {
      return b.category.includes(categoryOrArea); // 음식 카테고리 필터링
    }
  });

  renderBusinessGrid(filtered.length ? filtered : businesses);
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
        <img class=\"b-img\" src=\"${b.imageUrl}\" alt=\"${b.name}\">
        <span class="b-category-badge">${b.category}</span>
      </div>
      <div class=\"b-info\">
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

// -------------------------------------------------------------\n// [DETAIL PAGE] 비동기 데이터 로드 및 전환 연동 (view_*.html 연동)
function goToDetail(storeCode) { // 
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

// 상세 데이터 DOM 조작 및 동적 할당 함수
function renderStoreDetail(data) {
  // [보강] 데이터가 유효한지 안전 검사
  if (!data) return;

  // 1. 가게 기본 정보 바인딩 (view_header.html, view_info.html 등 연동)
  if (data.store) {
    const s = data.store;
    
    // 텍스트 및 수치 매핑 (안정성을 위해 기본값 || 0 처리 추가)
    document.getElementById('detail-name').textContent = s.STORE_NAME || '이름 없음';
    document.getElementById('detail-category').textContent = s.CATEGORY || '-';
    document.getElementById('detail-rating').textContent = Number(s.STAR || 0).toFixed(1);
    document.getElementById('detail-reviews').textContent = `리뷰 ${s.REVIEW_CNT || 0}개`;
    document.getElementById('detail-location').textContent = s.AREA || '-';
    document.getElementById('detail-pos-pct').textContent = `긍정 ${Math.round(s.PN_RATE || 0)}%`;

    // 카테고리별 감성 이모지 자동 매핑
    let icon = '📍';
    if (s.CATEGORY && s.CATEGORY.includes('한식')) icon = '🍚';
    else if (s.CATEGORY && (s.CATEGORY.includes('카페') || s.CATEGORY.includes('디저트') || s.CATEGORY.includes('빵'))) icon = '☕';
    else if (s.CATEGORY && s.CATEGORY.includes('일식')) icon = '🍣';
    document.getElementById('detail-icon').textContent = icon;

    // 별점 그래픽(★) 처리
    const starScore = Math.round(Number(s.STAR || 0));
    const starsText = '★'.repeat(starScore) + '☆'.repeat(Math.max(0, 5 - starScore));
    document.getElementById('detail-stars').textContent = starsText;
  } // 👈 [수정] 누락되었던 if (data.store) 닫는 중괄호 추가

  // 2. 메뉴 정보 리스트 동적 생성 (view_menu.html 연동)
  const menuContainer = document.getElementById('det-menu-list');
  if (menuContainer && data.menus) {
    if (data.menus.length === 0) {
      menuContainer.innerHTML = '<div class="no-data">등록된 메뉴 정보가 없습니다.</div>';
    } else {
      menuContainer.innerHTML = data.menus.map(m => `
        <div class="menu-item">
          <div class="menu-name-wrap">
            <span class="menu-name">${m.MENU_NAME}</span>
            ${m.BEST ? '<span class="menu-badge">대표</span>' : ''}
          </div>
          <div style="margin-left:auto; display:flex; gap:20px; align-items:center;">
            <span class="menu-price">${Number(m.MENU_PRICE || 0).toLocaleString()}원</span>
            <span class="menu-mentions">💬 언급 ${m.CNT || 0}회</span>
          </div>
        </div>
      `).join('');
    }
  }

  // 3. 실제 리뷰 샘플 리스트 동적 생성 (view_sample.html 연동)
  const reviewContainer = document.getElementById('det-review-list');
  if (reviewContainer && data.reviews) {
    if (data.reviews.length === 0) {
      reviewContainer.innerHTML = '<div class="no-data">수집된 리뷰가 존재하지 않습니다.</div>';
    } else {
      reviewContainer.innerHTML = data.reviews.map(r => {
        const isPos = r.REVIEW_PN === 'P';
        const className = isPos ? 'review-pos' : 'review-neg';
        const prefix = isPos ? '👍 긍정 수집 후기' : '👎 개선 요구 후기';
        
        return `
          <div class="review-item ${className}">
            <div class="review-label">${prefix} (점수: ${Number(r.PN_SCORE || 0).toFixed(2)})</div>
            <div class="review-text">${r.CONTENT}</div>
          </div>
        `;
      }).join('');
    }
  }
}

// -------------------------------------------------------------\n// [COMMON] 내부 페이지 라우팅 전환 함수 (원본 순수 기능)
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const targetPage = document.getElementById(`page-${pageId}`);
  if (targetPage) {
    targetPage.classList.add('active');
  }
}

// -------------------------------------------------------------\n// [COMMON INTERACTION] 모달, 팝업, RAG UI 애니메이션 제어 (보존된 원본 핵심 기능)
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
  if (!q) return;

  showPage('main');

  const ql = q.toLowerCase();
  const filtered = businesses.filter(b =>
    b.name.includes(q) ||
    b.category.toLowerCase().includes(ql) ||
    b.location.includes(q)
  );

  renderBusinessGrid(filtered.length ? filtered : businesses);

  const countEl = document.querySelector('.section-header .section-title + div span');
  if (countEl) {
    if (filtered.length) {
      countEl.textContent = `"${q}" 검색결과 ${filtered.length}개 업체`;
    } else {
      countEl.textContent = `"${q}" 결과 없음 — 전체 표시 중`;
    }
  }
}

/* ===== RAG AI 어시스턴트 검색 및 인터랙션 오버레이 활성화 ===== */
function ragSearch() {
  const input = document.getElementById('ragInput');
  if (!input || !input.value.trim()) return;

  const query = input.value.trim();
  
  // 오버레이 활성화 활싱화
  const overlay = document.getElementById('ragOverlay');
  const backdrop = document.getElementById('ragOverlayBackdrop');
  if (overlay) overlay.classList.add('open');
  if (backdrop) backdrop.classList.add('open');

  const body = document.getElementById('ragOverlayBody');
  if (body) {
    body.innerHTML = `
      <div class="chat-msg user"><div class="msg-box">${query}</div></div>
      <div class="chat-msg ai"><div class="msg-box loading">✦ AI가 리뷰 빅데이터 분석을 토대로 답변을 구성하고 있습니다...</div></div>
    `;
  }
  input.value = '';
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