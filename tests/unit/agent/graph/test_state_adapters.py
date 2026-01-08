"""
Unit tests for state serialization/deserialization adapters.

Tests verify that ConversationState can be correctly serialized to JSON
and deserialized back without data loss.
"""

import pytest
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.agent.graph.state_adapters import (
    serialize_message,
    deserialize_message,
    state_to_dict,
    dict_to_state,
    create_initial_state
)


class TestMessageSerialization:
    """Test message serialization and deserialization"""
    
    def test_serialize_human_message(self):
        """Test serializing a HumanMessage"""
        msg = HumanMessage(content="Hello")
        result = serialize_message(msg)
        
        assert result["role"] == "human"
        assert result["content"] == "Hello"
        assert result["type"] == "HumanMessage"
    
    def test_serialize_ai_message(self):
        """Test serializing an AIMessage"""
        msg = AIMessage(content="Hi there")
        result = serialize_message(msg)
        
        assert result["role"] == "ai"
        assert result["content"] == "Hi there"
        assert result["type"] == "AIMessage"
    
    def test_roundtrip_serialization(self):
        """Test that state can be serialized and deserialized without loss"""
        # Create initial state
        state = create_initial_state(
            session_id="test-roundtrip",
            call_direction="OUTBOUND",
            excel_row_index=5
        )
        
        # Add some data
        state["messages"] = [
            HumanMessage(content="Test message"),
            AIMessage(content="Test response")
        ]
        state["patient_full_name"] = "Juan Pérez"
        state["document_type"] = "CC"
        state["document_number"] = "12345678"
        
        # Serialize
        serialized = state_to_dict(state)
        
        # Deserialize
        deserialized = dict_to_state(serialized)
        
        # Verify critical fields
        assert deserialized["session_id"] == "test-roundtrip"
        assert deserialized["call_direction"] == "OUTBOUND"
        assert len(deserialized["messages"]) == 2


class TestCreateInitialState:
    """Test initial state creation"""
    
    def test_create_initial_inbound_state(self):
        """Test creating initial state for inbound call"""
        state = create_initial_state(
            session_id="inbound-123",
            call_direction="INBOUND"
        )
        
        assert state["session_id"] == "inbound-123"
        assert state["call_direction"] == "INBOUND"
        assert state["current_phase"] == "GREETING"
        assert state["messages"] == []
