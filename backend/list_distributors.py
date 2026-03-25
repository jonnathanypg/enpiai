from app import create_app
from models.distributor import Distributor

app = create_app()
with app.app_context():
    distributors = Distributor.query.all()
    print("ID    | Name")
    print("-" * 20)
    for d in distributors:
        print(f"{d.id:<5} | {d.name}")
