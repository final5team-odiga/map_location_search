// DOM 요소 참조
const logDiv = document.getElementById("log");
const loadingDiv = document.getElementById("loading");
const summaryDiv = document.getElementById("summary");

// 지도가 초기화된 후 호출되는 함수
function onMapReady() {
  // 버튼 이벤트 리스너 설정
  document
    .getElementById("run-classification")
    .addEventListener("click", runClassification);
  document.getElementById("run-search").addEventListener("click", runAnalysis);
  document
    .getElementById("run-workflow")
    .addEventListener("click", runWorkflow);
  document
    .getElementById("load-results")
    .addEventListener("click", loadResults);
  document.getElementById("clear-map").addEventListener("click", clearMap);
}

function runClassification() {
  clearMap();
  loadingDiv.style.display = "block";
  logDiv.innerText = "이미지 분류를 시작합니다...\n";
  summaryDiv.style.display = "none";

  fetch("/run-classification")
    .then((response) => response.json())
    .then((data) => {
      loadingDiv.style.display = "none";
      if (data.success) {
        logDiv.innerText += "분류가 완료되었습니다.\n";
        displayClassificationResults(data.classification);
      } else {
        logDiv.innerText += `오류 발생: ${data.error}\n`;
      }
    })
    .catch((error) => {
      loadingDiv.style.display = "none";
      logDiv.innerText += `요청 실패: ${error}\n`;
    });
}

function runAnalysis() {
  clearMap();
  loadingDiv.style.display = "block";
  logDiv.innerText = "이미지 분석을 시작합니다...\n";
  summaryDiv.style.display = "none";

  fetch("/run-analysis")
    .then((response) => response.json())
    .then((data) => {
      loadingDiv.style.display = "none";
      if (data.success) {
        logDiv.innerText += "분석이 완료되었습니다.\n";
        displayLocations(data.locations);
      } else {
        logDiv.innerText += `오류 발생: ${data.error}\n`;
      }
    })
    .catch((error) => {
      loadingDiv.style.display = "none";
      logDiv.innerText += `요청 실패: ${error}\n`;
    });
}

function runWorkflow() {
  clearMap();
  loadingDiv.style.display = "block";
  logDiv.innerText = "전체 워크플로우(분류 -> 위치 분석)를 시작합니다...\n";
  summaryDiv.style.display = "none";

  fetch("/run-workflow")
    .then((response) => response.json())
    .then((data) => {
      loadingDiv.style.display = "none";
      if (data.success) {
        logDiv.innerText += "워크플로우가 완료되었습니다.\n";

        // 분류 결과 표시
        logDiv.innerText += "\n== 분류 결과 ==\n";
        const personCount = Object.values(data.classification).filter(
          (val) => val === true
        ).length;
        logDiv.innerText += `사람 이미지: ${personCount}개\n`;
        logDiv.innerText += `배경 이미지: ${
          Object.keys(data.classification).length - personCount
        }개\n`;

        // 위치 분석 결과 표시
        displayLocations(data.locations);
      } else {
        logDiv.innerText += `오류 발생: ${data.error}\n`;
      }
    })
    .catch((error) => {
      loadingDiv.style.display = "none";
      logDiv.innerText += `요청 실패: ${error}\n`;
    });
}

function loadResults() {
  clearMap();
  logDiv.innerText = "저장된 결과를 불러옵니다...\n";
  summaryDiv.style.display = "none";

  fetch("/get-results")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        logDiv.innerText += "결과를 불러왔습니다.\n";

        if (data.results.classification) {
          displayClassificationResults(data.results.classification);
        }

        if (data.results.locations) {
          displayLocations(data.results.locations);
        }
      } else {
        logDiv.innerText += `오류 발생: ${data.error}\n`;
      }
    })
    .catch((error) => {
      logDiv.innerText += `요청 실패: ${error}\n`;
    });
}

function displayClassificationResults(classification) {
  const personImages = [];
  const backgroundImages = [];

  Object.entries(classification).forEach(([imageId, isPerson]) => {
    if (isPerson) {
      personImages.push(imageId);
    } else {
      backgroundImages.push(imageId);
    }
  });

  // 요약 정보 표시
  let summaryText = `총 이미지: ${Object.keys(classification).length}개 | `;
  summaryText += `사람 이미지: ${personImages.length}개 | `;
  summaryText += `배경 이미지: ${backgroundImages.length}개`;

  summaryDiv.textContent = summaryText;
  summaryDiv.style.display = "block";

  // 로그에 결과 표시
  logDiv.innerText += "\n== 분류 결과 ==\n";

  if (personImages.length > 0) {
    logDiv.innerText += "👤 사람으로 분류된 이미지:\n";
    personImages.forEach((img) => {
      logDiv.innerText += `- ${img}\n`;
    });
    logDiv.innerText += "\n";
  }

  if (backgroundImages.length > 0) {
    logDiv.innerText += "🏞️ 배경으로 분류된 이미지:\n";
    backgroundImages.forEach((img) => {
      logDiv.innerText += `- ${img}\n`;
    });
    logDiv.innerText += "\n";
  }
}

