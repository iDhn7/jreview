function Clean-TimeDetail ($text) {
    if (-not $text) { return "" }
    $text = $text.Replace("접기", "").Trim()
    if (-not $text) { return "" }
    if ($text -like "*정기휴무*") { return "정기휴무" }

    $mainTime = ""
    $breakTime = ""
    $lastOrder = ""

    # 1. 메인 영업시간 추출 (항상 맨 앞에 나옴)
    # "11:00 - 21:00" 또는 "12:00 - 다음 날 00:40" 등
    if ($text -match '^(\d{2}:\d{2}\s*-\s*(?:다음\s*날\s*)?\d{2}:\d{2})') {
        $mainTime = $Matches[1].Trim()
        $text = $text.Replace($Matches[0], "")
    } elseif ($text -match '^((?:오후|새벽|오전)?\s*\d{2}:\d{2}\s*~\s*(?:오후|새벽|오전)?\s*\d{2}:\d{2})') {
        $mainTime = $Matches[1].Trim()
        $text = $text.Replace($Matches[0], "")
    } elseif ($text.StartsWith("24시간 영업") -or $text.StartsWith("24시간영업")) {
        $mainTime = "24시간 영업"
        $text = $text.Replace("24시간 영업", "").Replace("24시간영업", "")
    }

    # 2. 브레이크타임 추출 (예: 15:00 - 17:00 브레이크타임)
    if ($text -match '(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\s*브레이크타임') {
        $breakTime = $Matches[1].Trim()
        $text = $text.Replace($Matches[0], "")
    }

    # 3. 라스트오더 추출 (예: 20:20 라스트오더 또는 14:20, 20:20 라스트오더)
    if ($text -match '([\d{2}:\d{2},\s]*\d{2}:\d{2})\s*라스트오더') {
        $lastOrder = $Matches[1].Trim()
        $text = $text.Replace($Matches[0], "")
    }

    # 결합
    $resultParts = @()
    if ($mainTime) {
        $resultParts += $mainTime
    } elseif ($text -like "*24시간*") {
        $resultParts += "24시간 영업"
    } elseif ($text -like "*연중무휴*") {
        $resultParts += "연중무휴"
    }

    $extraInfo = @()
    if ($breakTime) { $extraInfo += "브레이크타임: $breakTime" }
    if ($lastOrder) { $extraInfo += "라스트오더: $lastOrder" }

    if ($extraInfo.Count -gt 0) {
        $resultParts += "(" + ($extraInfo -join ", ") + ")"
    }

    if ($resultParts.Count -gt 0) {
        return $resultParts -join " "
    }

    return $text.Trim()
}

function Parse-StoreTimes ($timeStr) {
    $days = @("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")
    $daysData = @{}
    foreach ($d in $days) { $daysData[$d] = "" }

    if (-not $timeStr -or $timeStr.Trim() -eq "") {
        return $daysData
    }

    $parts = $timeStr.Split('_') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

    $dayMap = @{
        '월' = '월요일'
        '화' = '화요일'
        '수' = '수요일'
        '목' = '목요일'
        '금' = '금요일'
        '토' = '토요일'
        '일' = '일요일'
    }

    # 1단계: '매일' 패턴 처리
    $hasDaily = $false
    $dailyTime = ""
    foreach ($part in $parts) {
        if ($part.StartsWith('매일')) {
            $rest = $part.Substring(2).TrimStart('_')
            $cleaned = Clean-TimeDetail $rest
            if ($cleaned) {
                $dailyTime = $cleaned
                $hasDaily = $true
                break
            }
        }
    }

    if ($hasDaily) {
        foreach ($d in $days) {
            $daysData[$d] = $dailyTime
        }
    }

    # 2단계: 개별 요일 패턴 처리 (수11:00... 등)
    foreach ($part in $parts) {
        if ($part.Length -ge 1) {
            $firstChar = $part.Substring(0, 1) # 확실하게 string 타입으로 추출
            
            if ($dayMap.ContainsKey($firstChar)) {
                $targetDay = $dayMap[$firstChar]
                $rest = $part.Substring(1).TrimStart('_')

                if ($rest -like "*정기휴무*") {
                    $daysData[$targetDay] = "정기휴무"
                    continue
                }

                $cleaned = Clean-TimeDetail $rest
                if ($cleaned) {
                    $daysData[$targetDay] = $cleaned
                }
            }
        }
    }

    # 3단계: 정기휴무 관련 특수 패턴 검사 (예: "화정기휴무 (매주 화요일)")
    foreach ($part in $parts) {
        $noSpacePart = $part.Replace(" ", "")
        foreach ($korDay in $dayMap.Keys) {
            $fullDay = $dayMap[$korDay]
            if ($noSpacePart -like "*${korDay}정기휴무*" -or $noSpacePart -like "*매주${korDay}요일*") {
                $daysData[$fullDay] = "정기휴무"
            }
        }
    }

    # 4단계: 만약 아직도 다 비어있고 '24시간'이나 '연중무휴' 키워드가 존재하면 적용
    $hasValue = $false
    foreach ($d in $days) {
        if ($daysData[$d]) { $hasValue = $true }
    }

    if (-not $hasValue) {
        foreach ($part in $parts) {
            if ($part -like "*24시간*") {
                foreach ($d in $days) { $daysData[$d] = "24시간 영업" }
                break
            } elseif ($part -like "*연중무휴*") {
                foreach ($d in $days) { $daysData[$d] = "연중무휴" }
                break
            }
        }
    }

    return $daysData
}

$fileDir = "D:\작업용폴더\영업시간 전처리"
$inputFile = Join-Path $fileDir "naver_info.csv"
$outputFile = Join-Path $fileDir "naver_info_processed.csv"

Write-Host "Reading $inputFile..."
$data = Import-Csv -Path $inputFile -Encoding UTF8

$days = @("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")

$results = @()

foreach ($row in $data) {
    $timeStr = $row.store_times_str
    $parsed = Parse-StoreTimes $timeStr

    # 신규 요일 컬럼 추가
    foreach ($day in $days) {
        $row | Add-Member -MemberType NoteProperty -Name $day -Value $parsed[$day] -Force
    }

    # 영업시간_정제 컬럼 생성
    $summaryParts = @()
    foreach ($day in $days) {
        $shortDay = $day.Substring(0, 1)
        $val = $parsed[$day]
        if ($val) {
            $summaryParts += "${shortDay}: ${val}"
        } else {
            $summaryParts += "${shortDay}: 정보 없음"
        }
    }
    $summaryStr = $summaryParts -join " | "
    $row | Add-Member -MemberType NoteProperty -Name "영업시간_정제" -Value $summaryStr -Force

    $results += $row
}

Write-Host "Saving to $outputFile..."
$results | Export-Csv -Path $outputFile -NoTypeInformation -Encoding UTF8

Write-Host "Pre-processing completed successfully!"
