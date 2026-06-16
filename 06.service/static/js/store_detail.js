// 📝 static/js/store_detail.js


// 카카오맵 사전 초기화
// 스크립트가 늦게 로드되더라도 브라우저가 kakao를 인식할 수 있게 최상단에서
if (typeof kakao !== 'undefined' && kakao.maps) {
    kakao.maps.load(function() {
        console.log("카카오 맵 엔진 수동 이니셜라이징 완료");
    });
}

// 상세 데이터 DOM 조작 및 동적 할당 함수
function renderStoreDetail(data) {
  // [보강] 데이터가 유효한지 안전 검사
  if (!data) return;

  // 1. 가게 기본 정보 바인딩 (view_header.html, view_info.html 등 연동)
  if (data.store) {
    const s = data.store;
    
    // 리뷰 긍부정율/개수 계산식
    let posRate = 0;
    const totalReviews = s.REVIEW_CNT || (data.reviews ? data.reviews.length : 0);

    if (data.reviews && data.reviews.length > 0) {
        const totalScore = data.reviews.reduce((sum, r) => sum + Number(r.PN_SCORE || 0), 0);
        posRate = Math.round((totalScore / data.reviews.length) * 100);
    } else {
        posRate = Math.round(s.PN_RATE || 0);
    }
    const negRate = 100 - posRate;
    
    const posCount = Math.round(totalReviews * (posRate / 100));
    const negCount = totalReviews - posCount

    // 텍스트 및 수치 매핑 (안정성을 위해 기본값 || 0 처리 추가)
    document.getElementById('detail-name').textContent = s.STORE_NAME || '이름 없음';
    document.getElementById('detail-category').textContent = s.CATEGORY || '-';
    document.getElementById('detail-rating').textContent = Number(s.STAR || 0).toFixed(1);

    document.getElementById('detail-reviews').textContent = `리뷰 ${totalReviews.toLocaleString()}개`;
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
            // 콤마로 쪼기 
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
    
    // 카카오맵
    const mapContainer = document.getElementById('mapBox');
    
    // window.kakao가 완벽히 존재할 때만
    if (mapContainer && s.LAT && s.LNG && window.kakao && window.kakao.maps) {
        
        // 카카오 비동기 로드
        kakao.maps.load(function() {
            const mapOption = {
                center: new kakao.maps.LatLng(parseFloat(s.LAT), parseFloat(s.LNG)), // 위경도 수치화 변환
                level: 3 // 지도 확대 레벨
            };

            // 카카오 지도 객체 생성
            const map = new kakao.maps.Map(mapContainer, mapOption);

            // 마커 및 마킹 좌표 설정
            const markerPosition = new kakao.maps.LatLng(parseFloat(s.LAT), parseFloat(s.LNG));
            const marker = new kakao.maps.Marker({
                position: markerPosition
            });

            // 지도 위에 마커 탑탑 고정
            marker.setMap(map);

            // 말풍선
            const storeName = s.STORE_NAME || '선택한 맛집';
            const iwContent = `<div style="padding:5px; font-size:12px; font-weight:700; color:var(--text); text-align:center; min-width:150px;">${storeName}</div>`;
            
            const infowindow = new kakao.maps.InfoWindow({
                content: iwContent
            });
            
            // 지도 진입 즉시 말풍선
            infowindow.open(map, marker);
        });
    }

    // 카카오맵 버튼 클릭 이벤트
    /*
    const mapBtn = document.getElementById('btn-kakaomap');
    if (mapBtn) {
        mapBtn.onclick = function() {
            window.open(`https://map.kakao.com/?q=${encodeURIComponent(fullAddress)}`, '_blank');
        };
    }
    */

    // --원형 차트--
    // 맨 위에서 계산한 퍼센트 개수 받아먹기
    document.getElementById('pie-pos-pct').textContent = `${posRate}%`;
    document.getElementById('legend-pos-val').textContent = `${posCount.toLocaleString()}개 (${posRate}%)`;
    document.getElementById('legend-neg-val').textContent = `${negCount.toLocaleString()}개 (${negRate}%)`;

    // Chart.js 도넛 차트 동적 렌더링
    const ctx = document.getElementById('pieChart');
    if (ctx) {
        // 기존에 그려져 있던 차트 객체가 메모리에 남아있으면 파괴(Destroy) 후 재출력하여 렌더링 꼬임 방지
        if (window.myPieChart) {
            window.myPieChart.destroy();
        }
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
                cutout: '75%', // 가운데 글씨 공간 확보
                plugins: {
                    legend: { display: false }, //차트 자체 기본 범례 숨김
                    tooltip: { enabled: true }
                },
                responsive: false,
                maintainAspectRatio: false
            }
        });
    }
    // 워드클라우드
    const wordWrap = document.getElementById('wordcloudWrap');
    if (wordWrap) {
        wordWrap.innerHTML = ""; // 바구니 초기화

        if (data.words && data.words.length > 0) {
            // 최고 언급 횟수 기준
            const maxWordCnt = data.words[0].CNT || 1;

            data.words.forEach(w => {
                const badge = document.createElement('span');
                
                // 긍부정 따른 클래스 지정
                if (w.WORD_PN === 'P') {
                    badge.className = 'wc-badge pos';
                } else if (w.WORD_PN === 'N') {
                    badge.className = 'wc-badge neg';
                } else {
                    badge.className = 'wc-badge neutral';
                }

                // 언급 수가 많을수록 글자 크기 키우기
                const ratio = w.CNT / maxWordCnt;
                const fontSize = Math.round(12 + (ratio * 12)); 
                badge.style.fontSize = `${fontSize}px`;
                //바구니에 넣기
                badge.textContent = w.WORD;
                wordWrap.appendChild(badge);
            });
        } else {
            wordWrap.innerHTML = `<div style="color: var(--text-3); font-size: 13px; text-align: center; width: 100%; padding: 30px 0;">분석된 키워드가 없습니다.</div>`;
        }
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
        let mSentiment = 'neutral';
        if (mMention === 0) {
            //  언급이 0회라면 대표메뉴여도 무조건 긍정반응 neutral
            mSentiment = 'neutral';
        } else if (m.BEST || mMention > (maxMention * 0.5)) {
            // 언급이 1회 이상일 때만 대표메뉴이거나 언급 상위 50%일 때 긍정반응 높음
            mSentiment = 'pos';
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

  // 30 일별 막대 그래프
  const trendCtx = document.getElementById('detailTrendChart');
    if (trendCtx) {
        // 초기화
        if (window.myTrendChart) {
            window.myTrendChart.destroy();
        }

        // 백엔드 데이터가 누락되었을 경우
        const trends = data.daily_trends || [];
        
        // Chart.js에 주입할 x축 라벨(날짜), y축 데이터(긍정/부정 개수) 배열 생성
        const labels = trends.map(t => t.date);
        const posData = trends.map(t => t.pos_cnt);
        const negData = trends.map(t => t.neg_cnt);

        // 긍부정 색상
        const posColor = getComputedStyle(document.documentElement).getPropertyValue('--pos').trim() || '#1A7A4A';
        const negColor = getComputedStyle(document.documentElement).getPropertyValue('--neg').trim() || '#C0392B';

        // 막대그래프 렌더링
        window.myTrendChart = new Chart(trendCtx, {
            type: 'bar', 
            data: {
                labels: labels, // X축: 날짜 리스트 (ex: "05-14", "05-15")
                datasets: [
                    {
                        label: '긍정 리뷰',
                        data: posData,
                        borderColor: posColor,       
                        backgroundColor: posColor + '90', 
                        pointRadius: 3,    
                        fill: true   
                    },
                    {
                        label: '부정 리뷰',
                        data: negData,
                        borderColor: negColor,   
                        backgroundColor: negColor + '90', 
                        pointRadius: 3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false } // HTML 상단에 직접 커스텀 범례 디자인을 이미 달아두셨으므로 차트 자체 범례는 숨김 처리!
                },
                scales: {
                    x: {
                        grid: { display: false }, // X축 격자선은 숨겨서 심플하고 정갈하게 표현
                        ticks: { color: '#64748B', font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true, // Y축 눈금선은 0부터 정직하게 시작
                        grid: { color: '#E2E8F0' }, // 은은한 회색 격자선
                        ticks: { 
                            stepSize: 1, // 개수 단위이므로 소수점 없이 1개, 2개 단위로 정밀 마감
                            color: '#64748B' 
                        }
                    }
                }
            }
        });
    }

  // 3. 실제 리뷰 샘플 리스트 동적 생성 
  const posContainer = document.getElementById('det-pos-list');
  const negContainer = document.getElementById('det-neg-list');

  if (data.reviews) {
    // 3-1. 긍정(P) 리뷰 필터링 및 최대 2개 추출
    const posReviews = data.reviews.filter(r => r.REVIEW_PN === 'P').slice(0, 2);
    
    if (posContainer) {
      if (posReviews.length === 0) {
        posContainer.innerHTML = '<div class="no-data">수집된 긍정 리뷰가 없습니다.</div>';
      } else {
        posContainer.innerHTML = posReviews.map(r => `
          <div class="review-item review-pos">
            <div class="review-label">👍 긍정 후기 (점수: ${Number(r.PN_SCORE || 0).toFixed(2)})</div>
            <div class="review-text">${r.CONTENT}</div>
          </div>
        `).join('');
      }
    }

    // 3-2. 부정/개선(N 또는 F) 리뷰 필터링 및 최대 2개 추출
    const negReviews = data.reviews.filter(r => r.REVIEW_PN === 'N' || r.REVIEW_PN === 'F').slice(0, 2);
    
    if (negContainer) {
      if (negReviews.length === 0) {
        negContainer.innerHTML = '<div class="no-data">수집된 개선 요구 리뷰가 없습니다.</div>';
      } else {
        negContainer.innerHTML = negReviews.map(r => `
          <div class="review-item review-neg">
            <div class="review-label">👎 개선 요구 후기 (점수: ${Number(r.PN_SCORE || 0).toFixed(2)})</div>
            <div class="review-text">${r.CONTENT}</div>
          </div>
        `).join('');
      }
    }
  }

  // 4. AI 개선 리포트 동적 생성 (HTML 통째로 주입하는 방식)
  const reportContainer = document.getElementById('reportGrid');
  
  if (reportContainer && data.store) {
    // DB의 STORE 테이블에서 AI_REPORT 컬럼 값을 가져옴
    const aiReportHtml = data.store.AI_REPORT;
    
    if (!aiReportHtml || aiReportHtml.trim() === "") {
      // 리포트 데이터가 비어있거나 아직 생성되지 않은 경우
      reportContainer.innerHTML = `
        <div class="no-data" style="grid-column: 1/-1; text-align: center; color: var(--text-3); padding: 20px;">
          분석된 AI 개선 리포트가 없습니다.
        </div>`;
    } else {
      reportContainer.innerHTML = aiReportHtml;
    }
  }

  // 5. 월별 방문 추천도 계산 및 가로 막대그래프 렌더링
  const barsContainer = document.getElementById('visitBars');
  const bestMonthEl = document.getElementById('best-visit-months');

  if (barsContainer && data.reviews) {
    // 1월부터 12월까지 통계 통 데이터 바구니 초기화
    const monthlyStats = Array.from({ length: 12 }, (_, i) => ({
      month: i + 1,
      posCount: 0,
      totalCount: 0
    }));

    // 데이터 집계 루프
    data.reviews.forEach(r => {
      // 🚀 [보강]: 대문자/소문자 키 모두 대응 및 완벽한 정수(Int) 형변환 보장
      const rawMonth = r.MONTH !== undefined ? r.MONTH : r.month;
      const m = parseInt(rawMonth, 10);
      
      // 🚀 [보강]: 대문자/소문자 PN 상태값 모두 대응
      const pn = (r.REVIEW_PN || r.review_pn || '').toUpperCase();

      if (m >= 1 && m <= 12) {
        // P(긍정), N(부정), F(개선) 모두 해당 월의 총 리뷰 수에 포함시킴
        if (pn === 'P' || pn === 'N' || pn === 'F') {
          monthlyStats[m - 1].totalCount += 1;
          if (pn === 'P') {
            monthlyStats[m - 1].posCount += 1;
          }
        }
      }
    });

    let htmlContent = '';
    let bestMonths = [];
    let maxPosRate = -1;

    // 가로 바 차트용 HTML 빌드
    monthlyStats.forEach(stat => {
      const posRate = stat.totalCount > 0 ? Math.round((stat.posCount / stat.totalCount) * 100) : 0;
      const barColor = stat.totalCount > 0 ? 'var(--primary, #C8530A)' : '#E8DCC8';

      // 최고 긍정율을 기록한 최적 방문 월 추출 (최소 리뷰 1개 이상 기준)
      if (stat.totalCount > 0) {
        if (posRate > maxPosRate) {
          maxPosRate = posRate;
          bestMonths = [`${stat.month}월`];
        } else if (posRate === maxPosRate) {
          bestMonths.push(`${stat.month}월`);
        }
      }

      htmlContent += `
        <div style="display: flex; align-items: center; font-size: 11px; gap: 8px;">
          <span style="width: 28px; font-weight: 600; color: var(--text-2); text-align: right;">${stat.month}월</span>
          <div style="flex: 1; background: #E8DCC8; height: 8px; border-radius: 4px; overflow: hidden; position: relative;">
            <div style="background: ${barColor}; width: ${posRate}%; height: 100%; border-radius: 4px; transition: width 0.6s ease;"></div>
          </div>
          <span style="width: 55px; color: var(--text-3); text-align: left;">
            ${posRate}% (${stat.totalCount}건)
          </span>
        </div>
      `;
    });

    barsContainer.innerHTML = htmlContent;

    // 상단 대표 최적 방문 가이드 문구 매핑
    if (bestMonthEl) {
      if (bestMonths.length > 0 && maxPosRate > 0) {
        bestMonthEl.textContent = `${bestMonths.join(' · ')} (해당 월 평균 긍정율 ${maxPosRate}%)`;
      } else {
        bestMonthEl.textContent = '수집된 월별 데이터가 부족합니다.';
      }
    }
  }

  // 6. 계절별 리뷰 통계 및 긍정률 카드 렌더링
  if (data.reviews) {
    // 계절별 기본 메타 데이터 구조 정의
    const seasons = {
      spring: { name: '봄', months: [3, 4, 5], pos: 0, total: 0, elementId: 'season-spring' },
      summer: { name: '여름', months: [6, 7, 8], pos: 0, total: 0, elementId: 'season-summer' },
      autumn: { name: '가을', months: [9, 10, 11], pos: 0, total: 0, elementId: 'season-autumn' },
      winter: { name: '겨울', months: [12, 1, 2], pos: 0, total: 0, elementId: 'season-winter' }
    };

    // 리뷰 데이터를 계절별로 매핑 분류
    data.reviews.forEach(r => {
      const rawMonth = r.MONTH !== undefined ? r.MONTH : r.month;
      const m = parseInt(rawMonth, 10);
      const pn = (r.REVIEW_PN || r.review_pn || '').toUpperCase();
      
      if (!m) return;

      for (const key in seasons) {
        if (seasons[key].months.includes(m)) {
          if (pn === 'P' || pn === 'N' || pn === 'F') {
            seasons[key].total += 1;
            if (pn === 'P') {
              seasons[key].pos += 1;
            }
          }
          break;
        }
      }
    });

    // view_visit.html 내 정의된 계절별 요소에 데이터 주입
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
}