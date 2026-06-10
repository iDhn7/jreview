const businesses = [
  { id:1, name:'풍년제과', icon:'🥐', category:'카페/빵집', location:'완산구 전동', reviews:1243, rating:4.2, pos:78, neg:22, desc:'전주 대표 빵집. 초코파이가 유명.',
    menu:[
      { name:'초코파이', price:'1,500', mention:312, sentiment:'pos', tag:'대표메뉴' },
      { name:'단팥빵', price:'1,800', mention:198, sentiment:'pos', tag:'' },
      { name:'소보로빵', price:'1,500', mention:145, sentiment:'pos', tag:'' },
      { name:'크림치즈빵', price:'2,200', mention:89, sentiment:'pos', tag:'' },
      { name:'흑임자롤', price:'2,500', mention:67, sentiment:'neutral', tag:'' },
      { name:'카스테라', price:'3,000', mention:54, sentiment:'neg', tag:'' },
    ]
  },
  { id:2, name:'한국집', icon:'🍚', category:'한식', location:'완산구 풍남동', reviews:2841, rating:4.5, pos:85, neg:15, desc:'전주비빔밥 원조 맛집.',
    menu:[
      { name:'전주비빔밥', price:'13,000', mention:1240, sentiment:'pos', tag:'대표메뉴' },
      { name:'돌솥비빔밥', price:'14,000', mention:782, sentiment:'pos', tag:'' },
      { name:'육회비빔밥', price:'16,000', mention:431, sentiment:'pos', tag:'' },
      { name:'콩나물국밥', price:'9,000', mention:256, sentiment:'pos', tag:'' },
      { name:'한정식 세트', price:'28,000', mention:189, sentiment:'pos', tag:'' },
    ]
  },
  { id:3, name:'전주향교', icon:'🏯', category:'관광지', location:'완산구 교동', reviews:674, rating:4.3, pos:80, neg:20, desc:'조선시대 향교. 포토스팟으로 유명.',
    menu:[
      { name:'입장권 (성인)', price:'무료', mention:210, sentiment:'pos', tag:'' },
      { name:'문화해설 투어', price:'2,000', mention:98, sentiment:'pos', tag:'' },
      { name:'전통체험 프로그램', price:'5,000', mention:74, sentiment:'pos', tag:'' },
    ]
  },
  { id:4, name:'팔복예술공장', icon:'🎨', category:'체험', location:'덕진구 팔복동', reviews:412, rating:4.0, pos:72, neg:28, desc:'폐공장 리노베이션 복합문화공간.',
    menu:[
      { name:'기본 입장', price:'무료', mention:180, sentiment:'pos', tag:'' },
      { name:'도자기 체험', price:'15,000', mention:134, sentiment:'pos', tag:'' },
      { name:'판화 체험', price:'12,000', mention:88, sentiment:'pos', tag:'' },
      { name:'전시 특별관람', price:'5,000', mention:56, sentiment:'neutral', tag:'' },
    ]
  },
  { id:5, name:'전동성당카페', icon:'☕', category:'카페', location:'완산구 전동', reviews:889, rating:4.4, pos:83, neg:17, desc:'전동성당 뷰 카페. 분위기 최고.',
    menu:[
      { name:'아메리카노', price:'5,500', mention:320, sentiment:'pos', tag:'대표메뉴' },
      { name:'라떼', price:'6,500', mention:245, sentiment:'pos', tag:'' },
      { name:'성당뷰 케이크', price:'8,000', mention:198, sentiment:'pos', tag:'' },
      { name:'전주막걸리 라떼', price:'7,000', mention:132, sentiment:'pos', tag:'' },
      { name:'수제 쿠키 세트', price:'9,000', mention:87, sentiment:'neutral', tag:'' },
    ]
  },
  { id:6, name:'한옥마을게스트하우스', icon:'🛏', category:'숙박', location:'완산구 풍남동', reviews:521, rating:4.1, pos:74, neg:26, desc:'한옥마을 내 감성 게스트하우스.',
    menu:[
      { name:'한옥 도미토리', price:'35,000', mention:210, sentiment:'pos', tag:'' },
      { name:'한옥 온돌 1인실', price:'65,000', mention:178, sentiment:'pos', tag:'' },
      { name:'한옥 프리미엄 2인실', price:'120,000', mention:89, sentiment:'pos', tag:'' },
      { name:'조식 포함 패키지', price:'+10,000', mention:64, sentiment:'pos', tag:'' },
    ]
  },
  { id:7, name:'전주막걸리골목', icon:'🍶', category:'한식', location:'완산구 서학동', reviews:1102, rating:4.3, pos:81, neg:19, desc:'파전과 막걸리의 성지.',
    menu:[
      { name:'전주 막걸리', price:'4,000', mention:512, sentiment:'pos', tag:'대표메뉴' },
      { name:'녹두 빈대떡', price:'12,000', mention:398, sentiment:'pos', tag:'' },
      { name:'파전', price:'10,000', mention:345, sentiment:'pos', tag:'' },
      { name:'도토리묵무침', price:'8,000', mention:198, sentiment:'pos', tag:'' },
      { name:'모둠전 세트', price:'22,000', mention:134, sentiment:'pos', tag:'' },
    ]
  },
  { id:8, name:'전주공예품전시관', icon:'🏺', category:'체험', location:'완산구 풍남동', reviews:298, rating:3.9, pos:68, neg:32, desc:'전통 공예 체험 및 전시.',
    menu:[
      { name:'관람 입장', price:'2,000', mention:120, sentiment:'neutral', tag:'' },
      { name:'한지공예 체험', price:'10,000', mention:98, sentiment:'pos', tag:'' },
      { name:'매듭공예 체험', price:'12,000', mention:67, sentiment:'pos', tag:'' },
      { name:'전통 부채 만들기', price:'15,000', mention:45, sentiment:'pos', tag:'' },
    ]
  },
];

