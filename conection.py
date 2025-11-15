import psycopg2
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

load_dotenv()

def obtener_conexion():

    host = os.getenv("SUPABASE_HOST")
    dbname = os.getenv("SUPABASE_DBNAME")
    user = os.getenv("SUPABASE_USER")
    password = os.getenv("SUPABASE_PASSWORD")
    port = os.getenv("SUPABASE_PORT")

    if password is None:
        raise ValueError("❌ La variable SUPABASE_PASSWORD no está definida en .env")
    
    encoded_password = quote_plus(password)

    DATABASE_URL = f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}"

    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Conectado a Supabase desde Python")
        return conn
        #conn.close()
        #print("Conexión cerrado")

    except Exception as e:
        print("Error:", e)
        return None
    

 # Ejecutar la función
if __name__ == "__main__":
    conexion = obtener_conexion()
    if conexion:
        conexion.close()
        print("🔌 Conexión cerrada correctamente.")