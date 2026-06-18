// 📝 static/js/store_detail.js


// 카카오맵 사전 초기화
// 스크립트가 늦게 로드되더라도 브라우저가 kakao를 인식할 수 있게 최상단에서
if (typeof kakao !== 'undefined' && kakao.maps) {
    kakao.maps.load(function() {
        console.log("카카오 맵 엔진 수동 이니셜라이징 완료");
    });
}

// 상세 데이터 DOM 조작 및 동적 할당 함수 (대소문자 스키마 통합 및 에러 방어)
function renderStoreDetail(data) {
  // [보강] 데이터가 유효한지 안전 검사
  if (!data) return;
  console.log('디테일 접속 완료')

  // 1. 가게 기본 정보 바인딩
  if (data.store) {
    const s = data.store;
    
    // 리뷰 데이터 대소문자 매핑 방어
    const reviewsList = data.reviews || data.REVIEWS || [];
    const totalReviews = s.REVIEW_CNT || s.review_cnt || reviewsList.length;

    let posRate = 0;
    if (reviewsList.length > 0) {
        const totalScore = reviewsList.reduce((sum, r) => sum + Number(r.PN_SCORE || r.pn_score || 0), 0);
        posRate = Math.round((totalScore / reviewsList.length) * 100);
    } else {
        posRate = Math.round(s.PN_RATE || s.pn_rate || 0);
    }
    const negRate = 100 - posRate;
    
    const posCount = Math.round(totalReviews * (posRate / 100));
    const negCount = totalReviews - posCount;

    // 💡 HTML 엘리먼트 존재 여부를 매번 검사하여 에러로 스크립트가 멈추는 현상 원천 차단
    if(document.getElementById('detail-name')) 
      document.getElementById('detail-name').textContent = s.STORE_NAME || s.name || s.store_name || '이름 없음';
    
    if(document.getElementById('detail-category')) 
      document.getElementById('detail-category').textContent = s.CATEGORY || s.category || '-';
    
    if(document.getElementById('detail-rating')) 
      document.getElementById('detail-rating').textContent = Number(s.STAR || s.star || 0).toFixed(1);

    if(document.getElementById('detail-reviews')) 
      document.getElementById('detail-reviews').textContent = `리뷰 ${totalReviews.toLocaleString()}개`;
    
    if(document.getElementById('detail-location')) 
      document.getElementById('detail-location').textContent = s.AREA || s.area || s.location || '-';
    
    if(document.getElementById('detail-pos-pct')) 
      document.getElementById('detail-pos-pct').textContent = `긍정 ${posRate}%`;

    // 카테고리별 감성 이모지 자동 매핑
    const currentCategory = s.CATEGORY || s.category || '';
    let icon = '📍';
    if (currentCategory.includes('한식')) icon = '🍚';
    else if (currentCategory.includes('카페') || currentCategory.includes('디저트') || currentCategory.includes('빵')) icon = '☕';
    else if (currentCategory.includes('일식')) icon = '🍣';
    
    if(document.getElementById('detail-icon')) 
      document.getElementById('detail-icon').textContent = icon;

    // 별점 그래픽(★) 처리
    const starScore = Math.round(Number(s.STAR || s.star || 0));
    const starsText = '★'.repeat(starScore) + '☆'.repeat(Math.max(0, 5 - starScore));
    if(document.getElementById('detail-stars')) 
      document.getElementById('detail-stars').textContent = starsText;

    // 도로명 주소, 지번 주소
    const fullAddress = s.ADDRESS_DO || s.address_do || s.address || '주소 정보 없음';
    if(document.getElementById('biz-address')) 
      document.getElementById('biz-address').textContent = fullAddress;
    
    if(document.getElementById('map-address-display')) {
        document.getElementById('map-address-display').textContent = s.ADDRESS_JI || s.address_ji || '정보 없음';
    }

    // 전화번호
    if(document.getElementById('biz-phone')) {
        document.getElementById('biz-phone').textContent = s.PHONE || s.phone || '등록된 번호 없음';
    }

    // 주차 정보 스타일 처리
    const parkingEl = document.getElementById('biz-parking');
    if (parkingEl) {
        const parkingText = s.PARKING || s.parking || '주차 정보 없음';
        parkingEl.textContent = parkingText;
        if (parkingText.includes('불가')) {
            parkingEl.style.color = "var(--neg, #f44336)"; 
        } else {
            parkingEl.style.color = "var(--pos, #4CAF50)"; 
        }
    }

    // 편의성 배지 달기
    const amenityBox = document.getElementById('biz-amenities-box');
    if (amenityBox) {
        amenityBox.innerHTML = "";
        const amenityStr = s.AMENITY || s.amenity;
        if (amenityStr) {
            const amenityArray = amenityStr.split('_');
            amenityArray.forEach(item => {
                const trimmed = item.trim();
                if (trimmed) {
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
        const hoursStr = s.BUSINESS_HOURS || s.business_hours;
        if (hoursStr) {
            hoursTooltip.innerHTML = `<p>${hoursStr.replace(/\n/g, '<br>')}</p>`;
        } else {
            hoursTooltip.innerHTML = `<p>등록된 영업시간 정보가 없습니다.</p>`;
        }
    }
    
    // 카카오맵
    const mapContainer = document.getElementById('mapBox');
    const latVal = s.LAT || s.lat;
    const lngVal = s.LNG || s.lng;
    
    if (mapContainer && latVal && lngVal && window.kakao && window.kakao.maps) {
        kakao.maps.load(function() {
            const mapOption = {
                center: new kakao.maps.LatLng(parseFloat(latVal), parseFloat(lngVal)),
                level: 3
            };
            const map = new kakao.maps.Map(mapContainer, mapOption);
            const markerPosition = new kakao.maps.LatLng(parseFloat(latVal), parseFloat(lngVal));
            const marker = new kakao.maps.Marker({ position: markerPosition });
            marker.setMap(map);

            const storeName = s.STORE_NAME || s.name || '선택한 맛집';
            const iwContent = `<div style="padding:5px; font-size:12px; font-weight:700; color:var(--text); text-align:center; min-width:150px;">${storeName}</div>`;
            const infowindow = new kakao.maps.InfoWindow({ content: iwContent });
            infowindow.open(map, marker);
        });
    }

    // 도넛 차트 값 바인딩
    if(document.getElementById('pie-pos-pct')) document.getElementById('pie-pos-pct').textContent = `${posRate}%`;
    if(document.getElementById('legend-pos-val')) document.getElementById('legend-pos-val').textContent = `${posCount.toLocaleString()}개 (${posRate}%)`;
    if(document.getElementById('legend-neg-val')) document.getElementById('legend-neg-val').textContent = `${negCount.toLocaleString()}개 (${negRate}%)`;

    // Chart.js 도넛 차트
    const ctx = document.getElementById('pieChart');
    if (ctx) {
        if (window.myPieChart) { window.myPieChart.destroy(); }
        const posColor = getComputedStyle(document.documentElement).getPropertyValue('--pos').trim() || '#1A7A4A';
        const negColor = getComputedStyle(document.documentElement).getPropertyValue('--neg').trim() || '#C0392B';

        window.myPieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['긍정', '부정'],
                datasets: [{
                    data: [posRate, negRate],
                    backgroundColor: [posColor, negColor],
                    borderWidth: 0
                }]
            },
            options: {
                cutout: '75%',
                plugins: { legend: { display: false }, tooltip: { enabled: true } },
                responsive: false,
                maintainAspectRatio: false
            }
        });
    }

    // 워드클라우드
    const wordWrap = document.getElementById('wordcloudWrap');
    const wordsList = data.words || data.WORDS || [];
    if (wordWrap) {
        wordWrap.innerHTML = "";

        if (wordsList.length > 0) {
            const maxWordCnt = wordsList[0].CNT || wordsList[0].cnt || 1;

            wordsList.forEach(w => {
                const badge = document.createElement('span');
                const wordPn = (w.WORD_PN || w.word_pn || '').toUpperCase();
                const wordText = w.WORD || w.word || '';
                const wordCnt = w.CNT || w.cnt || 0;
                
                if (wordPn === 'P') badge.className = 'wc-badge pos';
                else if (wordPn === 'N') badge.className = 'wc-badge neg';
                else badge.className = 'wc-badge neutral';

                const ratio = wordCnt / maxWordCnt;
                const fontSize = Math.round(12 + (ratio * 12)); 
                badge.style.fontSize = `${fontSize}px`;
                badge.textContent = wordText;
                wordWrap.appendChild(badge);
            });
        } else {
            wordWrap.innerHTML = `<div style="color: var(--text-3); font-size: 13px; text-align: center; width: 100%; padding: 30px 0;">분석된 키워드가 없습니다.</div>`;
        }
    }
  }
  console.log('기본정보 가져옴')

  // 2. 메뉴 정보 리스트 동적 생성
  const menuContainer = document.getElementById('menuGrid');
  const menusList = data.menus || data.MENUS || [];
  console.log("메뉴그리드찾음")
  
  if (menuContainer) {
    if (menusList.length === 0) {
      menuContainer.innerHTML = '<div class="no-data" style="grid-column: 1/-1; text-align: center; color: var(--text-3); padding: 20px;">등록된 메뉴 정보가 없습니다.</div>';
    } else {
      const sentimentColors = {
        pos: { bg: '#E6F5ED', border: '#A7F3D0', text: '#1A7A4A', label: '긍정반응 높음' },
        neutral: { bg: '#F5F0E8', border: '#E8DCC8', text: '#5C4A2A', label: '보통' },
        neg: { bg: '#FAE8E6', border: '#FECACA', text: '#C0392B', label: '부정반응 있음' },
      };

      const maxMention = menusList[0].CNT || menusList[0].cnt || 1;

      menuContainer.innerHTML = menusList.map(m => {
        const mName = m.MENU_NAME || m.menu_name || '이름 없음';
        const mPriceRaw = m.MENU_PRICE !== undefined ? m.MENU_PRICE : m.menu_price;
        const mPrice = mPriceRaw ? Number(mPriceRaw).toLocaleString() : '가격 정보 없음';
        const mMention = m.CNT || m.cnt || 0;
        const isBest = m.BEST || m.best;
        const mTag = isBest ? '대표메뉴' : '';

        let mSentiment = 'neutral';
        if (mMention > 0 && (isBest || mMention > (maxMention * 0.5))) {
            mSentiment = 'pos';
        }

        const sc = sentimentColors[mSentiment];
        const barWidth = maxMention > 0 ? Math.min(100, Math.round(mMention / maxMention * 100)) : 0;
        const progressBgColor = mMention === 0 ? '#CBD5E1' : sc.text;

        return `
          <div style="background: var(--bg-card); border: 1px solid var(--border-2); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 6px; position: relative;">
            ${mTag ? `<span style="position:absolute; top:10px; right:10px; background:${sc.bg}; color:${sc.text}; border:1px solid ${sc.border}; font-size:10px; font-weight:700; padding:2px 7px; border-radius:100px;">${mTag}</span>` : ''}
            <div style="font-size: 14px; font-weight: 700; color: var(--text-1); padding-right: ${mTag ? '65px' : '0'};">${mName}</div>
            <div style="font-size: 16px; font-weight: 700; color: var(--text-2); font-family: 'Noto Sans KR', serif;">${mPrice}${mPrice !== '무료' && mPriceRaw ? '원' : ''}</div>
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

  // 30 일별 막대 그래프
  const trendCtx = document.getElementById('detailTrendChart');
  const trends = data.daily_trends || data.DAILY_TRENDS || [];
  if (trendCtx) {
        if (window.myTrendChart) { window.myTrendChart.destroy(); }
        
        const labels = trends.map(t => t.date || t.DATE || '');
        const posData = trends.map(t => t.pos_cnt || t.POS_CNT || 0);
        const negData = trends.map(t => t.neg_cnt || t.NEG_CNT || 0);

        const posColor = getComputedStyle(document.documentElement).getPropertyValue('--pos').trim() || '#1A7A4A';
        const negColor = getComputedStyle(document.documentElement).getPropertyValue('--neg').trim() || '#C0392B';

        window.myTrendChart = new Chart(trendCtx, {
            type: 'bar', 
            data: {
                labels: labels,
                datasets: [
                    { label: '긍정 리뷰', data: posData, borderColor: posColor, backgroundColor: posColor + '90', pointRadius: 3, fill: true },
                    { label: '부정 리뷰', data: negData, borderColor: negColor, backgroundColor: negColor + '90', pointRadius: 3, fill: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#64748B', font: { size: 11 } } },
                    y: { beginAtZero: true, grid: { color: '#E2E8F0' }, ticks: { stepSize: 1, color: '#64748B' } }
                }
            }
        });
  }

  // 3. 실제 리뷰 샘플 리스트 동적 생성 
  const posContainer = document.getElementById('det-pos-list');
  const negContainer = document.getElementById('det-neg-list');
  const reviewsList = data.reviews || data.REVIEWS || [];

  if (reviewsList) {
    const posReviews = reviewsList.filter(r => (r.REVIEW_PN || r.review_pn || '').toUpperCase() === 'P').slice(0, 2);
    if (posContainer) {
      if (posReviews.length === 0) {
        posContainer.innerHTML = '<div class="no-data">수집된 긍정 리뷰가 없습니다.</div>';
      } else {
        posContainer.innerHTML = posReviews.map(r => `
          <div class="review-item review-pos">
            <div class="review-label">👍 긍정 후기 (점수: ${Number(r.PN_SCORE || r.pn_score || 0).toFixed(2)})</div>
            <div class="review-text">${r.CONTENT || r.content || ''}</div>
          </div>
        `).join('');
      }
    }

    const negReviews = reviewsList.filter(r => {
        const pn = (r.REVIEW_PN || r.review_pn || '').toUpperCase();
        return pn === 'N' || pn === 'F';
    }).slice(0, 2);
    
    if (negContainer) {
      if (negReviews.length === 0) {
        negContainer.innerHTML = '<div class="no-data">수집된 개선 요구 리뷰가 없습니다.</div>';
      } else {
        negContainer.innerHTML = negReviews.map(r => `
          <div class="review-item review-neg">
            <div class="review-label">👎 개선 요구 후기 (점수: ${Number(r.PN_SCORE || r.pn_score || 0).toFixed(2)})</div>
            <div class="review-text">${r.CONTENT || r.content || ''}</div>
          </div>
        `).join('');
      }
    }
  }

  // 4. AI 개선 리포트 동적 생성
  const reportContainer = document.getElementById('reportGrid');
  if (reportContainer && data.store) {
    const aiReportHtml = data.store.AI_REPORT || data.store.ai_report;
    if (!aiReportHtml || aiReportHtml.trim() === "") {
      reportContainer.innerHTML = `<div class="no-data" style="grid-column: 1/-1; text-align: center; color: var(--text-3); padding: 20px;">분석된 AI 개선 리포트가 없습니다.</div>`;
    } else {
      reportContainer.innerHTML = aiReportHtml;
    }
  }

  // 5. 월별 방문 추천도 및 6. 계절별 통계
  const barsContainer = document.getElementById('visitBars');
  const bestMonthEl = document.getElementById('best-visit-months');

  if (reviewsList.length > 0) {
    const monthlyStats = Array.from({ length: 12 }, (_, i) => ({ month: i + 1, posCount: 0, totalCount: 0 }));
    const seasons = {
      spring: { name: '봄', months: [3, 4, 5], pos: 0, total: 0, elementId: 'season-spring' },
      summer: { name: '여름', months: [6, 7, 8], pos: 0, total: 0, elementId: 'season-summer' },
      autumn: { name: '가을', months: [9, 10, 11], pos: 0, total: 0, elementId: 'season-autumn' },
      winter: { name: '겨울', months: [12, 1, 2], pos: 0, total: 0, elementId: 'season-winter' }
    };

    reviewsList.forEach(r => {
      const rawMonth = r.MONTH !== undefined ? r.MONTH : r.month;
      const m = parseInt(rawMonth, 10);
      const pn = (r.REVIEW_PN || r.review_pn || '').toUpperCase();

      if (m >= 1 && m <= 12) {
        if (pn === 'P' || pn === 'N' || pn === 'F') {
          monthlyStats[m - 1].totalCount += 1;
          if (pn === 'P') monthlyStats[m - 1].posCount += 1;
        }

        for (const key in seasons) {
          if (seasons[key].months.includes(m)) {
            if (pn === 'P' || pn === 'N' || pn === 'F') {
              seasons[key].total += 1;
              if (pn === 'P') seasons[key].pos += 1;
            }
            break;
          }
        }
      }
    });

    if (barsContainer) {
        let htmlContent = '';
        let bestMonths = [];
        let maxPosRate = -1;

        monthlyStats.forEach(stat => {
          const posRate = stat.totalCount > 0 ? Math.round((stat.posCount / stat.totalCount) * 100) : 0;
          const barColor = stat.totalCount > 0 ? 'var(--primary, #C8530A)' : '#E8DCC8';

          if (stat.totalCount > 0) {
            if (posRate > maxPosRate) { maxPosRate = posRate; bestMonths = [`${stat.month}월`]; }
            else if (posRate === maxPosRate) { bestMonths.push(`${stat.month}월`); }
          }

          htmlContent += `
            <div style="display: flex; align-items: center; font-size: 11px; gap: 8px;">
              <span style="width: 28px; font-weight: 600; color: var(--text-2); text-align: right;">${stat.month}월</span>
              <div style="flex: 1; background: #E8DCC8; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: ${barColor}; width: ${posRate}%; height: 100%; border-radius: 4px; transition: width 0.6s ease;"></div>
              </div>
              <span style="width: 55px; color: var(--text-3); text-align: left;">${posRate}% (${stat.totalCount}건)</span>
            </div>`;
        });
        barsContainer.innerHTML = htmlContent;

        if (bestMonthEl) {
          if (bestMonths.length > 0 && maxPosRate > 0) {
            bestMonthEl.textContent = `${bestMonths.join(' · ')} (해당 월 평균 긍정율 ${maxPosRate}%)`;
          } else {
            bestMonthEl.textContent = '수집된 월별 데이터가 부족합니다.';
          }
        }
    }

    for (const key in seasons) {
      const targetCard = document.getElementById(seasons[key].elementId);
      if (targetCard) {
        const s = seasons[key];
        const rate = s.total > 0 ? Math.round((s.pos / s.total) * 100) : 0;
        const pctNode = targetCard.querySelector('.pct');
        const metaNode = targetCard.querySelector('.meta');
        if (pctNode) pctNode.textContent = `${rate}%`;
        if (metaNode) metaNode.textContent = `긍정 · 리뷰 ${s.total}개`;
      }
    }
  }

  // 🚀 [마무리 스위치] 모든 DOM 바인딩이 에러 없이 무사히 끝났으므로 화면을 메인에서 상세로 스위칭합니다.
  if (typeof showPage === 'function') {
      showPage('detail');
      console.log('상세 스위치 완료')
  }
  
}