function renderMenuGrid(menuItems) {
  const grid = document.getElementById('menuGrid');
  if (!grid || !menuItems) return;
  const sentimentColors = {
    pos: { bg: '#E6F5ED', border: '#A7F3D0', text: '#1A7A4A', label: '긍정반응 높음' },
    neutral: { bg: '#F5F0E8', border: '#E8DCC8', text: '#5C4A2A', label: '보통' },
    neg: { bg: '#FAE8E6', border: '#FECACA', text: '#C0392B', label: '부정반응 있음' },
  };
  grid.innerHTML = menuItems.map(m => {
    const sc = sentimentColors[m.sentiment];
    return `<div style="background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 6px; position: relative;">
      ${m.tag ? `<span style="position:absolute; top:10px; right:10px; background:${sc.bg}; color:${sc.text}; border:1px solid ${sc.border}; font-size:10px; font-weight:700; padding:2px 7px; border-radius:100px;">${m.tag}</span>` : ''}
      <div style="font-size: 14px; font-weight: 700; color: var(--text); padding-right: ${m.tag ? '52px' : '0'};">${m.name}</div>
      <div style="font-size: 16px; font-weight: 700; color: var(--primary); font-family: 'Pretendard', serif;">${m.price}${m.price !== '무료' ? '원' : ''}</div>
      <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 2px;">
        <span style="font-size: 11px; color: var(--text-3);">리뷰 언급 ${m.mention}회</span>
        <span style="font-size: 10px; font-weight: 600; color: ${sc.text};">${sc.label}</span>
      </div>
      <div style="height: 4px; background: var(--border); border-radius: 2px; overflow: hidden;">
        <div style="height:100%; width:${Math.min(100, Math.round(m.mention / menuItems[0].mention * 100))}%; background:${sc.text}; border-radius:2px;"></div>
      </div>
    </div>`;
  }).join('');
}

function renderBusinessGrid(data) {
  const grid = document.getElementById('businessGrid');
  grid.innerHTML = data.map(b => `
    <div class="business-card" onclick="showDetail(${b.id})">
      <div class="business-card-img img-placeholder" style="position:relative;">
        ${b.icon}
        <span class="biz-category-badge">${b.category}</span>
      </div>
      <div class="business-card-body">
        <div class="biz-name">${b.name}</div>
        <div class="biz-loc">📍 ${b.location}</div>
        <div class="biz-stats">
          <span class="biz-stat">⭐ ${b.rating}</span>
          <span class="biz-stat">📝 리뷰 ${b.reviews.toLocaleString()}개</span>
        </div>
        <div class="sentiment-bar">
          <div class="sentiment-bar-fill" style="--pos-pct: ${b.pos}%; width: ${b.pos}%; background: var(--pos);"></div>
        </div>
        <div class="sentiment-labels">
          <span class="s-pos">긍정 ${b.pos}%</span>
          <span class="s-neg">부정 ${b.neg}%</span>
        </div>
      </div>
    </div>
  `).join('');
}

