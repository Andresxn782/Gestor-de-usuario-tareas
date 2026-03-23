from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_secreta"


# -------------------------
# CONEXIÓN BD
# -------------------------

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="gestor_user",
        password="1234",
        database="gestor_tareas"
    )


# -------------------------
# LOGIN
# -------------------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM usuarios WHERE email=%s",(email,))
        usuario = cursor.fetchone()

        cursor.close()
        conexion.close()

        if usuario and check_password_hash(usuario["password"], password):

            session["usuario_id"] = usuario["id_usuario"]
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["nombre"]

            return redirect("/panel")

    return render_template("login.html")


# -------------------------
# REGISTRO
# -------------------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        rol = request.form["rol"]

        password_hash = generate_password_hash(password)

        conexion = get_db_connection()
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO usuarios (nombre,email,password,rol)
        VALUES (%s,%s,%s,%s)
        """,(nombre,email,password_hash,rol))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect("/")

    return render_template("register.html")


# -------------------------
# PANEL
# -------------------------

@app.route("/panel")
def panel():

    if "usuario_id" not in session:
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    if session["rol"] == "administrador":

        cursor.execute("SELECT id_usuario,nombre,email,rol FROM usuarios WHERE rol='trabajador'")
        usuarios = cursor.fetchall()

        cursor.close()
        conexion.close()

        return render_template("panel_admin.html",
                               usuarios=usuarios,
                               nombre=session["nombre"])

    else:

        cursor.execute("""
        SELECT t.id_tarea,t.nombre,t.descripcion,t.estado
        FROM tareas t
        JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
        WHERE ut.id_usuario = %s
        """,(session["usuario_id"],))

        tareas = cursor.fetchall()

        cursor.close()
        conexion.close()

        return render_template("panel_trabajador.html",
                               tareas=tareas,
                               nombre=session["nombre"])


# -------------------------
# PANEL TAREAS ADMIN
# -------------------------

@app.route("/admin/tareas")
def admin_tareas():

    if session.get("rol") != "administrador":
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
    SELECT 
        t.id_tarea, 
        t.nombre, 
        t.descripcion, 
        t.estado, 
        GROUP_CONCAT(u.nombre SEPARATOR ', ') AS trabajadores
    FROM tareas t
    JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
    JOIN usuarios u ON ut.id_usuario = u.id_usuario
    GROUP BY t.id_tarea
    """)

    tareas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("admin_tareas.html", tareas=tareas)
# -------------------------
# CREAR TAREA
# -------------------------

@app.route("/admin/crear_tarea", methods=["GET","POST"])
def crear_tarea():

    if session.get("rol") != "administrador":
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        usuario_id = request.form["usuario"]

        # comprobar tarea activa
        cursor.execute("""
        SELECT *
        FROM tareas t
        JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
        WHERE ut.id_usuario=%s
        AND t.estado!='finalizada'
        """,(usuario_id,))

        tarea_activa = cursor.fetchone()

        if tarea_activa:
            return "El trabajador ya tiene una tarea activa"

        cursor.execute("""
        INSERT INTO tareas (nombre,descripcion,estado)
        VALUES (%s,%s,'pendiente')
        """,(nombre,descripcion))

        conexion.commit()

        id_tarea = cursor.lastrowid

        cursor.execute("""
        INSERT INTO usuario_tarea (id_usuario,id_tarea)
        VALUES (%s,%s)
        """,(usuario_id,id_tarea))

        conexion.commit()

        return redirect("/admin/tareas")

    cursor.execute("SELECT id_usuario,nombre FROM usuarios WHERE rol='trabajador'")
    usuarios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("crear_tarea.html", usuarios=usuarios)

# -------------------------
# CREAR TAREA GRUPAL
# -------------------------

@app.route("/admin/crear_tarea_grupal", methods=["GET","POST"])
def crear_tarea_grupal():

    if session.get("rol") != "administrador":
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        usuarios = request.form.getlist("usuarios")

        if not usuarios:
            return "Debes seleccionar al menos un trabajador"

        # comprobar si alguno tiene tarea activa
        for usuario_id in usuarios:
            cursor.execute("""
            SELECT *
            FROM tareas t
            JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
            WHERE ut.id_usuario=%s
            AND t.estado!='finalizada'
            """,(usuario_id,))

            if cursor.fetchone():
                return "Uno de los trabajadores ya tiene una tarea activa"

        # crear tarea
        cursor.execute("""
        INSERT INTO tareas (nombre,descripcion,estado)
        VALUES (%s,%s,'pendiente')
        """,(nombre,descripcion))

        conexion.commit()

        id_tarea = cursor.lastrowid

        # asignar a todos
        for usuario_id in usuarios:
            cursor.execute("""
            INSERT INTO usuario_tarea (id_usuario,id_tarea)
            VALUES (%s,%s)
            """,(usuario_id,id_tarea))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect("/admin/tareas")

    cursor.execute("SELECT id_usuario,nombre FROM usuarios WHERE rol='trabajador'")
    usuarios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("crear_tarea_grupal.html", usuarios=usuarios)

# -------------------------
# ACTUALIZAR ESTADO TAREA
# -------------------------

@app.route("/actualizar_estado", methods=["POST"])
def actualizar_estado():

    if "usuario_id" not in session:
        return redirect("/")

    id_tarea = request.form["id_tarea"]
    nuevo_estado = request.form["estado"]

    conexion = get_db_connection()
    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE tareas
    SET estado = %s
    WHERE id_tarea = %s
    """, (nuevo_estado, id_tarea))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect("/panel")

# -------------------------
# LOGOUT
# -------------------------

@app.route("/logout")
def logout():

    session.clear()  # elimina la sesión

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)