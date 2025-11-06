"""
Agent Communication Protocol

This module provides the communication infrastructure for OSINT agents
to coordinate and share information.
"""

import asyncio
import json
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging
from dataclasses import dataclass, asdict

from pydantic import BaseModel


class MessageTypes(Enum):
    """Types of messages that can be sent between agents"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    DATA_SHARE = "data_share"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: MessageTypes
    priority: MessagePriority
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    requires_response: bool = False
    response_timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            **asdict(self),
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary"""
        return cls(
            id=data["id"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            message_type=MessageTypes(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            requires_response=data.get("requires_response", False),
            response_timeout=data.get("response_timeout", 30)
        )


class AgentCommunication:
    """
    Handles communication between OSINT agents.
    
    Provides message passing, coordination, and status monitoring.
    """
    
    def __init__(self, agent_id: str, logger: Optional[logging.Logger] = None):
        self.agent_id = agent_id
        self.logger = logger or logging.getLogger(f"{__name__}.{agent_id}")
        
        # Message handling
        self.message_handlers: Dict[MessageTypes, List[Callable]] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # Agent registry
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        
        # Communication channels
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.outbox: asyncio.Queue = asyncio.Queue()
        
        # Status tracking
        self.is_running = False
        self.message_stats = {
            "sent": 0,
            "received": 0,
            "errors": 0,
            "timeouts": 0
        }
        
        self.logger.info(f"Initialized communication system for agent {agent_id}")
    
    async def start(self):
        """Start the communication system"""
        self.is_running = True
        
        # Start message processing tasks
        asyncio.create_task(self._process_inbox())
        asyncio.create_task(self._process_outbox())
        
        self.logger.info(f"Communication system started for agent {self.agent_id}")
    
    async def stop(self):
        """Stop the communication system"""
        self.is_running = False
        self.logger.info(f"Communication system stopped for agent {self.agent_id}")
    
    def register_handler(self, message_type: MessageTypes, handler: Callable):
        """Register a handler for a specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
        self.logger.debug(f"Registered handler for {message_type.value}")
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]):
        """Register another agent for communication"""
        self.registered_agents[agent_id] = {
            **agent_info,
            "registered_at": datetime.utcnow()
        }
        self.logger.info(f"Registered agent: {agent_id}")
    
    async def send_message(
        self,
        receiver_id: str,
        message_type: MessageTypes,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
        correlation_id: Optional[str] = None,
        response_timeout: int = 30
    ) -> Optional[AgentMessage]:
        """
        Send a message to another agent.
        
        Returns the response message if requires_response is True.
        """
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            priority=priority,
            payload=payload,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id,
            requires_response=requires_response,
            response_timeout=response_timeout
        )
        
        # Add to outbox for processing
        await self.outbox.put(message)
        self.message_stats["sent"] += 1
        
        self.logger.debug(f"Sent {message_type.value} to {receiver_id}")
        
        # Wait for response if required
        if requires_response:
            response_future = asyncio.Future()
            self.pending_responses[message.id] = response_future
            
            try:
                response = await asyncio.wait_for(response_future, timeout=response_timeout)
                return response
            except asyncio.TimeoutError:
                self.message_stats["timeouts"] += 1
                self.logger.warning(f"Timeout waiting for response to {message.id}")
                return None
            finally:
                self.pending_responses.pop(message.id, None)
        
        return None
    
    async def broadcast_message(
        self,
        message_type: MessageTypes,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        exclude_agents: List[str] = None
    ):
        """Broadcast a message to all registered agents"""
        exclude_agents = exclude_agents or []
        
        for agent_id in self.registered_agents:
            if agent_id != self.agent_id and agent_id not in exclude_agents:
                await self.send_message(agent_id, message_type, payload, priority)
    
    async def send_task_request(
        self,
        receiver_id: str,
        task_data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[AgentMessage]:
        """Send a task request to another agent"""
        return await self.send_message(
            receiver_id=receiver_id,
            message_type=MessageTypes.TASK_REQUEST,
            payload=task_data,
            priority=priority,
            requires_response=True
        )
    
    async def send_data_share(
        self,
        receiver_id: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ):
        """Share data with another agent"""
        payload = {
            "data": data,
            "metadata": metadata or {}
        }
        
        await self.send_message(
            receiver_id=receiver_id,
            message_type=MessageTypes.DATA_SHARE,
            payload=payload
        )
    
    async def send_status_update(
        self,
        status: Dict[str, Any],
        broadcast: bool = False
    ):
        """Send status update"""
        if broadcast:
            await self.broadcast_message(
                message_type=MessageTypes.STATUS_UPDATE,
                payload=status
            )
        else:
            # Send to a coordinator or monitoring agent
            for agent_id in self.registered_agents:
                if "coordinator" in self.registered_agents[agent_id].get("role", "").lower():
                    await self.send_message(
                        receiver_id=agent_id,
                        message_type=MessageTypes.STATUS_UPDATE,
                        payload=status
                    )
                    break
    
    async def _process_inbox(self):
        """Process incoming messages"""
        while self.is_running:
            try:
                # Get message from inbox
                message = await asyncio.wait_for(self.inbox.get(), timeout=1.0)
                self.message_stats["received"] += 1
                
                # Handle the message
                await self._handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.message_stats["errors"] += 1
                self.logger.error(f"Error processing inbox message: {e}", exc_info=True)
    
    async def _process_outbox(self):
        """Process outgoing messages"""
        while self.is_running:
            try:
                # Get message from outbox
                message = await asyncio.wait_for(self.outbox.get(), timeout=1.0)
                
                # Send to target agent
                await self._deliver_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.message_stats["errors"] += 1
                self.logger.error(f"Error processing outbox message: {e}", exc_info=True)
    
    async def _handle_message(self, message: AgentMessage):
        """Handle an incoming message"""
        self.logger.debug(f"Received {message.message_type.value} from {message.sender_id}")
        
        # Check if this is a response to a pending request
        if message.correlation_id and message.correlation_id in self.pending_responses:
            future = self.pending_responses[message.correlation_id]
            if not future.done():
                future.set_result(message)
            return
        
        # Handle based on message type
        handlers = self.message_handlers.get(message.message_type, [])
        
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}", exc_info=True)
    
    async def _deliver_message(self, message: AgentMessage):
        """Deliver message to target agent"""
        target_agent = self.registered_agents.get(message.receiver_id)
        
        if not target_agent:
            self.logger.warning(f"Target agent {message.receiver_id} not found")
            return
        
        # Use actual communication delivery through message passing
        try:
            # Deliver message to target agent's message queue
            await self._deliver_message(message)
            
        except Exception as e:
            self.logger.error(f"Error delivering message to {message.receiver_id}: {e}")
    
    async def _deliver_message(self, message: AgentMessage):
        """Deliver message to target agent's message queue"""
        # Get target agent from registry
        target_agent = self.agent_registry.get_agent(message.receiver_id)
        if target_agent:
            # Add message to target's inbox
            if not hasattr(target_agent, 'message_queue'):
                target_agent.message_queue = []
            
            target_agent.message_queue.append({
                "message": message,
                "received_at": datetime.utcnow(),
                "status": "pending"
            })
            
            self.logger.info(f"Message delivered to agent {message.receiver_id}")
        else:
            self.logger.warning(f"Target agent {message.receiver_id} not found for message delivery")
    
    def get_status(self) -> Dict[str, Any]:
        """Get communication system status"""
        return {
            "agent_id": self.agent_id,
            "is_running": self.is_running,
            "registered_agents": len(self.registered_agents),
            "message_handlers": len(self.message_handlers),
            "pending_responses": len(self.pending_responses),
            "inbox_size": self.inbox.qsize(),
            "outbox_size": self.outbox.qsize(),
            "message_stats": self.message_stats.copy()
        }