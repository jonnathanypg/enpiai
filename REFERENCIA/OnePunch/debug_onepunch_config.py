
import os
import sys
from dotenv import load_dotenv

# Force load .env from current directory
load_dotenv()

from config import Config

print("\n🔍 OnePunch Configuration Debug")
print("-------------------------------")
print(f"MYSQL_HOST: '{os.getenv('MYSQL_HOST')}'")
print(f"MYSQL_USER: '{os.getenv('MYSQL_USER')}'")
print("\nResolved SQLALCHEMY_DATABASE_URI:")
print(Config.SQLALCHEMY_DATABASE_URI)
print("\n-------------------------------")

if 'sqlite' in Config.SQLALCHEMY_DATABASE_URI:
    print("📢 CONCLUSION: OnePunch is using SQLITE (Local DB).")
    print("   The MySQL variables might be set, but the code chose SQLite.")
else:
    print("📢 CONCLUSION: OnePunch is configured for MySQL.")
