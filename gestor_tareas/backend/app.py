# Importaciones necesarias para Flask y manejo de base de datos
from flask import Flask, render_template, request, redirect, session
import mysql.connector  # Para conectarse a MySQL
from werkzeug.security import generate_password_hash, check_password_hash  # Para hashear y verificar contraseñas

# Crear la aplicación Flask
app = Flask(__name__)
# Clave secreta usada para sesiones seguras
app.secret_key = "clave_super_secreta"

# -------------------------
# TRADUCCIONES COMPLETAS
# -------------------------

# Función para manejar traducciones de la interfaz
def textos():
    # Obtener idioma de la sesión, por defecto español
    idioma = session.get("idioma", "es")

    # Diccionario con traducciones en español e inglés
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
            "usuarios": "Usuarios",
            "lista_trabajadores": "Lista de trabajadores",
            "nombre": "Nombre",
            "rol": "Rol",
            "panel_trabajador": "Panel Trabajador",
            "tarea": "Tarea",
            "registro": "Registro",
            "nombre_completo": "Nombre completo",
            "trabajador": "Trabajador",
            "administrador": "Administrador",
            "ya_cuenta": "¿Ya tienes cuenta?",
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
            "usuarios": "Users",
            "lista_trabajadores": "Workers List",
            "nombre": "Name",
            "rol": "Role",
            "panel_trabajador": "Worker Panel",
            "tarea": "Task",
            "registro": "Register",
            "nombre_completo": "Full name",
            "trabajador": "Worker",
            "administrador": "Administrator",
            "ya_cuenta": "Already have an account?",
            "volver": "Back",
        }
    }

    # Devolver traducciones del idioma elegido, por defecto español
    return traducciones.get(idioma, traducciones["es"])

# Hacer la función de traducciones disponible en los templates HTML
app.jinja_env.globals.update(textos=textos)

# -------------------------
# CONEXIÓN BD
# -------------------------

