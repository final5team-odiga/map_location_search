import os
import json
import requests
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContainerClient

# 환경변수 로드
load_dotenv()

def get_blob_list(connection_string, container_name):
    """Azure Blob Storage 컨테이너에서 모든 Blob 목록을 가져옵니다."""
    try:
        # BlobServiceClient 생성
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # 컨테이너 클라이언트 생성
        container_client = blob_service_client.get_container_client(container_name)
        
        # 컨테이너의 모든 Blob 목록 가져오기
        blob_list = container_client.list_blobs()
        
        # 결과를 리스트로 변환하고 이름 기준으로 정렬
        sorted_blobs = sorted([blob for blob in blob_list], key=lambda x: x.name)
        
        return sorted_blobs
    
    except Exception as e:
        print(f"Blob 목록을 가져오는 중 오류 발생: {e}")
        return []

def classify_image(image_url):
    """이미지에 사람이 있는지 분류합니다."""
    prediction_key = os.getenv("VISION_PREDICTION_KEY")
    prediction_url = os.getenv("VISION_PREDICTION_URL")
    
    # 요청 구성
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/json"
    }
    
    body = {"Url": image_url}
    
    # 요청
    response = requests.post(prediction_url, headers=headers, json=body)
    
    # 결과 확인
    if response.status_code == 200:
        result = response.json()
        
        # 사람 태그 확인 (태그 이름은 실제 모델에 맞게 조정 필요)
        for prediction in result["predictions"]:
            if prediction["tagName"].lower() == "person" and prediction["probability"] > 0.7:
                return True
        
        return False
    else:
        print(f"❌ 이미지 분류 오류: {response.status_code}")
        print(response.text)
        return False  # 오류 발생 시 기본값으로 False 반환

def main():
    # Azure Storage 연결 문자열 및 컨테이너 이름
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER")
    
    # Blob 목록 가져오기
    blobs = get_blob_list(connection_string, container_name)
    
    # 분류 결과를 저장할 딕셔너리
    classification_results = {}
    
    # 각 Blob에 대해 처리
    for i, blob in enumerate(blobs, 1):
        try:
            # 이미지 URL 생성
            image_url = f"https://5teamsfoundrystorage.blob.core.windows.net/{container_name}/{blob.name}"
            
            # 이미지 분류 수행
            is_person = classify_image(image_url)
            
            # 결과 저장
            classification_results[i] = is_person
            print(f"결과: {'사람 있음' if is_person else '사람 없음'}")
            
        except Exception as e:
            print(f"이미지 {blob.name} 처리 중 오류 발생: {e}")
            classification_results[i] = False  # 오류 발생 시 기본값으로 False 설정
    
    # 결과를 파일로 저장
    with open("classification_results.json", 'w') as f:
        json.dump(classification_results, f, indent=2)
    
    print("\n분류 완료. 결과가 classification_results.json에 저장되었습니다.")
    return classification_results

if __name__ == "__main__":
    main()

