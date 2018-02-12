def test_can_pass():
    assert True

def test_health_endpoint(client):
    response = client.get('/health').json
    assert response == {'health': 'OK'}

