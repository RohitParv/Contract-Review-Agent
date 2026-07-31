from router import IntentRouter
from subagents.base import RouteDecision


def test_greeting_on_first_turn_vague_message():
    router = IntentRouter()
    assert router.classify("hi", session_id="s1") == RouteDecision.GREETING


def test_greeting_capability_question():
    router = IntentRouter()
    decision = router.classify("what can you help me with?", session_id="s2")
    assert decision == RouteDecision.GREETING


def test_greeting_only_fires_on_first_turn():
    router = IntentRouter()
    router.classify("hi", session_id="s3")
    # Same session, second turn — a vague word shouldn't re-trigger greeting.
    decision = router.classify("help", session_id="s3")
    assert decision != RouteDecision.GREETING


def test_review_route_when_contract_uploaded():
    router = IntentRouter()
    decision = router.classify(
        "here it is", session_id="s4", has_contract_upload=True
    )
    assert decision == RouteDecision.REVIEW


def test_review_route_on_explicit_phrasing():
    router = IntentRouter()
    decision = router.classify("please review this lease", session_id="s5")
    assert decision == RouteDecision.REVIEW


def test_qa_default_route():
    router = IntentRouter()
    decision = router.classify(
        "what is usually included in a security deposit clause?",
        session_id="s6",
    )
    assert decision == RouteDecision.QA
