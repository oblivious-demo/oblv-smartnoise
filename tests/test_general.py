from io import BytesIO
from fastapi.testclient import TestClient
from app import app
import config 
import yaml

OBLV_MOCK_CONFIG_PATH = "tests/yaml/runtime_mwem_1.yaml"

def mock_config():
    with open(OBLV_MOCK_CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
            
    return config.Settings(**config_data)


config.settings = mock_config

client = TestClient(app)

def test_detail_get():
    # should get the values set
    response = client.get("/details")
    assert response.status_code == 200
    assert response.json() == {
        "n_parties" : 2,
        "epsilon" : 1,
        "num_samples" : 1000
    }

def test_detail_post():
    # should not allow post data
    files = [
        ("parameter", ("file1.txt", BytesIO(b"aaa"))),
        ("parameter", ("file2.txt", BytesIO(b"bbb"))),
    ]

    response = client.post("/details", files=files)
    assert response.status_code == 405
    