#!/usr/bin/env python
import os
from app import create_app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    print('启动服务器: http://0.0.0.0:5000')
    print('网络模式：局域网内其他电脑可以访问')
    print('请确保防火墙允许端口访问')
    print('局域网访问地址: http://你的IP:5000')
    print('本地访问地址: http://127.0.0.1:5000')
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)