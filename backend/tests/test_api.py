import os
os.environ["DATABASE_URL"]="sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine
from app.db.seed import seed
Base.metadata.drop_all(bind=engine); seed()
client=TestClient(app)

def test_health(): assert client.get("/health").json()["status"]=="ok"
def test_login_and_catalogue():
    r=client.post("/api/v1/auth/login",json={"email":"doctor@example.com","password":"Demo@12345"}); assert r.status_code==200
    token=r.json()["access_token"]; products=client.get("/api/v1/products?limit=10",headers={"Authorization":f"Bearer {token}"}); assert products.status_code==200 and len(products.json())==10

def test_order():
    token=client.post("/api/v1/auth/login",json={"email":"doctor@example.com","password":"Demo@12345"}).json()["access_token"]
    products=client.get("/api/v1/products?limit=1").json(); pid=products[0]["id"]
    r=client.post("/api/v1/orders",headers={"Authorization":f"Bearer {token}"},json={"items":[{"product_id":pid,"quantity":2}]}); assert r.status_code==200 and r.json()["total"]
