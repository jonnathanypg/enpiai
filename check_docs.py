import sys
import os
sys.path.append(os.path.abspath('backend'))
from app import create_app
from extensions import db
from models.document import Document

app = create_app()
with app.app_context():
    docs = Document.query.all()
    print("Documents in DB:")
    for d in docs:
        print(f"ID: {d.id}, Filename: {d.filename}, Processed: {d.is_processed}, Distributor: {d.distributor_id}")
