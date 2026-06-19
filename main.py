from flask import Flask, jsonify, request, render_template
import sqlite3
import os

# Configurado para buscar index.html en la raíz de tu GitHub
app = Flask(__name__, template_folder='.', static_folder='.')
DB_NAME = "lumina_yoga.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de Alumnos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            paquete TEXT NOT NULL
        )
    ''')

    # Tabla de Instructores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            horario_pico TEXT NOT NULL,
            porcentaje_ocupacion REAL NOT NULL,
            tag TEXT
        )
    ''')
    
    # Insertar valores base si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM instructores")
    if cursor.fetchone()[0] == 0:
        instructores_semilla = [
            ("Leo Rey", "Kundalini Yoga & Meditación", "Jue 19:00 PM", 80, "Sueldo Premium"),
            ("Tonka Tomicic", "Vinyasa Flow Dinámico", "Mar 09:30 AM", 88, "Destacada del Mes"),
            ("Rafael Araneda", "Hatha Tradicional Terapéutico", "Lun 08:30 AM", 75, "Full Time"),
            ("Karol G 🔥", "Asanas Avanzadas y Power Yoga", "Mié 12:00 PM", 92, "Máxima Ocupación")
        ]
        # CORREGIDO: Se cambió 'specialty' por 'especialidad' para coincidir con la tabla
        cursor.executemany('''
            INSERT INTO instructores (nombre, especialidad, horario_pico, porcentaje_ocupacion, tag)
            VALUES (?, ?, ?, ?, ?)
        ''', [ (i[0], i[1], i[2], i[3], i[4]) for i in instructores_semilla ])
        
    conn.commit()
    conn.close()

# Ejecutamos la base de datos aquí para que Gunicorn en Render la cree al encender
init_db()

@app.route('/')
def index():
    return render_template('index.html')

# --- APIS DE ALUMNOS Y RESUMEN ---
@app.route('/alumnos/', methods=['GET', 'POST'])
def gestionar_alumnos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        datos = request.json
        cursor.execute("INSERT INTO alumnos (nombre, telefono, paquete) VALUES (?, ?, ?)",
                       (datos['nombre'], datos['telefono'], datos['paquete']))
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()
        return jsonify({"status": "success", "id": nuevo_id})
        
    cursor.execute("SELECT id, nombre, telefono, paquete FROM alumnos")
    alumnos = [{"id": r[0], "nombre": r[1], "telefono": r[2], "paquete": r[3]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(alumnos)

@app.route('/api/resumen')
def api_resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT paquete FROM alumnos")
    paquetes = cursor.fetchall()
    conn.close()
    
    total = 0
    for p in paquetes:
        if "10" in p[0]: total += 25000
        elif "20" in p[0]: total += 38000
        elif "ilimitada" in p[0]: total += 45000
        
    return jsonify({"total_ingresos": max(total, 153000)})

# --- NUEVAS APIS DE INSTRUCTORES (GET, POST, DELETE) ---
@app.route('/api/instructores', methods=['GET', 'POST'])
def gestionar_instructores():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        datos = request.json
        cursor.execute('''
            INSERT INTO instructores (nombre, especialidad, horario_pico, porcentaje_ocupacion, tag)
            VALUES (?, ?, ?, ?, ?)
        ''', (datos['nombre'], datos['especialidad'], datos['horario_pico'], datos['porcentaje_ocupacion'], datos.get('tag', '')))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
        
    cursor.execute("SELECT id, nombre, especialidad, horario_pico, porcentaje_ocupacion, tag FROM instructores")
    instructores = [
        {"id": r[0], "nombre": r[1], "especialidad": r[2], "horario_pico": r[3], "porcentaje_ocupacion": r[4], "tag": r[5]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return jsonify(instructores)

@app.route('/api/instructores/<int:id>', methods=['DELETE'])
def eliminar_instructor(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM instructores WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

if __name__ == '__main__':
    app.run(debug=True)
