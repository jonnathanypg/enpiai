from app import create_app
from extensions import db
from models.user import User
from models.distributor import Distributor

app = create_app()
with app.app_context():
    print("--- Reparación Masiva de Usuarios ---")
    dist = Distributor.query.first()
    if not dist:
        print("❌ No hay distribuidores. Crea uno primero.")
    else:
        users = User.query.all()
        fixed = 0
        for u in users:
            if not u.distributor_id:
                u.distributor_id = dist.id
                fixed += 1
                print(f"✅ Vinculando Usuario {u.id} ({u.email}) -> Distribuidor {dist.id}")
        
        db.session.commit()
        print(f"\n--- Proceso terminado. Se arreglaron {fixed} usuarios. ---")
