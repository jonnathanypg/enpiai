from app import create_app
from models.user import User
from models.distributor import Distributor

app = create_app()
with app.app_context():
    print(f"{'ID':<5} | {'Email':<30} | {'Dist_ID':<8} | {'Dist_Exists':<10}")
    print("-" * 60)
    users = User.query.all()
    for u in users:
        dist = Distributor.query.get(u.distributor_id) if u.distributor_id else None
        exists = "✅ SÍ" if dist else "❌ NO"
        print(f"{u.id:<5} | {u.email:<30} | {u.distributor_id if u.distributor_id else 'NONE':<8} | {exists:<10}")