function setFilter(el, cat) {
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  const filtered = cat === '전체' ? businesses : businesses.filter(b => b.category.includes(cat) || b.name.includes(cat));
  renderBusinessGrid(filtered);
}

function filterCategory(cat) {
  document.querySelectorAll('.filter-chip').forEach(c => {
    if(c.textContent.includes(cat)) { c.classList.add('active'); } else { c.classList.remove('active'); }
  });
  const filtered = businesses.filter(b => b.category.includes(cat) || b.name.includes(cat));
  renderBusinessGrid(filtered.length ? filtered : businesses);
}

function handleSearch() {
  const q = document.getElementById('heroSearch').value.toLowerCase();
  if (!q) { renderBusinessGrid(businesses); return; }
  const filtered = businesses.filter(b => b.name.includes(q) || b.category.includes(q) || b.desc.includes(q));
  renderBusinessGrid(filtered.length ? filtered : businesses);
  document.querySelector('.business-section').scrollIntoView({ behavior: 'smooth' });
}

function showPage(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  window.scrollTo(0,0);
  if (page === 'detail') { initDetailCharts(); initWordcloud(); }
}

function showDetail(id) {
  const b = businesses.find(x => x.id === id);
  if (!b) return;
  document.getElementById('detail-icon').textContent = b.icon;
  document.getElementById('detail-name').textContent = b.name;
  document.getElementById('detail-category').textContent = b.category;
  document.getElementById('detail-rating').textContent = b.rating;
  document.getElementById('detail-reviews').textContent = `리뷰 ${b.reviews.toLocaleString()}개`;
  document.getElementById('detail-location').textContent = b.location;
  document.getElementById('detail-pos-pct').textContent = `긍정 ${b.pos}%`;
  document.getElementById('pie-pos-pct').textContent = `${b.pos}%`;
  const posCount = Math.round(b.reviews * b.pos / 100);
  const negCount = b.reviews - posCount;
  document.getElementById('legend-pos-val').textContent = `${posCount.toLocaleString()}개 (${b.pos}%)`;
  document.getElementById('legend-neg-val').textContent = `${negCount.toLocaleString()}개 (${b.neg}%)`;
  document.getElementById('biz-address').textContent = `전북 전주시 ${b.location} ○○길 12`;
  document.getElementById('map-address-display').textContent = `전북 전주시 ${b.location}`;
  renderMenuGrid(b.menu);
  showPage('detail');
}

// MAIN TREND CHART - 삭제됨 (일별 추이 메인 제거)

