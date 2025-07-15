import unittest
from app.classifier import classifier_node, AgentState

class TestClassifierNode(unittest.TestCase):

    def test_crm_classification(self):
        state: AgentState = {
            "question": "Can you help me track my order?",
            "chat_history": [
                {"user": "Hi", "assistant": "Hello! How can I help you?", "agent": "crm-agent"},
                {"user": "I need support for my purchase.", "assistant": "Sure, can you tell me the order ID?", "agent": "crm-agent"}
            ],
            "session_id": "123",
            "agent": "unknown"
        }

        result = classifier_node(state)
        self.assertEqual(result["agent"], "crm-agent")

    def test_unknown_classification(self):
        state: AgentState = {
            "question": "What’s the weather like today?",
            "chat_history": [
                {"user": "Hi", "assistant": "Hello! How can I help you?", "agent": "crm-agent"},
                {"user": "I want to know about today's weather.", "assistant": "I'm not sure I can help with that.", "agent": "crm-agent"}
            ],
            "session_id": "124",
            "agent": "unknown"
        }

        result = classifier_node(state)
        self.assertEqual(result["agent"], "unknown")

    def test_empty_history(self):
        state: AgentState = {
            "question": "Do you offer refunds?",
            "chat_history": [],
            "session_id": "125",
            "agent": "unknown"
        }

        result = classifier_node(state)
        self.assertIn(result["agent"], ["crm-agent", "unknown"]) 

if __name__ == "__main__":
    unittest.main()