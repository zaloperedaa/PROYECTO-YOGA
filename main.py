from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import os
from datetime import datetime

app = FastAPI()

# Middleware para permitir conexión desde el frontend
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DB_PATH = "proyecto.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS alumnos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, clases_disponibles INTEGER, paquete TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pagos (id INTEGER PRIMARY KEY AUTOINCREMENT, alumno_id INTEGER, monto REAL, fecha TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clases_programadas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_clase TEXT, horario TEXT, duracion TEXT, cupos_totales INTEGER, cupos_disponibles INTEGER, instructor TEXT, descripcion_instructor TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM clases_programadas")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO clases_programadas (nombre_clase, horario, duracion, cupos_totales, cupos_disponibles, instructor, descripcion_instructor) VALUES (?, ?, ?, ?, ?, ?, ?)', [
            ("Yoga Vinyasa", "18:00", "1 hora", 15, 15, "Leo Rey", "Experto en fluidez y control respiratorio."),
            ("Hatha Yoga", "19:30", "1.5 horas", 12, 12, "Tonka Tomicic", "Enfoque en relajación profunda y estiramientos."),
            ("Meditación", "09:00", "1 hora", 20, 20, "Rafael Araneda", "Especialista en mindfulness y reducción de estrés."),
            ("Power Yoga", "10:30", "1 hora", 18, 18, "Karol G", "Yoga dinámico con mucha energía y fuerza física.")
        ])
    conn.commit()
    conn.close()

init_db()

# --- SERVIR FRONTEND ---
@app.get("/")
def read_root():
    # Si tu archivo está en la raíz, usa 'index.html'. Si está en carpeta, 'FRONTEND/index.html'
    return FileResponse('index.html') 

app.mount("/static", StaticFiles(directory="."), name="static")

# --- MÉTODOS API ---

@app.get("/valentina/ingreso-promedio")
def obtener_ingreso_promedio():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(monto), COUNT(DISTINCT alumno_id) FROM pagos")
    res = cursor.fetchone()
    total_ingresos = res[0] or 0.0
    total_alumnos = res[1] if res[1] and res[1] > 0 else 1
    conn.close()
    return {"ingreso_promedio": round(total_ingresos / total_alumnos, 2)}

@app.get("/valentina/metricas")
def obtener_metricas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alumnos WHERE clases_disponibles > 0")
    activos = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(monto) FROM pagos")
    ingresos = cursor.fetchone()[0] or 0.0
    conn.close()
    return {"alumnos_activos": activos, "ingresos_totales": ingresos}

@app.post("/alumnos/")
def registrar_alumno(data: dict = Body(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    paquete = data.get("paquete", "10 clases")
    precios = {"10 clases": 25000.0, "20 clases": 38000.0, "mensualidad ilimitada": 45000.0}
    monto = precios.get(paquete, 3500.0)
    
    cursor.execute("INSERT INTO alumnos (nombre, telefono, clases_disponibles, paquete) VALUES (?, ?, ?, ?)", 
                   (data.get("nombre"), data.get("telefono"), 10, paquete))
    alumno_id = cursor.lastrowid
    cursor.execute("INSERT INTO pagos (alumno_id, monto, fecha) VALUES (?, ?, ?)", (alumno_id, monto, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return {"status": "success", "id": alumno_id}

@app.get("/alumnos/")
def obtener_alumnos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, telefono, clases_disponibles, paquete FROM alumnos")
    res = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "telefono": f[2], "clases": f[3], "paquete": f[4]} for f in res]

@app.get("/clases/")
def obtener_clases():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_clase, horario, duracion, cupos_disponibles, instructor, descripcion_instructor FROM clases_programadas")
    res = cursor.fetchall()
    conn.close()
    return [{"id": x[0], "nombre_clase": x[1], "horario": x[2], "duracion": x[3], "cupos": x[4], "instructor": x[5], "descripcion": x[6]} for x in res]

@app.post("/asistencia/{alumno_id}")
def registrar_asistencia(alumno_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE alumnos SET clases_disponibles = clases_disponibles - 1 WHERE id = ? AND clases_disponibles > 0", (alumno_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}