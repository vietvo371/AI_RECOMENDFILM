import pytest
from app.services.chat_service import ChatService
from app.services.nlp_service import NLPService
from app.services.recommender_service import RecommenderService

@pytest.fixture
def chat_service():
    return ChatService()

@pytest.fixture
def nlp_service():
    return NLPService()

@pytest.fixture
def recommender_service():
    return RecommenderService() 