CREATE DATABASE gestor_tareas;



-- =======================================
-- TABLA: usuarios
-- Guarda datos de los usuarios
-- Ahora incluye el rol (administrador o trabajador)
-- =======================================
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT,           -- Identificador único del usuario
    nombre VARCHAR(100) NOT NULL,            -- Nombre del usuario
    email VARCHAR(100) NOT NULL,             -- Email del usuario
    rol ENUM('administrador','trabajador') NOT NULL DEFAULT 'trabajador',
                                             -- Rol del usuario, por defecto 'trabajador'
    PRIMARY KEY (id_usuario),                -- Clave primaria
    UNIQUE (email)                           -- Evita emails duplicados
);

-- =======================================
-- INSERTAR USUARIOS DE PRUEBA
-- =======================================
INSERT INTO usuarios (nombre, email, rol) VALUES
('Ana Pérez', 'ana.perez@email.com', 'administrador'),  -- Ana es administradora
('Luis Gómez', 'luis.gomez@email.com', 'trabajador'),   -- Luis es trabajador
('María López', 'maria.lopez@email.com', 'trabajador'); -- María es trabajadora


-- =======================================
-- TABLA: tareas
-- Guarda la información de las tareas
-- =======================================
CREATE TABLE tareas (
    id_tarea INT AUTO_INCREMENT,                     -- Identificador único de la tarea
    nombre VARCHAR(100) NOT NULL,                    -- Nombre o título de la tarea
    descripcion TEXT,                                -- Descripción de la tarea
    estado ENUM('pendiente','en_proceso','finalizada') DEFAULT 'pendiente',
                                                     -- Estado de la tarea, valor por defecto 'pendiente'
    PRIMARY KEY (id_tarea)                           -- Clave primaria de la tabla
);

-- =======================================
-- TABLA: usuario_tarea
-- Relaciona usuarios con tareas (muchos a muchos)
-- =======================================
CREATE TABLE usuario_tarea (
    id_usuario INT,          -- FK: referencia a usuarios
    id_tarea INT,            -- FK: referencia a tareas
    PRIMARY KEY (id_usuario, id_tarea),   -- PK compuesta para evitar duplicados
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),   -- Relación con tabla usuarios
    FOREIGN KEY (id_tarea) REFERENCES tareas(id_tarea)          -- Relación con tabla tareas
);


-- Creamos usuario y le otorgamos privilegios
CREATE USER 'gestor_user'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON gestortareas.* TO 'gestor_user'@'localhost';
FLUSH PRIVILEGES;

