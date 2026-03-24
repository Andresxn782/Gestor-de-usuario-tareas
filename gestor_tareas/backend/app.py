from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# -------------------------
# TRADUCCIONES COMPLETAS
# -------------------------

def textos():

    idioma = session.get("idioma", "es")

    traducciones = {

        "es": {
            "bienvenido": "Bienvenido",
            "mis_tareas": "Mis Tareas",
            "cerrar_sesion": "Cerrar sesión",
            "tareas": "Tareas",
            "descripcion": "Descripción",
            "estado": "Estado",
            "trabajadores": "Trabajadores",
            "pendiente": "Pendiente",
            "en_proceso": "En proceso",
            "finalizada": "Finalizada",
            "crear_tarea": "Crear tarea",
            "tarea_grupal": "Tarea grupal",
            "login": "Iniciar sesión",
            "email": "Correo electrónico",
            "password": "Contraseña",
            "no_cuenta": "¿No tienes cuenta?",
            "registrarse": "Regístrate aquí",
            "panel_admin": "Panel Administrador",
            "bienvenido": "Bienvenido",
            "usuarios": "Usuarios",
            "tareas": "Tareas",
            "cerrar_sesion": "Cerrar sesión",
            "lista_trabajadores": "Lista de trabajadores",
            "nombre": "Nombre",
            "email": "Email",
            "rol": "Rol",
            "panel_trabajador": "Panel Trabajador",
            "mis_tareas": "Mis Tareas",
            "tarea": "Tarea",
            "estado": "Estado",
            "pendiente": "Pendiente",
            "en_proceso": "En proceso",
            "finalizada": "Finalizada",
            "registro": "Registro",
            "nombre_completo": "Nombre completo",
            "trabajador": "Trabajador",
            "administrador": "Administrador",
            "ya_cuenta": "¿Ya tienes cuenta?",
            "crear_tarea": "Crear tarea",
            "volver": "Volver",

        },

        "en": {
            "bienvenido": "Welcome",
            "mis_tareas": "My Tasks",
            "cerrar_sesion": "Logout",
            "tareas": "Tasks",
            "descripcion": "Description",
            "estado": "Status",
            "trabajadores": "Workers",
            "pendiente": "Pending",
            "en_proceso": "In Progress",
            "finalizada": "Completed",
            "crear_tarea": "Create Task",
            "tarea_grupal": "Group Task",
            "login": "Login",
            "email": "Email",
            "password": "Password",
            "no_cuenta": "Don't have an account?",
            "registrarse": "Sign up here",
            "panel_admin": "Admin Panel",
            "bienvenido": "Welcome",
            "usuarios": "Users",
            "tareas": "Tasks",
            "cerrar_sesion": "Logout",
            "lista_trabajadores": "Workers List",
            "nombre": "Name",
            "email": "Email",
            "rol": "Role",
            "panel_trabajador": "Worker Panel",
            "mis_tareas": "My Tasks",
            "tarea": "Task",
            "estado": "Status",
            "pendiente": "Pending",
            "en_proceso": "In Progress",
            "finalizada": "Completed",
            "registro": "Register",
            "nombre_completo": "Full name",
            "trabajador": "Worker",
            "administrador": "Administrator",
            "ya_cuenta": "Already have an account?",
            "crear_tarea": "Create task",
            "volver": "Back",
        }

    }

    return traducciones.get(idioma, traducciones["es"])


# hacer disponible en HTML
app.jinja_env.globals.update(textos=textos)


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

    # TAREAS
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

    # ESTADÍSTICAS
    cursor.execute("SELECT COUNT(*) AS total FROM tareas WHERE estado='pendiente'")
    pendientes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM tareas WHERE estado='en_proceso'")
    en_proceso = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM tareas WHERE estado='finalizada'")
    finalizadas = cursor.fetchone()["total"]

    cursor.close()
    conexion.close()

    return render_template(
        "admin_tareas.html",
        tareas=tareas,
        pendientes=pendientes,
        en_proceso=en_proceso,
        finalizadas=finalizadas
    )
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


# -------------------------
# CAMBIAR IDIOMA
# -------------------------

@app.route("/cambiar_idioma/<idioma>")
def cambiar_idioma(idioma):

    session["idioma"] = idioma

    return redirect(request.referrer or "/")

if __name__ == "__main__":
    app.run(debug=True)
