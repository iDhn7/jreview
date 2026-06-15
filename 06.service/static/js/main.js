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

    // 업체 정보 
    // 도로명 주소, 지번 주소
    const fullAddress = s.ADDRESS_DO || '주소 정보 없음';
    document.getElementById('biz-address').textContent = fullAddress;
    
    if(document.getElementById('map-address-display')) {
        document.getElementById('map-address-display').textContent = s.ADDRESS_JI || '정보 없음';
    }

    // 전화번호
    if(document.getElementById('biz-phone')) {
        document.getElementById('biz-phone').textContent = s.PHONE || '등록된 번호 없음';
    }

    // 주차 정보 스타일 처리
    const parkingEl = document.getElementById('biz-parking');
    if (parkingEl) {
        parkingEl.textContent = s.PARKING || '주차 정보 없음';
        if (s.PARKING && s.PARKING.includes('불가')) {
            parkingEl.style.color = "var(--neg)"; // 불가일 땐 빨간색 
        } else {
            parkingEl.style.color = "var(--pos)"; // 가능일 땐 초록색
        }
    }

    // 편의성 콤마로 쪼개서 배지 달기
    const amenityBox = document.getElementById('biz-amenities-box');
    if (amenityBox) {
        amenityBox.innerHTML = "";
        if (s.AMENITY) {
            // 콤마로 쪼개기 
            const amenityArray = s.AMENITY.split(',');
            
            amenityArray.forEach(item => {
                const trimmed = item.trim();
                if (trimmed) {
                    // 메모리에 span 태그를 동적으로 구워내서 꽂아버리기
                    const badge = document.createElement('span');
                    badge.style = "display: inline-flex; align-items: center; gap: 4px; background: var(--bg); border: 1px solid var(--border-2); color: var(--text-2); font-weight: 500; font-size: 12px; padding: 4px 10px; border-radius: 100px;";
                    badge.textContent = trimmed;
                    amenityBox.appendChild(badge);
                }
            });
        } else {
            amenityBox.innerHTML = `<span style="color: var(--text-3); font-size: 12px;">정보 없음</span>`;
        }
    }
    // 영업시간 세팅
    const hoursTooltip = document.getElementById('biz-hours-tooltip');
    if (hoursTooltip) {
        if (s.BUSINESS_HOURS) {
            hoursTooltip.innerHTML = `<p>${s.BUSINESS_HOURS.replace(/\n/g, '<br>')}</p>`;
        } else {
            hoursTooltip.innerHTML = `<p>등록된 영업시간 정보가 없습니다.</p>`;
        }
    }
    
    // 카카오맵 버튼 클릭 이벤트
    const mapBtn = document.getElementById('btn-kakaomap');
    if (mapBtn) {
        mapBtn.onclick = function() {
            window.open(`https://map.kakao.com/?q=${encodeURIComponent(fullAddress)}`, '_blank');
        };
    }
  
    }

  // 2. 메뉴 정보 리스트 동적 생성 (view_menu.html 연동)
  const menuContainer = document.getElementById('menuGrid');
  
  if (menuContainer && data.menus) {
    if (data.menus.length === 0) {
      menuContainer.innerHTML = '<div class="no-data" style="grid-column: 1/-1; text-align: center; color: var(--text-3); padding: 20px;">등록된 메뉴 정보가 없습니다.</div>';
    } else {
      
      // 감성 평가 스타일
      const sentimentColors = {
        pos: { bg: '#E6F5ED', border: '#A7F3D0', text: '#1A7A4A', label: '긍정반응 높음' },
        neutral: { bg: '#F5F0E8', border: '#E8DCC8', text: '#5C4A2A', label: '보통' },
        neg: { bg: '#FAE8E6', border: '#FECACA', text: '#C0392B', label: '부정반응 있음' },
      };

      // 1등 메뉴의 언급 횟수(CNT)를 구하여 비율바(Bar)의 분모 기준으로 사용합니다.
      // (쿼리에서 이미 CNT DESC로 정렬되어 오므로 0번째가 무조건 최대값입니다.)
      const maxMention = data.menus[0].CNT || 1;

      menuContainer.innerHTML = data.menus.map(m => {
        // 1. DB 필드 값 매핑 변수 선언
        const mName = m.MENU_NAME || '이름 없음';
        const mPrice = m.MENU_PRICE ? Number(m.MENU_PRICE).toLocaleString() : '가격 정보 없음';
        const mMention = m.CNT || 0;
        
        // 2. [UI 기믹] DB의 BEST 컬럼값 유무에 따라 상단 우측 배지(tag) 동적 생성
        const mTag = m.BEST ? '대표메뉴' : '';

        // 3. [AI 연동] 리뷰 언급 횟수나 식당 긍정율에 비례해 감성 상태를 안전하게 가공
        // (우선 기본 데이터 분석 가이드에 맞춰 언급이 많고 평점이 높으면 'pos', 데이터가 적당하면 'neutral'로 안전 분기)
        let mSentiment = 'neutral';
        if (m.BEST || mMention > (maxMention * 0.5)) {
          mSentiment = 'pos'; // 언급율이 상위 50% 이상이거나 대표메뉴면 긍정반응 높음 바인딩
        }

        const sc = sentimentColors[mSentiment];
        
        // 언급 빈도 수 바
        const barWidth = maxMention > 0 ? Math.min(100, Math.round(mMention / maxMention * 100)) : 0;
        // 언급이 0회일 때는 중립적인 연한 회색 바
        const progressBgColor = mMention === 0 ? '#CBD5E1' : sc.text;

        return `
          <div style="background: var(--bg-card); border: 1px solid var(--border-2); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 6px; position: relative;">
            
            ${mTag ? `<span style="position:absolute; top:10px; right:10px; background:${sc.bg}; color:${sc.text}; border:1px solid ${sc.border}; font-size:10px; font-weight:700; padding:2px 7px; border-radius:100px;">${mTag}</span>` : ''}
            
            <div style="font-size: 14px; font-weight: 700; color: var(--text-1); padding-right: ${mTag ? '65px' : '0'};">${mName}</div>
            
            <div style="font-size: 16px; font-weight: 700; color: var(--text-2); font-family: 'Noto Sans KR', serif;">${mPrice}${mPrice !== '무료' && m.MENU_PRICE ? '원' : ''}</div>
            
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 2px;">
              <span style="font-size: 11px; color: var(--text-3);">리뷰 언급 ${mMention}회</span>
              <span style="font-size: 10px; font-weight: 600; color: ${sc.text};">${sc.label}</span>
            </div>
            
            <div style="height: 4px; background: var(--border-2); border-radius: 2px; overflow: hidden; width: 100%;">
              <div style="height:100%; width:${barWidth}%; background:${progressBgColor}; border-radius:2px;"></div>
            </div>

          </div>
        `;
      }).join('');
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