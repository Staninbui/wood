#!/usr/bin/env python3
"""
简化的测试应用，用于调试Cloud Run启动问题
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'wood-ebay-app-test'}), 200

@app.route('/')
def index():
    return jsonify({
        'message': 'Wood eBay App Test Version',
        'python_path': os.environ.get('PYTHONPATH', 'Not set'),
        'port': os.environ.get('PORT', '8080'),
        'working_dir': os.getcwd()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
