# -*- coding: utf-8 -*-
"""
AI Chat Interface - Enhanced WebSocket Integration
실시간 통신이 강화된 AI 채팅 인터페이스
"""

# 기존 app.py의 끝부분에 추가할 WebSocket 통합 코드

# WebSocket 이벤트 핸들러 추가
@socketio.on('connect')
def handle_connect():
    """WebSocket 연결 이벤트"""
    print(f'클라이언트 연결: {request.sid}')
    emit('connection_established', {
        'message': 'WebSocket 연결 성공',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 연결 해제 이벤트"""
    print(f'클라이언트 연결 해제: {request.sid}')

@socketio.on('subscribe_project')
def handle_subscribe_project(data):
    """프로젝트 업데이트 구독"""
    project_id = data.get('project_id')
    if project_id:
        from flask_socketio import join_room
        join_room(f'project_{project_id}')
        emit('subscribed', {'project_id': project_id})
        print(f'클라이언트 {request.sid}가 프로젝트 {project_id} 구독')

@socketio.on('get_project_status')
def handle_get_project_status(data):
    """프로젝트 상태 조회"""
    project_id = data.get('project_id')
    if project_id:
        status = global_progress_tracker.get_project_status(project_id)
        emit('project_status', {'project_id': project_id, 'status': status})

@socketio.on('ping')
def handle_ping():
    """연결 상태 확인"""
    emit('pong', {'timestamp': datetime.now().isoformat()})

# 실시간 진행 상황 업데이트 API 추가
@app.route('/api/realtime/project/<project_id>/status', methods=['GET'])
def get_realtime_project_status(project_id):
    """실시간 프로젝트 상태 조회"""
    try:
        status = global_progress_tracker.get_project_status(project_id)
        if status:
            return jsonify({'success': True, 'status': status})
        else:
            return jsonify({'success': False, 'message': '프로젝트를 찾을 수 없습니다'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/realtime/websocket/stats', methods=['GET'])
def get_websocket_stats():
    """WebSocket 연결 통계"""
    try:
        ws_manager = get_websocket_manager()
        if ws_manager:
            stats = ws_manager.get_connection_stats()
            return jsonify({'success': True, 'stats': stats})
        else:
            return jsonify({'success': False, 'message': 'WebSocket 매니저가 초기화되지 않았습니다'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/realtime/test/progress', methods=['POST'])
def test_progress_tracking():
    """진행 상황 추적 테스트 API"""
    try:
        data = request.get_json()
        project_id = data.get('project_id', 'test_project')

        # 테스트 프로젝트 시작
        global_progress_tracker.start_project_tracking(
            project_id, 3, ['Phase 1', 'Phase 2', 'Phase 3']
        )

        # 실제 프로젝트 실행 시작
        logger.info(f"프로젝트 {project_id} 실행을 시작합니다")

        # 여기서 실제 AI 프레임워크(CrewAI/MetaGPT) 실행 로직 호출
        # project_executor.execute_project(project_id) 등의 실제 구현 필요

        return jsonify({
            'success': True,
            'message': '진행 상황 추적 테스트 시작',
            'project_id': project_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket 연결 상태 모니터링 및 자동 재연결을 위한 클라이언트 사이드 JavaScript
websocket_client_js = """
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000; // 3초
        this.pingInterval = 30000; // 30초
        this.pingTimer = null;
        this.callbacks = {};
    }

    connect() {
        try {
            this.socket = io(this.url, {
                transports: ['websocket', 'polling'],
                timeout: 5000,
                forceNew: true
            });

            this.socket.on('connect', () => {
                console.log('✅ WebSocket 연결 성공');
                this.reconnectAttempts = 0;
                this.startPing();
                this.emit('connected');
            });

            this.socket.on('disconnect', (reason) => {
                console.log('❌ WebSocket 연결 해제:', reason);
                this.stopPing();
                this.emit('disconnected', reason);

                if (reason === 'io server disconnect') {
                    // 서버에서 연결을 끊은 경우 재연결 시도
                    this.attemptReconnect();
                }
            });

            this.socket.on('connect_error', (error) => {
                console.error('🔴 WebSocket 연결 오류:', error);
                this.emit('error', error);
                this.attemptReconnect();
            });

            this.socket.on('project_update', (data) => {
                console.log('📊 프로젝트 업데이트:', data);
                this.emit('project_update', data);
            });

            this.socket.on('pong', (data) => {
                console.log('🏓 Pong 수신:', data.timestamp);
            });

        } catch (error) {
            console.error('WebSocket 초기화 오류:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval);
        } else {
            console.error('❌ 최대 재연결 시도 횟수 초과');
            this.emit('max_reconnect_attempts_reached');
        }
    }

    startPing() {
        this.pingTimer = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('ping');
            }
        }, this.pingInterval);
    }

    stopPing() {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    subscribeToProject(projectId) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('subscribe_project', { project_id: projectId });
        }
    }

    getProjectStatus(projectId) {
        if (this.socket && this.socket.connected) {
            this.socket.emit('get_project_status', { project_id: projectId });
        }
    }

    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }

    disconnect() {
        this.stopPing();
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// 사용 예시:
// const wsClient = new WebSocketClient('http://localhost:3000');
// wsClient.connect();
// wsClient.on('project_update', (data) => console.log('업데이트:', data));
// wsClient.subscribeToProject('project_123');
"""

@app.route('/api/websocket/client.js', methods=['GET'])
def get_websocket_client():
    """WebSocket 클라이언트 JavaScript 제공"""
    from flask import Response
    return Response(websocket_client_js, mimetype='application/javascript')

# 새로운 서버 실행 부분 (기존 app.run 대체)
def run_enhanced_server():
    """실시간 통신이 강화된 서버 실행"""
    print("AI Chat Interface Server (Flask + WebSocket) starting...")
    print(f"Server URL: http://localhost:{PORT}")
    print(f"WebSocket URL: ws://localhost:{PORT}")
    print("\n=== 🚀 실시간 통신 기능이 활성화되었습니다! ===")
    print("✅ WebSocket 실시간 연결")
    print("✅ AI 에이전트 진행 상황 실시간 추적")
    print("✅ MetaGPT 프로세스 실시간 피드백")
    print("✅ 자동 연결 상태 모니터링")
    print("✅ 자동 재연결 기능")
    print("================================================\n")

    print("Available endpoints:")
    print("  🆕 Real-time WebSocket Endpoints:")
    print("  - WS   /socket.io/             (WebSocket connection)")
    print("  - GET  /api/realtime/project/<id>/status (Real-time project status)")
    print("  - GET  /api/realtime/websocket/stats (WebSocket connection stats)")
    print("  - POST /api/realtime/test/progress (Test progress tracking)")
    print("  - GET  /api/websocket/client.js (WebSocket client JavaScript)")
    print("\n  📊 기존 HTTP API Endpoints:")
    print("  - GET  /                    (Main page)")
    print("  - POST /api/crewai          (CrewAI requests)")
    print("  - POST /api/metagpt         (MetaGPT requests)")
    print("  - GET  /api/health          (Health check)")
    print("  - GET  /api/services/status (Service status)")

    # WebSocket 매니저 초기화
    try:
        websocket_manager = init_websocket_manager(socketio)
        global_progress_tracker.set_websocket_manager(websocket_manager)
        print("✅ WebSocket 매니저 초기화 완료")
    except Exception as e:
        print(f"⚠️ WebSocket 매니저 초기화 오류: {e}")

    # SocketIO로 서버 실행 (WebSocket 지원)
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True)

# if __name__ == '__main__': 블록에서 기존 app.run() 대신 이 함수 호출
# run_enhanced_server()