let detailChartsInit = false;
function initDetailCharts() {
  if (detailChartsInit) { return; }
  detailChartsInit = true;

  // 월별 방문 추천도 바
  const visitScores = [
    { m: '1월', score: 72 }, { m: '2월', score: 68 }, { m: '3월', score: 85 },
    { m: '4월', score: 91 }, { m: '5월', score: 88 }, { m: '6월', score: 70 },
    { m: '7월', score: 58 }, { m: '8월', score: 62 }, { m: '9월', score: 87 },
    { m: '10월', score: 94 }, { m: '11월', score: 89 }, { m: '12월', score: 79 },
  ];
  const barsWrap = document.getElementById('visitBars');
  if (barsWrap) {
    barsWrap.innerHTML = visitScores.map(v => {
      const color = v.score >= 85 ? '#1A7A4A' : v.score >= 70 ? '#C8530A' : '#C0392B';
      return `<div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
        <span style="width:26px; font-size:10px; color:var(--text-3); text-align:right; flex-shrink:0;">${v.m}</span>
        <div style="flex:1; background:var(--bg); border-radius:3px; height:8px; overflow:hidden;">
          <div style="width:${v.score}%; height:100%; background:${color}; border-radius:3px;"></div>
        </div>
        <span style="width:30px; font-size:10px; font-weight:600; color:${color}; text-align:right;">${v.score}</span>
      </div>`;
    }).join('');
  }

  // 계절별 리뷰 막대 차트
  new Chart(document.getElementById('seasonChart'), {
    type: 'bar',
    data: {
      labels: ['봄 (3–5월)', '여름 (6–8월)', '가을 (9–11월)', '겨울 (12–2월)'],
      datasets: [
        { label: '긍정', data: [275, 274, 354, 90], backgroundColor: '#1A7A4A', borderRadius: 4 },
        { label: '부정', data: [37, 154, 35, 24], backgroundColor: '#C0392B', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}개` }}},
      scales: {
        x: { stacked: true, ticks: { font: { size: 10 }, color: '#9C8A6A' }, grid: { display: false }, border: { display: false } },
        y: { stacked: true, ticks: { font: { size: 10 }, color: '#9C8A6A' }, grid: { color: 'rgba(0,0,0,0.05)' }, border: { display: false } }
      }
    }
  });

  // 도넛 차트
  new Chart(document.getElementById('pieChart'), {
    type: 'doughnut',
    data: { labels: ['긍정', '부정'], datasets: [{ data: [78, 22], backgroundColor: ['#1A7A4A', '#C0392B'], borderWidth: 0, hoverOffset: 4 }] },
    options: { responsive: false, cutout: '70%', plugins: { legend: { display: false }, tooltip: { enabled: false } }, animation: { animateRotate: true, duration: 800 } }
  });

  // 일일 긍부정 평가 추이 — 묶음 막대 그래프 (최근 30일)
  const days = Array.from({length:30}, (_,i) => {
    const d = new Date(2025,11,30); d.setDate(d.getDate() - (29 - i));
    return `${d.getMonth()+1}/${d.getDate()}`;
  });
  const posDaily = [48,52,60,45,70,85,90,78,65,72,88,95,82,76,68,91,103,97,85,80,95,108,100,112,98,88,105,115,108,120];
  const negDaily = [18,15,20,22,25,30,32,28,20,24,30,35,28,22,25,38,42,40,32,28,35,40,38,42,35,30,38,45,40,48];
  new Chart(document.getElementById('detailTrendChart'), {
    type: 'bar',
    data: {
      labels: days,
      datasets: [
        { label: '긍정', data: posDaily, backgroundColor: 'rgba(26,122,74,0.75)', borderRadius: 3, borderSkipped: false },
        { label: '부정', data: negDaily, backgroundColor: 'rgba(192,57,43,0.75)', borderRadius: 3, borderSkipped: false }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}건` }}},
      scales: {
        x: { ticks: { font: { size: 9 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 10, color: '#9C8A6A' }, grid: { display: false }, border: { display: false } },
        y: { ticks: { font: { size: 10 }, color: '#9C8A6A' }, grid: { color: 'rgba(0,0,0,0.05)' }, border: { display: false } }
      }
    }
  });
}

function initWordcloud() {
  const wrap = document.getElementById('wordcloudWrap');
  if (wrap.children.length > 0) return;
  const words = [
    { text: '맛있어요', size: 24, type: 'pos' },
    { text: '친절', size: 20, type: 'pos' },
    { text: '분위기', size: 19, type: 'pos' },
    { text: '초코파이', size: 22, type: 'pos' },
    { text: '전주여행', size: 17, type: 'neutral' },
    { text: '대기시간', size: 18, type: 'neg' },
    { text: '포장예쁨', size: 16, type: 'pos' },
    { text: '재방문', size: 20, type: 'pos' },
    { text: '주차불편', size: 16, type: 'neg' },
    { text: '인생샷', size: 15, type: 'pos' },
    { text: '달달해요', size: 17, type: 'pos' },
    { text: '선물용', size: 16, type: 'pos' },
    { text: '가격', size: 14, type: 'neg' },
    { text: '줄서요', size: 15, type: 'neg' },
    { text: '꼭방문', size: 18, type: 'pos' },
    { text: '깔끔', size: 14, type: 'pos' },
    { text: '전통', size: 13, type: 'neutral' },
  ];
  const colorMap = {
    pos: { bg: '#E6F5ED', color: '#1A7A4A', border: '#A7F3D0' },
    neg: { bg: '#FAE8E6', color: '#C0392B', border: '#FECACA' },
    neutral: { bg: '#F5F0E8', color: '#5C4A2A', border: '#E8DCC8' },
  };
  words.forEach(w => {
    const el = document.createElement('span');
    el.className = 'wc-word';
    el.textContent = w.text;
    const c = colorMap[w.type];
    el.style.cssText = `font-size: ${w.size}px; background: ${c.bg}; color: ${c.color}; border: 1px solid ${c.border};`;
    wrap.appendChild(el);
  });
}

