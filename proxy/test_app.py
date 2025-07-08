import os
import pytest
from unittest.mock import patch, mock_open
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_models_no_filter(client):
    """Test /v1/models without any filtering."""
    with patch('requests.get') as mock_get, \
         patch('os.path.exists') as mock_exists:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {"id": "model1", "created": 123, "object": "model"},
                {"id": "model2", "created": 456, "object": "model"}
            ]
        }
        mock_exists.return_value = False
        
        response = client.get('/v1/models')
        assert response.status_code == 200
        data = response.json
        assert len(data['data']) == 2
        assert data['data'][0]['id'] == 'model1'
        assert data['data'][1]['id'] == 'model2'

def test_get_models_with_default_filter_file(client):
    """Test /v1/models with filter-models.txt present."""
    with patch('requests.get') as mock_get, \
         patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data="model1\n")) as mock_file:
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {"id": "model1", "created": 123, "object": "model"},
                {"id": "model2", "created": 456, "object": "model"}
            ]
        }
        mock_exists.return_value = True
        
        response = client.get('/v1/models')
        assert response.status_code == 200
        data = response.json
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'model1'

@patch.dict(os.environ, {'MODEL_FILTER_FILE': 'custom-filters.txt'})
def test_get_models_with_env_var_filter_file(client):
    """Test /v1/models with MODEL_FILTER_FILE environment variable."""
    with patch('requests.get') as mock_get, \
         patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data="model2\n")) as mock_file:
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {"id": "model1", "created": 123, "object": "model"},
                {"id": "model2", "created": 456, "object": "model"}
            ]
        }
        mock_exists.return_value = True
        
        response = client.get('/v1/models')
        assert response.status_code == 200
        data = response.json
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == 'model2'

@patch.dict(os.environ, {'MODEL_FILTER_FILE': 'non-existent-filters.txt'})
def test_get_models_with_non_existent_filter_file(client):
    """Test /v1/models with a non-existent filter file."""
    with patch('requests.get') as mock_get, \
         patch('os.path.exists') as mock_exists:
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {"id": "model1", "created": 123, "object": "model"},
                {"id": "model2", "created": 456, "object": "model"}
            ]
        }
        mock_exists.return_value = False
        
        response = client.get('/v1/models')
        assert response.status_code == 200
        data = response.json
        assert len(data['data']) == 2

def test_get_models_with_wildcard_filter(client):
    """Test /v1/models with wildcard filtering."""
    filter_content = "google/*\nopenai/gpt-4*"
    mock_models = {
        "data": [
            {"id": "google/gemini-pro", "created": 123, "object": "model"},
            {"id": "google/gemini-flash", "created": 123, "object": "model"},
            {"id": "openai/gpt-4o", "created": 456, "object": "model"},
            {"id": "openai/gpt-3.5-turbo", "created": 789, "object": "model"},
            {"id": "anthropic/claude-3-opus", "created": 101, "object": "model"}
        ]
    }
    
    with patch('requests.get') as mock_get, \
         patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data=filter_content)):
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_models
        mock_exists.return_value = True
        
        response = client.get('/v1/models')
        assert response.status_code == 200
        data = response.json
        
        returned_ids = {model['id'] for model in data['data']}
        expected_ids = {"google/gemini-pro", "google/gemini-flash", "openai/gpt-4o"}
        
        assert len(returned_ids) == 3
        assert returned_ids == expected_ids