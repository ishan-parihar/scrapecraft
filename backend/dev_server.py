from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any

app = FastAPI(title='ScrapeCraft Backend', version='1.0.0')

# Simple WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, investigation_id: str):
        await websocket.accept()
        if investigation_id not in self.active_connections:
            self.active_connections[investigation_id] = []
        self.active_connections[investigation_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, investigation_id: str):
        if investigation_id in self.active_connections:
            if websocket in self.active_connections[investigation_id]:
                self.active_connections[investigation_id].remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, investigation_id: str):
        if investigation_id in self.active_connections:
            for connection in self.active_connections[investigation_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

@app.get('/api/osint/investigations')
def get_investigations() -> List[Dict[str, Any]]:
    return [
        {
            'id': 'inv_001',
            'title': 'Sample Investigation',
            'description': 'Test investigation for development',
            'status': 'ACTIVE',
            'created_at': '2023-10-15T10:30:00Z',
            'classification': 'CONFIDENTIAL',
            'targets': [
                {
                    'id': 'target_001',
                    'name': 'example.com',
                    'type': 'DOMAIN',
                    'status': 'ACTIVE'
                }
            ],
            'collected_evidence': [
                {
                    'id': 'ev_001',
                    'source': 'example.com',
                    'source_type': 'WEB_CONTENT',
                    'reliability_score': 85,
                    'relevance_score': 90,
                    'content': {
                        'type': 'text',
                        'summary': 'Sample evidence data'
                    }
                }
            ],
            'threat_assessments': [
                {
                    'id': 'threat_001',
                    'title': 'Sample Threat',
                    'threat_level': 'MEDIUM',
                    'threat_type': 'CYBERSECURITY',
                    'likelihood': 60,
                    'impact': 70
                }
            ]
        }
    ]

@app.get('/api/osint/investigations/{investigation_id}')
def get_investigation(investigation_id: str):
    investigations = get_investigations()
    for inv in investigations:
        if inv['id'] == investigation_id:
            return inv
    return {'error': 'Investigation not found'}, 404

@app.post('/api/osint/investigations')
def create_investigation(data: dict):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return {
        'id': f'inv_{timestamp}',
        'title': data.get('title', 'New Investigation'),
        'description': data.get('description', ''),
        'status': 'ACTIVE',
        'created_at': datetime.now().isoformat(),
        'classification': data.get('classification', 'UNCLASSIFIED'),
        'targets': [],
        'collected_evidence': [],
        'threat_assessments': []
    }

@app.get('/api/osint/agents')
def get_agents():
    return [
        {
            'agent_id': 'agent_001',
            'name': 'Web Scraper',
            'type': 'SCRAPER',
            'status': 'IDLE',
            'capabilities': ['web_scraping', 'data_extraction']
        },
        {
            'agent_id': 'agent_002', 
            'name': 'Social Media Analyzer',
            'type': 'ANALYZER',
            'status': 'ACTIVE',
            'capabilities': ['social_media_analysis', 'sentiment_analysis']
        }
    ]

@app.get('/api/pipelines')
def get_pipelines():
    return [
        {
            'id': 'pipeline_001',
            'name': 'Web Scraping Pipeline',
            'description': 'Basic web scraping pipeline',
            'status': 'ACTIVE',
            'config': {
                'urls': ['https://example.com'],
                'output_format': 'json'
            }
        }
    ]

@app.get('/api/osint/investigations/{investigation_id}/agents')
def get_investigation_agents(investigation_id: str):
    # Get all agents and format them for the specific investigation
    agents_list = get_agents()
    return [
        {
            'agent_id': agent['agent_id'],
            'investigation_id': investigation_id,
            'name': agent['name'],
            'type': agent['type'],
            'current_status': agent['status'],
            'assigned_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'current_task': None,
            'performance_metrics': {
                'tasks_completed': 0,
                'success_rate': 100,
                'average_task_time': 0,
                'error_count': 0
            }
        }
        for agent in agents_list
    ]

@app.post('/api/osint/investigations/{investigation_id}/agents/assign')
def assign_agent_to_investigation(investigation_id: str, assignment: dict):
    return {
        'agent_id': assignment.get('agent_id'),
        'investigation_id': investigation_id,
        'status': 'assigned',
        'assigned_at': datetime.now().isoformat(),
        'message': f"Agent {assignment.get('agent_id')} assigned to investigation {investigation_id}"
    }

@app.put('/api/osint/agents/{agent_id}/status')
def update_agent_status(agent_id: str, status_update: dict):
    return {
        'agent_id': agent_id,
        'status': status_update.get('status', 'IDLE'),
        'updated_at': datetime.now().isoformat(),
        'message': f"Agent {agent_id} status updated to {status_update.get('status', 'IDLE')}"
    }

@app.post('/api/osint/agents/{agent_id}/tasks')
def assign_task_to_agent(agent_id: str, task: dict):
    return {
        'agent_id': agent_id,
        'task_id': f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'task': task,
        'status': 'assigned',
        'assigned_at': datetime.now().isoformat(),
        'message': f"Task assigned to agent {agent_id}"
    }

@app.get('/api/osint/agents/{agent_id}/performance')
def get_agent_performance(agent_id: str):
    return {
        'agent_id': agent_id,
        'investigation_id': 'current',
        'agent_type': 'SCRAPER',
        'current_status': 'IDLE',
        'assigned_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'current_task': None,
        'performance_metrics': {
            'tasks_completed': 10,
            'success_rate': 95,
            'average_task_time': 30,
            'error_count': 1
        }
    }

@app.websocket("/ws/{investigation_id}")
async def websocket_endpoint(websocket: WebSocket, investigation_id: str):
    await manager.connect(websocket, investigation_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get('type', 'response')
            
            if message_type == 'ping':
                await manager.send_personal_message({'type': 'pong'}, websocket)
            else:
                # Echo back or process the message
                response = {
                    'type': 'response',
                    'response': f"Received: {data.get('message', 'No message')}",
                    'investigation_id': investigation_id,
                    'timestamp': datetime.now().isoformat()
                }
                await manager.send_personal_message(response, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, investigation_id)

if __name__ == '__main__':
    print('🚀 ScrapeCraft Backend starting on http://localhost:8000')
    print('📚 API Documentation: http://localhost:8000/docs')
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')