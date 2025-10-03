import pytest
from server import app as flask_app
from unittest.mock import patch
import json
from pathlib import Path
import copy

@pytest.fixture
def client():
    """
    Crée un client de test qui utilise des données simulées ("mockées")
    au lieu de lire/écrire dans les vrais fichiers.
    """
    # --- CORRECTION DE LA LIGNE CI-DESSOUS ---
    # On ne remonte que d'un seul dossier car test_server.py est à la racine
    base_dir = Path(__file__).resolve().parent
    # --- FIN DE LA CORRECTION ---

    with open(base_dir / 'clubs.json') as f:
        clubs_data = json.load(f)['clubs']
    with open(base_dir / 'competitions.json') as f:
        competitions_data = json.load(f)['competitions']

    flask_app.config['TESTING'] = True
    
    with patch('server.loadClubs') as mock_load_clubs, \
         patch('server.loadCompetitions') as mock_load_competitions, \
         patch('server.saveData') as mock_save_data:
        
        mock_load_clubs.return_value = copy.deepcopy(clubs_data)
        mock_load_competitions.return_value = copy.deepcopy(competitions_data)

        with flask_app.test_client() as client:
            yield client

def test_index_page_loads(client):
    """Teste que la page d'accueil se charge."""
    response = client.get('/')
    assert response.status_code == 200

def test_purchase_places_success(client):
    """
    Teste une réservation réussie et vérifie que les points sont déduits.
    """
    # ARRANGE
    form_data = {
        "club": "She Lifts",
        "competition": "Spring Festival",
        "places": "3"
    }

    # ACT
    response = client.post('/purchasePlaces', data=form_data)
    print(response.data)
    # ASSERT
    assert response.status_code == 200
    assert b"Points available: 9" in response.data