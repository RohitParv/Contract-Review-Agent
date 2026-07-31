from shared.memory.conversation_store import InMemoryConversationStore


def test_append_and_read_history():
    store = InMemoryConversationStore()
    store.append_turn("s1", "user", "hello")
    store.append_turn("s1", "assistant", "hi there")

    history = store.history("s1")
    assert [t.role for t in history] == ["user", "assistant"]
    assert history[1].text == "hi there"


def test_sessions_are_isolated():
    store = InMemoryConversationStore()
    store.append_turn("s1", "user", "message in s1")
    assert store.history("s2") == []


def test_contract_and_profile_roundtrip():
    store = InMemoryConversationStore()
    store.set_contract("s1", "raw text")
    store.set_profile("s1", {"document_type": "lease"})
    store.set_risk_review("s1", {"overall_risk_level": "low"})

    assert store.get_contract("s1") == "raw text"
    assert store.get_profile("s1") == {"document_type": "lease"}
    assert store.get_risk_review("s1") == {"overall_risk_level": "low"}
