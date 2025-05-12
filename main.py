from flask import Flask, render_template, jsonify
import json
import os
from search import analyze_images_and_save_results
from classification import main as classify_images

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-classification', methods=['GET'])
def run_classification():
    # 이미지 분류 실행
    try:
        classification_results = classify_images()
        return jsonify({"success": True, "classification": classification_results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/run-search', methods=['GET'])
def run_search():
    # 이미지 위치 분석 실행
    analyze_images_and_save_results()
    
    # 저장된 결과 파일 읽기
    try:
        with open('identified_locations.json', 'r', encoding='utf-8') as f:
            locations = json.load(f)
        return jsonify({"success": True, "locations": locations})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/run-workflow', methods=['GET'])
def run_workflow():
    # 전체 워크플로우 실행: 분류 -> 검색
    try:
        # 1. 이미지 분류 실행
        classification_results = classify_images()
        
        # 2. 이미지 위치 분석 실행
        analyze_images_and_save_results()
        
        # 3. 위치 분석 결과 읽기
        with open('identified_locations.json', 'r', encoding='utf-8') as f:
            locations = json.load(f)
            
        # 4. 결과 반환
        return jsonify({
            "success": True, 
            "classification": classification_results,
            "locations": locations
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/get-results', methods=['GET'])
def get_results():
    # 이미 저장된 결과 파일들 읽기
    try:
        results = {}
        
        # 분류 결과 읽기
        if os.path.exists('classification_results.json'):
            with open('classification_results.json', 'r', encoding='utf-8') as f:
                results["classification"] = json.load(f)
        
        # 위치 분석 결과 읽기
        if os.path.exists('identified_locations.json'):
            with open('identified_locations.json', 'r', encoding='utf-8') as f:
                results["locations"] = json.load(f)
                
        if results:
            return jsonify({"success": True, "results": results})
        else:
            return jsonify({"success": False, "error": "결과 파일이 존재하지 않습니다."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)


