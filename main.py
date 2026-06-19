from flask import Flask, jsonify, request, render_template
import sqlite3
import os

app = Flask(__name__, template_folder='.', static_folder='.')
DB_NAME = "lumina_yoga.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabla de Alumnos (Con columna 'clases' para gestionar sus créditos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            paquete TEXT NOT NULL,
            clases INTEGER DEFAULT 8
        )
    ''')
    
    # Migración: Si la tabla ya existía sin la columna 'clases', la agregamos dinámicamente
    try:
        cursor.execute("ALTER TABLE alumnos ADD COLUMN clases INTEGER DEFAULT 8")
    except sqlite3.OperationalError:
        pass 

    # 2. Tabla de Instructores
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

    # 3. Tabla de Clases (Espejo de lo que consume tu HTML del Alumno)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_clase TEXT NOT NULL,
            horario TEXT NOT NULL,
            instructor TEXT NOT NULL,
            cupos INTEGER DEFAULT 15
        )
    ''')
    
    # Insertar instructores base si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM instructores")
    if cursor.fetchone()[0] == 0:
        instructores_semilla = [
            ("Leo Rey", "Kundalini Yoga & Meditación", "Jue 19:00 PM", 80, "Sueldo Premium"),
            ("Tonka Tomicic", "Vinyasa Flow Dinámico", "Mar 09:30 AM", 88, "Destacada del Mes"),
            ("Rafael Araneda", "Hatha Tradicional Terapéutico", "Lun 08:30 AM", 75, "Full Time"),
            ("Karol G 🔥", "Asanas Avanzadas y Power Yoga", "Mié 12:00 PM", 92, "Máxima Ocupación")
        ]
        cursor.executemany('''
            INSERT INTO instructores (nombre, especialidad, horario_pico, porcentaje_ocupacion, tag)
            VALUES (?, ?, ?, ?, ?)
        ''', instructores_semilla)

    # Insertar clases base si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM clases")
    if cursor.fetchone()[0] == 0:
        clases_semilla = [
            ("Kundalini Yoga", "19:00", "Leo Rey", 15),
            ("Vinyasa Flow", "09:30", "Tonka Tomicic", 12),
            ("Hatha Yoga", "08:30", "Rafael Araneda", 18),
            ("Ashtanga Yoga", "12:00", "Karol G 🔥", 10)
        ]
        cursor.executemany('''
            INSERT INTO clases (nombre_clase, horario, instructor, cupos)
            VALUES (?, ?, ?, ?)
        ''', clases_semilla)
        
    conn.commit()
    conn.close()

# Inicializar la base de datos automáticamente al arrancar
init_db()

# ==========================================
#          RUTAS DE NAVEGACIÓN VISTAS
# ==========================================

# 1. RUTA PANEL ADMINISTRADORA (index.html)
@app.route('/')
def index():
    return render_template('index.html')

# 2. RUTA PORTAL DEL ALUMNO (alumno.html)
# Nota: Asegúrate de que tu archivo HTML se llame exactamente 'alumno.html'
@app.route('/alumno')
@app.route('/alumno/')
def vista_alumno():
    return render_template('alumno.html')


# ==========================================
#          APIS Y ENDPOINTS (BACKEND)
# ==========================================

# API: Gestionar Alumnos
@app.route('/alumnos', methods=['GET', 'POST'])
@app.route('/alumnos/', methods=['GET', 'POST'])
@app.route('/api/alumnos', methods=['GET', 'POST'])
def gestionar_alumnos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        datos = request.json
        cursor.execute("INSERT INTO alumnos (nombre, telefono, paquete, clases) VALUES (?, ?, ?, 8)",
                       (datos['nombre'], datos['telefono'], datos['paquete']))
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()
        return jsonify({"status": "success", "id": nuevo_id})
        
    cursor.execute("SELECT id, nombre, telefono, paquete, clases FROM alumnos")
    alumnos = [{"id": r[0], "nombre": r[1], "telefono": r[2], "paquete": r[3], "clases": r[4]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(alumnos)

# API: Obtener Clases (Para el portal del alumno)
@app.route('/clases')
@app.route('/clases/')
def obtener_clases():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_clase, horario, instructor, cupos FROM clases")
    clases = [
        {"id": r[0], "nombre_clase": r[1], "horario": r[2], "instructor": r[3], "cupos": r[4]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return jsonify(clases)

# API: Descontar clase al presionar "RESERVAR"
@app.route('/asistencia/<int:alumno_id>', methods=['POST'])
def registrar_asistencia(alumno_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Resta 1 crédito al alumno sin dejar que baje de cero
    cursor.execute("UPDATE alumnos SET clases = MAX(0, clases - 1) WHERE id = ?", (alumno_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Clase reservada con éxito."})

# API: Calcular ingresos del panel administrativo
@app.route('/api/resumen')
def api_resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT paquete FROM alumnos")
    paquetes = cursor.fetchall()
    conn.close()
    
    total = 0
    for p in paquetes:
        if p[0]:
            paquete_texto = str(p[0]).lower()
            if "10" in paquete_texto: total += 25000
            elif "20" in paquete_texto: total += 38000
            elif "ilimitada" in paquete_texto or "ilimitado" in paquete_texto: total += 45000
        
    return jsonify({"total_ingresos": total})

# API: Gestionar Instructores
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

if __name__ == '__main__':
    app.run(debug=True)