function displayLocations(locations) {
  // 위치 정보 분류
  const personImages = [];
  const errorImages = [];
  const validLocations = [];

  // 데이터 분류
  Object.entries(locations).forEach(([imageName, location]) => {
    if (location === "person") {
      personImages.push(imageName);
    } else if (location === "Error analyzing image") {
      errorImages.push(imageName);
    } else {
      validLocations.push([imageName, location]);
    }
  });

  // 요약 정보 표시
  let summaryText = `총 이미지: ${Object.keys(locations).length}개 | `;
  summaryText += `위치 표시: ${validLocations.length}개 | `;
  summaryText += `사람 이미지: ${personImages.length}개 | `;
  summaryText += `오류: ${errorImages.length}개`;

  summaryDiv.textContent = summaryText;
  summaryDiv.style.display = "block";

  // 사람 이미지 로그에 표시
  if (personImages.length > 0) {
    logDiv.innerText += "👤 사람으로 분류된 이미지 (지도에 표시되지 않음):\n";
    personImages.forEach((img) => {
      logDiv.innerText += `- ${img}\n`;
    });
    logDiv.innerText += "\n";
  }

  // 오류 이미지 로그에 표시
  if (errorImages.length > 0) {
    logDiv.innerText += "❌ 오류가 발생한 이미지 (지도에 표시되지 않음):\n";
    errorImages.forEach((img) => {
      logDiv.innerText += `- ${img}\n`;
    });
    logDiv.innerText += "\n";
  }

  if (validLocations.length === 0) {
    logDiv.innerText += "표시할 유효한 위치 정보가 없습니다.\n";
    return;
  }

  // 지오코딩 서비스 초기화
  const geocoder = new google.maps.Geocoder();
  let processedCount = 0;

  // 유효한 위치만 지도에 표시
  validLocations.forEach(([imageName, locationName], index) => {
    // 위치 이름으로 좌표 검색
    geocoder.geocode({ address: locationName }, function (results, status) {
      processedCount++;

      if (status === "OK" && results[0]) {
        const position = results[0].geometry.location;
        const latLng = {
          lat: position.lat(),
          lng: position.lng(),
        };

        // 마커 추가
        const marker = new google.maps.Marker({
          position: latLng,
          map: map,
          title: `${imageName}: ${locationName}`,
          label: (index + 1).toString(),
        });
        markers.push(marker);

        // 정보창 추가
        const infoWindow = new google.maps.InfoWindow({
          content: `<div><strong>${imageName}</strong><br>${locationName}</div>`,
        });

        marker.addListener("click", () => {
          infoWindow.open(map, marker);
        });

        // 로그에 텍스트 출력
        logDiv.innerText += `📍 ${
          index + 1
        }. ${imageName}: ${locationName}\n위도: ${latLng.lat.toFixed(
          6
        )}, 경도: ${latLng.lng.toFixed(6)}\n\n`;

        // 좌표 추가
        pathCoordinates.push(latLng);

        // 모든 위치가 처리되면 경로 그리기 및 지도 조정
        if (processedCount === validLocations.length) {
          drawPath();
          adjustMapView();
        }
      } else {
        logDiv.innerText += `❌ ${imageName}: "${locationName}" - 좌표를 찾을 수 없습니다. (${status})\n\n`;

        // 모든 위치가 처리되면 경로 그리기 및 지도 조정
        if (processedCount === validLocations.length) {
          drawPath();
          adjustMapView();
        }
      }
    });
  });
}

function drawPath() {
  // 경로를 그릴 좌표가 2개 이상인 경우에만 그리기
  if (pathCoordinates.length < 2) {
    return;
  }

  // 이전 선 제거
  if (polyline) {
    polyline.setMap(null);
  }

  // 새 선 그리기
  polyline = new google.maps.Polyline({
    path: pathCoordinates,
    geodesic: true,
    strokeColor: "#FF0000",
    strokeOpacity: 1.0,
    strokeWeight: 3,
  });

  polyline.setMap(map);
}

function adjustMapView() {
  // 마커가 없으면 조정하지 않음
  if (markers.length === 0) {
    return;
  }

  // 모든 마커를 포함하는 경계 생성
  const bounds = new google.maps.LatLngBounds();
  markers.forEach((marker) => {
    bounds.extend(marker.getPosition());
  });

  // 지도 경계 조정
  map.fitBounds(bounds);

  // 마커가 하나만 있는 경우 적절한 줌 레벨 설정
  if (markers.length === 1) {
    map.setZoom(10);
  }
}

function clearMap() {
  // 마커 제거
  markers.forEach((marker) => {
    marker.setMap(null);
  });
  markers = [];

  // 경로 제거
  if (polyline) {
    polyline.setMap(null);
    polyline = null;
  }

  // 좌표 배열 초기화
  pathCoordinates = [];

  // 로그 초기화
  logDiv.innerText = "지도가 초기화되었습니다.\n";

  // 요약 정보 숨기기
  summaryDiv.style.display = "none";
}