/* ===== RAG 모의 응답 시스템 ===== */
const ragResponses = [
  {
    keys: ['카페','커피','디저트','차'],
    answer: '전주 리뷰 데이터 <span class="rag-highlight">89,412건</span>을 분석한 결과, 한옥마을 인근 카페 중 긍정 비율이 가장 높은 곳은 <span class="rag-highlight">수제청 카페 (긍정 91%)</span>와 <span class="rag-highlight">전동 커피 로스터스 (긍정 87%)</span>입니다. 리뷰에서 "분위기 좋다", "사진 잘 나온다"는 언급이 두드러집니다.',
    sources: ['리뷰 #A-2041', '리뷰 #A-3872', '리뷰 #B-0119'],
    cat: '카페'
  },
  {
    keys: ['주차','차량'],
    answer: '리뷰 분석 결과, <span class="rag-highlight">주차 관련 부정 언급</span>은 한옥마을 권역에 집중됩니다. 풍남동·전동 업체 68%에서 "주차 어렵다"는 언급이 확인됩니다. <span class="rag-highlight">덕진구·효자동</span> 권역 업체는 주차 편의 언급 비율이 낮아 차량 방문 시 추천됩니다.',
    sources: ['리뷰 #C-0883', '리뷰 #C-1220'],
    cat: '한식'
  },
  {
    keys: ['한식','밥','비빔밥','음식'],
    answer: '전주 한식 업체 리뷰를 분석한 결과, <span class="rag-highlight">비빔밥·한정식</span> 카테고리의 긍정 비율이 평균 <span class="rag-highlight">81.4%</span>로 높습니다. "맛있어요", "재방문 의사 있음" 키워드가 상위 3위 안에 포함됩니다. 가격대는 <span class="rag-highlight">1만~2만원대</span>가 가장 많은 호평을 받습니다.',
    sources: ['리뷰 #D-0041', '리뷰 #D-2210', '리뷰 #D-3009'],
    cat: '한식'
  },
  {
    keys: ['아이','가족','아동','어린이','키즈'],
    answer: '어린이·가족 동반 리뷰를 분석하면 <span class="rag-highlight">체험 공방 및 전통문화 시설</span>의 만족도가 평균 <span class="rag-highlight">85% 이상</span>으로 높습니다. "아이가 너무 좋아했어요"라는 표현이 체험 카테고리에서 가장 빈번히 등장합니다.',
    sources: ['리뷰 #E-0317', '리뷰 #E-0598'],
    cat: '체험'
  },
  {
    keys: ['야경','저녁','밤','야간'],
    answer: '야경 관련 긍정 리뷰는 <span class="rag-highlight">전동성당 인근</span>과 <span class="rag-highlight">남부시장 야시장</span> 주변 업체에 집중됩니다. 12월~1월 겨울 시즌 야경 언급 빈도가 <span class="rag-highlight">3.2배</span> 증가하며, 해당 기간 긍정 비율은 평균 대비 6%p 높습니다.',
    sources: ['리뷰 #F-1192', '리뷰 #F-2047', '리뷰 #F-3301'],
    cat: '한옥마을'
  },
  {
    keys: ['숙박','호텔','한옥','게스트','민박'],
    answer: '전주 숙박 리뷰 분석 결과, <span class="rag-highlight">전통 한옥 숙박</span>의 긍정 비율은 평균 <span class="rag-highlight">84%</span>로 일반 호텔 대비 12%p 높습니다. "체험 분위기", "직원 친절"이 주요 호평 키워드이며, "방음"은 주의 키워드로 분류됩니다.',
    sources: ['리뷰 #G-0042', '리뷰 #G-0887'],
    cat: '숙박'
  },
];

const ragDefaultAnswer = '리뷰 <span class="rag-highlight">89,412건</span>을 분석했습니다. 더 정확한 결과를 위해 카테고리(한식·카페·숙박 등)나 원하시는 조건(주차·분위기·가격대 등)을 함께 입력해 주세요.';

function ragPreset(el) {
  document.getElementById('ragInput').value = el.textContent;
  ragSearch();
}

