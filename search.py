import os
import json
import asyncio
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from pathlib import Path


import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents import ChatMessageContent, TextContent, ImageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings


dotenv_path = Path(r'C:/Users/EL0021/Desktop/imagesearch/.env')

# 환경 변수 로드
load_dotenv(dotenv_path=dotenv_path, override=True)



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

async def analyze_image_location(image_url, chat_completion_service):
    """멀티모달 AI를 사용하여 이미지의 위치 정보를 분석합니다."""
    try:
        
        # 실행 설정 생성
        execution_settings = OpenAIChatPromptExecutionSettings()
        
        # 시스템 메시지로 채팅 기록 생성 (키워드 인자 사용)
        chat_history = ChatHistory(system_message="""You are a location identification expert. Your task is to analyze the image and identify the location shown in it.
            If you can identify a specific location (city, landmark, etc.), provide that.
            If it's not possible to identify a specific location, provide your best guess of the region or country.
            If the image contains a person as the main subject, simply respond with 'person'.
            If the image is a landscape without clear location markers, respond with 'landscape'.""")

        # 텍스트 및 이미지 콘텐츠 생성
        text_content = TextContent(text="What location is shown in this image? Provide only the location name without explanation.")
        image_content = ImageContent(uri=image_url)
        
        # 사용자 메시지 생성 (키워드 인자 사용)
        user_message = ChatMessageContent(
            role=AuthorRole.USER,
            items=[text_content, image_content]
        )
        
        # 채팅 기록에 메시지 추가
        chat_history.add_message(user_message)

        # 채팅 완성 모델 호출 (settings 매개변수 추가)
        response = await chat_completion_service.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings
        )
        
        return response.content.strip()
    except Exception as e:
        print(f"이미지 분석 중 오류 발생: {e}")
        import traceback
        print(traceback.format_exc())  # 상세한 오류 정보 출력
        return "Error analyzing image"
    

async def collect_image_location_results(classification_results=None):

    # Azure Storage 연결 문자열 및 컨테이너 이름
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER")

    # Semantic Kernel 초기화
    kernel = sk.Kernel()
    
    # Azure OpenAI 서비스 설정
    service_id = "location_identifier"
    kernel.add_service(
        AzureChatCompletion(
            service_id=service_id,
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    )

    
    # 채팅 완성 서비스 가져오기
    chat_completion_service = kernel.get_service(service_id)

    # Blob 목록 가져오기
    blobs = get_blob_list(connection_string, container_name)

    # 결과를 저장할 딕셔너리
    results_dict = {}

    # 각 Blob에 대해 처리
    for i, blob in enumerate(blobs, 1):
        try:
            # 분류 결과가 있고 사람인 경우 건너뛰기 (선택적)
            if classification_results and (classification_results.get(str(i), False) or classification_results.get(i, False)):
                results_dict[i] = "person"
                print(f"이미지 {i}: 사람 이미지로 분류됨 - 건너뜀")
                continue

            # 이미지 URL 생성
            image_url = f"https://5teamsfoundrystorage.blob.core.windows.net/{container_name}/{blob.name}"


            # 이미지 위치 분석
            location = await analyze_image_location(image_url, chat_completion_service)
            
            # 결과 딕셔너리에 저장
            results_dict[i] = location
            print(f"이미지 {i} 위치: {location}")
            
        except Exception as e:
            print(f"이미지 {blob.name} 처리 중 오류 발생: {e}")
            results_dict[i] = "Error processing image"

    print("\n위치 분석 완료")
    return results_dict

def save_results_to_file(results_dict, filename="identified_locations.json"):
    """분석 결과를 JSON 파일로 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        print(f"분석 결과가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"결과 저장 중 오류 발생: {e}")

async def main():
    # 분류 결과 로드 (선택적)
    classification_results = None
    try:
        with open("classification_results.json", 'r') as f:
            classification_results = json.load(f)
        print("분류 결과를 로드했습니다.")
    except FileNotFoundError:
        print("분류 결과 파일을 찾을 수 없습니다. 모든 이미지를 분석합니다.")
    except json.JSONDecodeError:
        print("분류 결과 파일이 올바른 JSON 형식이 아닙니다. 모든 이미지를 분석합니다.")

    # 이미지 위치 분석 결과 수집
    results = await collect_image_location_results(classification_results)

    # 결과를 파일로 저장
    save_results_to_file(results)

    return results



def analyze_images_and_save_results():
    """이미지 분석을 실행하고 결과를 저장하는 함수"""
    # 비동기 함수를 실행하기 위한 코드
    import asyncio
    
    # 기존 main() 함수의 내용을 호출
    asyncio.run(main())
    
    # 분석 결과가 저장되었는지 확인
    if os.path.exists('identified_locations.json'):
        print("분석 결과가 identified_locations.json에 저장되었습니다.")
    else:
        print("분석 결과 저장 중 오류가 발생했습니다.")



if __name__ == "__main__":
    asyncio.run(main())