from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(title="Lumina Yoga API")

# Permitir la conexión con el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos para recibir peticiones
class Alumno(BaseModel):
    nombre: str
    telefono: str
    paquete: str

class Instructor(BaseModel):
    nombre: str
    especialidad: str
    horario_pico: str
    ocupacion: int

def conectar_db():
    # 🌟 CORRECCIÓN CRÍTICA DE RUTA (Evita el Exit Status 3) 🌟
    # Obtiene la ubicación exacta en tiempo real de este archivo main.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Apunta correctamente a la carpeta db saliendo un nivel hacia arriba de forma absoluta
    path_db = os.path.normpath(os.path.join(base_dir, "..", "db", "lumina_yoga.db"))
    
    # Si la carpeta /db no existe físicamente en tu PC, se crea automáticamente aquí
    os.makedirs(os.path.dirname(path_db), exist_ok=True)
    
    conn = sqlite3.connect(path_db)
    conn.row_factory = sqlite3.Row
    return conn

# Al iniciar, creamos las tablas si no existen por seguridad
@app.on_event("startup")
def crear_tablas_iniciales():
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            paquete TEXT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            horario_pico TEXT NOT NULL,
            ocupacion INTEGER NOT NULL
        );
        """)
        conn.commit()
        conn.close()
        print("🚀 Base de datos inicializada y conectada con éxito sin errores.")
    except Exception as e:
        print(f"❌ Error al intentar inicializar la base de datos: {e}")

# ================= ENDPOINTS DE ALUMNOS =================
@app.get("/alumnos/")
def obtener_alumnos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, telefono, paquete FROM alumnos")
    alumnos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alumnos

@app.post("/alumnos/")
def registrar_alumno(alumno: Alumno):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alumnos (nombre, telefono, paquete) VALUES (?, ?, ?)",
            (alumno.nombre, alumno.telefono, alumno.paquete)
        )
        conn.commit()
        id_generado = cursor.lastrowid
        conn.close()
        return {"status": "success", "id": id_generado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= ENDPOINTS DE INSTRUCTORES =================
@app.get("/instructores/")
def obtener_instructores():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, especialidad, horario_pico, ocupacion FROM instructores ORDER BY ocupacion DESC")
    instructores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return instructores

@app.post("/instructores/")
def registrar_instructor(instructor: Instructor):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO instructores (nombre, especialidad, horario_pico, ocupacion) VALUES (?, ?, ?, ?)",
            (instructor.nombre, instructor.especialidad, instructor.horario_pico, instructor.ocupacion)
        )
        conn.commit()
        id_generado = cursor.lastrowid
        conn.close()
        return {"status": "success", "id": id_generado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= ENDPOINT REPORTE FINANCIERO =================
@app.get("/api/resumen")
def obtener_resumen():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT paquete FROM alumnos")
    filas = cursor.fetchall()
    conn.close()
    
    precios = {
        "10 clases": 25000,
        "20 clases": 38000,
        "mensualidad ilimitada": 45000,
        "ninguno": 0
    }
    
    total = sum(precios.get(row["paquete"].lower(), 0) for row in filas)
    return {"total_ingresos": total}