function processRagQuery(q) {
  const body = document.getElementById('ragOverlayBody');
  
  // 사용자 질문 버블
  const userBubble = document.createElement('div');
  userBubble.className = 'rag-ol-user-card';
  userBubble.textContent = q;
  body.appendChild(userBubble);

  // AI 답변 대기 버블
  const aiBubble = document.createElement('div');
  aiBubble.className = 'rag-ol-ai-card';
  aiBubble.innerHTML = `
    <div class="rag-ol-ai-hd">
      <div class="rag-pulse"></div>
      <span class="rag-status">분석 중...</span>
    </div>
    <div class="rag-answer-text">
      <div class="rag-thinking"><span></span><span></span><span></span></div>
    </div>
    <div class="rag-ol-sources" style="display:none; margin-top:12px; padding-top:10px; border-top:1px solid rgba(200,83,10,0.15); gap:6px; flex-wrap:wrap;"></div>
    <div class="rag-ol-results-hd" style="display:none; font-size:12px; font-weight:700; color:var(--text-2); margin-top:16px; margin-bottom:8px; align-items:center; gap:8px;"></div>
    <div class="rag-ol-grid"></div>
  `;
  body.appendChild(aiBubble);
  
  // 스크롤 맨 아래로
  requestAnimationFrame(() => { body.scrollTop = body.scrollHeight; });

  const ql = q.toLowerCase();

  // 1. 업체 직접 검색인지 확인
  const directBusiness = businesses.find(b => q.includes(b.name) || b.name.includes(q));

  if (directBusiness) {
    setTimeout(() => {
      aiBubble.querySelector('.rag-status').textContent = '업체 검색 완료';
      const answerEl = aiBubble.querySelector('.rag-answer-text');
      answerEl.style.opacity = '0';
      answerEl.innerHTML = `검색하신 <span style="font-weight:700; color:var(--primary);">${directBusiness.name}</span> 정보입니다. 카드를 클릭하시면 상세 페이지로 이동합니다.`;
      
      const gridEl = aiBubble.querySelector('.rag-ol-grid');
      gridEl.innerHTML = `
        <div class="business-card" style="box-shadow: none; border: 1px solid var(--border); cursor:pointer;" onclick="closeRagOverlay(); showDetail(${directBusiness.id})">
          <div class="business-card-img img-placeholder" style="height:100px; font-size:1.5rem;">
            ${directBusiness.icon}
            <span class="biz-category-badge" style="top:6px; left:6px;">${directBusiness.category}</span>
          </div>
          <div class="business-card-body" style="padding:12px;">
            <div class="biz-name" style="font-size:13px;">${directBusiness.name}</div>
            <div class="biz-loc" style="font-size:11px; margin-bottom:6px;">📍 ${directBusiness.location}</div>
            <div class="sentiment-bar" style="margin-bottom:4px;">
              <div class="sentiment-bar-fill" style="--pos-pct: ${directBusiness.pos}%; width: ${directBusiness.pos}%; background: var(--pos);"></div>
            </div>
            <div class="sentiment-labels" style="font-size:10px;">
              <span class="s-pos">긍정 ${directBusiness.pos}%</span>
            </div>
          </div>
        </div>
      `;
      
      requestAnimationFrame(() => { 
        answerEl.style.transition = 'opacity .4s';
        answerEl.style.opacity = '1'; 
        body.scrollTop = body.scrollHeight;
      });
    }, 600);
    return;
  }

  // 2. 일반 RAG 질의 처리
  const match = ragResponses.find(r => r.keys.some(k => ql.includes(k)));

  setTimeout(() => {
    const text = match ? match.answer : ragDefaultAnswer;
    const sources = match ? match.sources : ['리뷰 #Z-0001', '리뷰 #Z-0002'];

    aiBubble.querySelector('.rag-status').textContent = `분석 완료 · 참조 ${sources.length}건`;
    
    const answerEl = aiBubble.querySelector('.rag-answer-text');
    answerEl.style.opacity = '0';
    answerEl.innerHTML = text;
    requestAnimationFrame(() => { 
      answerEl.style.transition = 'opacity .4s';
      answerEl.style.opacity = '1'; 
      body.scrollTop = body.scrollHeight;
    });

    const sourcesEl = aiBubble.querySelector('.rag-ol-sources');
    sourcesEl.style.display = 'flex';
    sourcesEl.innerHTML = '<span class="rag-src-label" style="font-size:10px; color:var(--text-3); font-weight:600; align-self:center;">📄 참조 리뷰</span>';
    sources.forEach(s => {
      const chip = document.createElement('span');
      chip.className = 'rag-src-chip';
      chip.textContent = s;
      sourcesEl.appendChild(chip);
    });

    if (match && match.cat) {
      const filtered = businesses.filter(b =>
        b.category.includes(match.cat) || b.name.includes(q) || b.desc.includes(q)
      );
      if (filtered.length > 0) {
        const resultsHd = aiBubble.querySelector('.rag-ol-results-hd');
        const gridEl = aiBubble.querySelector('.rag-ol-grid');
        resultsHd.style.display = 'flex';
        resultsHd.innerHTML = `<span style="width:3px; height:14px; background:var(--primary); border-radius:2px; display:inline-block;"></span>관련 업체 추천`;
        gridEl.innerHTML = filtered.map(b => `
          <div class="business-card" style="box-shadow: none; border: 1px solid var(--border); cursor:pointer;" onclick="closeRagOverlay(); showDetail(${b.id})">
            <div class="business-card-img img-placeholder" style="height:100px; font-size:1.5rem;">
              ${b.icon}
              <span class="biz-category-badge" style="top:6px; left:6px;">${b.category}</span>
            </div>
            <div class="business-card-body" style="padding:12px;">
              <div class="biz-name" style="font-size:13px;">${b.name}</div>
              <div class="biz-loc" style="font-size:11px; margin-bottom:6px;">📍 ${b.location}</div>
              <div class="sentiment-bar" style="margin-bottom:4px;">
                <div class="sentiment-bar-fill" style="--pos-pct: ${b.pos}%; width: ${b.pos}%; background: var(--pos);"></div>
              </div>
              <div class="sentiment-labels" style="font-size:10px;">
                <span class="s-pos">긍정 ${b.pos}%</span>
              </div>
            </div>
          </div>
        `).join('');
      }
    }
    
    // 최종 높이 변경 후 다시 스크롤
    setTimeout(() => { body.scrollTop = body.scrollHeight; }, 50);
  }, 1500);
}

