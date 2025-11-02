from pymongo import MongoClient
from dotenv import load_dotenv, dotenv_values

load_dotenv()
config = dotenv_values(".env")

MONGO_URI = config.get("MONGO_URI")
DB_NAME = config.get("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_orders_collection():
    return db[config.get("COLLECTION_NAME")]