# Función para obtener la conexión a la base de datos
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
    # Si se envía el formulario
    if request.method == "POST":
        email = request.form["email"]  # Obtener email del formulario
        password = request.form["password"]  # Obtener contraseña del formulario

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        # Buscar usuario por email
        cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        usuario = cursor.fetchone()

        cursor.close()
        conexion.close()

        # Verificar que el usuario exista y la contraseña coincida
        if usuario and check_password_hash(usuario["password"], password):
            # Guardar información del usuario en sesión
            session["usuario_id"] = usuario["id_usuario"]
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["nombre"]

            # Redirigir al panel correspondiente
            return redirect("/panel")

    # Si es GET o login fallido, mostrar el formulario
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

        # VALIDACIÓN NOMBRE
        if len(nombre) < 5 or len(nombre) > 20:
            return render_template("register.html",
                                   message="El nombre debe tener entre 5 y 20 caracteres",
                                   error=True)

        # VALIDACIÓN PASSWORD
        if len(password) < 8 or len(password) > 16:
            return render_template("register.html",
                                   message="La contraseña debe tener entre 8 y 16 caracteres",
                                   error=True)

        # 🔥 ESTO VA FUERA DE LOS IF
        password_hash = generate_password_hash(password)

        conexion = get_db_connection()
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO usuarios (nombre,email,password,rol)
        VALUES (%s,%s,%s,%s)
        """, (nombre, email, password_hash, rol))

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
    # Si no hay usuario logueado, redirigir al login
    if "usuario_id" not in session:
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # Panel de administrador
    if session["rol"] == "administrador":
        # Obtener lista de trabajadores
        cursor.execute("SELECT id_usuario,nombre,email,rol FROM usuarios WHERE rol='trabajador'")
        usuarios = cursor.fetchall()
        cursor.close()
        conexion.close()

        # Renderizar panel admin
        return render_template("panel_admin.html",
                               usuarios=usuarios,
                               nombre=session["nombre"])
    else:
        # Panel de trabajador: obtener sus tareas
        cursor.execute("""
        SELECT t.id_tarea,t.nombre,t.descripcion,t.estado
        FROM tareas t
        JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
        WHERE ut.id_usuario = %s
        """, (session["usuario_id"],))

        tareas = cursor.fetchall()
        cursor.close()
        conexion.close()

        # Renderizar panel trabajador
        return render_template("panel_trabajador.html",
                               tareas=tareas,
                               nombre=session["nombre"])

# -------------------------
# PANEL TAREAS ADMIN
# -------------------------

@app.route("/admin/tareas")
def admin_tareas():
    # Solo admin puede acceder
    if session.get("rol") != "administrador":
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # Obtener todas las tareas con los trabajadores asignados
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

    # Obtener estadísticas de estado de tareas
    cursor.execute("SELECT COUNT(*) AS total FROM tareas WHERE estado='pendiente'")
    pendientes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM tareas WHERE estado='en_proceso'")
    en_proceso = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM tareas WHERE estado='finalizada'")
    finalizadas = cursor.fetchone()["total"]

    cursor.close()
    conexion.close()

    # Renderizar vista de tareas admin
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

        # Comprobar si el trabajador tiene una tarea activa
        cursor.execute("""
        SELECT *
        FROM tareas t
        JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
        WHERE ut.id_usuario=%s
        AND t.estado!='finalizada'
        """, (usuario_id,))

        tarea_activa = cursor.fetchone()

        if tarea_activa:
            return "El trabajador ya tiene una tarea activa"

        # Crear tarea nueva
        cursor.execute("""
        INSERT INTO tareas (nombre,descripcion,estado)
        VALUES (%s,%s,'pendiente')
        """, (nombre, descripcion))

        conexion.commit()
        id_tarea = cursor.lastrowid

        # Asignar tarea al trabajador
        cursor.execute("""
        INSERT INTO usuario_tarea (id_usuario,id_tarea)
        VALUES (%s,%s)
        """, (usuario_id, id_tarea))

        conexion.commit()
        return redirect("/admin/tareas")

    # Obtener lista de trabajadores para el formulario
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
        usuarios = request.form.getlist("usuarios")  # Obtener lista de ids

        if not usuarios:
            return "Debes seleccionar al menos un trabajador"

        # Comprobar si algún trabajador tiene tarea activa
        for usuario_id in usuarios:
            cursor.execute("""
            SELECT *
            FROM tareas t
            JOIN usuario_tarea ut ON t.id_tarea = ut.id_tarea
            WHERE ut.id_usuario=%s
            AND t.estado!='finalizada'
            """, (usuario_id,))

            if cursor.fetchone():
                return "Uno de los trabajadores ya tiene una tarea activa"

        # Crear tarea grupal
        cursor.execute("""
        INSERT INTO tareas (nombre,descripcion,estado)
        VALUES (%s,%s,'pendiente')
        """, (nombre, descripcion))

        conexion.commit()
        id_tarea = cursor.lastrowid

        # Asignar tarea a todos los trabajadores seleccionados
        for usuario_id in usuarios:
            cursor.execute("""
            INSERT INTO usuario_tarea (id_usuario,id_tarea)
            VALUES (%s,%s)
            """, (usuario_id, id_tarea))

        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect("/admin/tareas")

    # Obtener lista de trabajadores
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

    # Actualizar estado de tarea
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
    # Limpiar sesión
    session.clear()
    return redirect("/")

# -------------------------
# CAMBIAR IDIOMA
# -------------------------

@app.route("/cambiar_idioma/<idioma>")
def cambiar_idioma(idioma):
    # Guardar idioma en sesión
    session["idioma"] = idioma
    # Redirigir a la página anterior
    return redirect(request.referrer or "/")

# Ejecutar la app
if __name__ == "__main__":
    app.run(debug=True)
