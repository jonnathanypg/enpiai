from app import create_app
from extensions import db
from models.user import User
from models.distributor import Distributor
import requests

app = create_app()
with app.app_context():
    print("--- Test de Conexión Interna Flask -> Gateway ---")
    user = User.query.filter_by(email="jonnathan.ypg@gmail.com").first()
    if not user:
        print("❌ Usuario no encontrado")
    else:
        print(f"✅ Usuario: {user.email}, Distributor ID: {user.distributor_id}")
        dist = Distributor.query.get(user.distributor_id)
        if not dist:
            print("❌ Distribuidor no encontrado en la DB")
        else:
            print(f"✅ Distribuidor: {dist.name}")
            # Intentar llamar al gateway como lo hace Flask
            try:
                res = requests.post(
                    "http://localhost:3001/session/init",
                    json={"companyId": str(dist.id)},
                    timeout=5
                )
                print(f"📡 Respuesta del Gateway: {res.status_code}")
                print(f"📡 Cuerpo: {res.text}")
            except Exception as e:
                print(f"❌ Error al conectar al puerto 3001: {e}")