function ragSearch() {
  const q = (document.getElementById('ragInput').value || '').trim();
  if (!q) return;

  const backdrop = document.getElementById('ragOverlayBackdrop');
  const overlay = document.getElementById('ragOverlay');
  const body = document.getElementById('ragOverlayBody');

  // 오버레이 열기 및 초기화
  backdrop.classList.add('open');
  overlay.classList.add('open');
  body.innerHTML = ''; 
  document.getElementById('ragInput').value = ''; 
  
  processRagQuery(q);
}

function sendRagOverlayMessage() {
  const input = document.getElementById('ragOverlayInput');
  const q = (input.value || '').trim();
  if (!q) return;
  
  input.value = '';
  processRagQuery(q);
}

function closeRagOverlay() {
  document.getElementById('ragOverlayBackdrop').classList.remove('open');
  document.getElementById('ragOverlay').classList.remove('open');
}

/* ===== 우상단 nav 검색 (RAG 완전 분리 — 업체 직접 필터링) ===== */
function navSearch(q) {
  q = (q || '').trim();
  if (!q) return;

  // 메인 페이지로 이동 (detail 등 다른 페이지에 있을 경우)
  showPage('main');

  // 업체 데이터 직접 필터링
  const ql = q.toLowerCase();
  const filtered = businesses.filter(b =>
    b.name.includes(q) ||
    b.category.toLowerCase().includes(ql) ||
    b.location.includes(q) ||
    (b.desc && b.desc.includes(q))
  );

  renderBusinessGrid(filtered.length ? filtered : businesses);

  // 결과 카운트 업데이트
  const countEl = document.querySelector('.section-header .section-title + div span');
  if (countEl) {
    if (filtered.length) {
      countEl.textContent = `"${q}" 검색결과 ${filtered.length}개 업체`;
      countEl.style.color = 'var(--primary)';
      countEl.style.fontWeight = '600';
    } else {
      countEl.textContent = `"${q}" 결과 없음 — 전체 표시 중`;
      countEl.style.color = 'var(--neg)';
    }
  }

  // 업체 목록으로 부드럽게 스크롤
  setTimeout(() => {
    document.querySelector('.business-section')?.scrollIntoView({ behavior: 'smooth' });
  }, 150);

  // 필터 chip 전체 해제 후 '전체' 활성화
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  const allChip = document.querySelector('.filter-chip');
  if (allChip) allChip.classList.add('active');
}

function handleSearch() { ragSearch(); }

// INIT
renderBusinessGrid(businesses);