-- Esquema para el portal de postulaciones
-- Ejecutar: mysql -u tu_usuario -p tu_basededatos < schema.sql

CREATE TABLE IF NOT EXISTS vacantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa VARCHAR(255) NOT NULL,
    cargo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    email_contacto VARCHAR(255),
    url VARCHAR(500),
    fuente VARCHAR(100) DEFAULT 'manual',        -- manual, api, scraping
    match_pct FLOAT DEFAULT NULL,                -- % de coincidencia calculado
    palabras_clave TEXT,                         -- keywords detectadas, separadas por coma
    estado ENUM(
        'pendiente',        -- recién agregada, falta calcular match / generar CV
        'cv_generado',      -- CV listo, esperando que el script local la envíe
        'enviada',          -- correo ya enviado
        'respondida',       -- la empresa respondió algo
        'entrevista',       -- pasó a entrevista
        'rechazada',        -- te descartaron
        'descartada'        -- tú decidiste no aplicar (ej. match muy bajo)
    ) DEFAULT 'pendiente',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_envio DATETIME DEFAULT NULL,
    notas TEXT,
    perfil_editado TEXT DEFAULT NULL,    -- si el usuario edita el perfil a mano, se guarda aquí
    habilidades_orden TEXT DEFAULT NULL, -- orden final de habilidades, separadas por coma, tras editar
    cc_contacto VARCHAR(255) DEFAULT NULL -- copia (CC) específica para esta vacante, si aplica
);

-- Plantilla de correo editable, usada para TODOS los envíos masivos.
-- Placeholders disponibles en asunto_tpl / cuerpo_tpl: {cargo}, {empresa}
CREATE TABLE IF NOT EXISTS plantilla_correo (
    id INT PRIMARY KEY DEFAULT 1,
    asunto_tpl VARCHAR(255) NOT NULL,
    cuerpo_tpl TEXT NOT NULL,
    cc_default VARCHAR(255) DEFAULT NULL,
    CONSTRAINT unica_fila CHECK (id = 1)
);

INSERT IGNORE INTO plantilla_correo (id, asunto_tpl, cuerpo_tpl, cc_default) VALUES (
    1,
    'Postulación - {cargo}',
    'Estimados,\n\nAdjunto mi hoja de vida para el cargo de {cargo} en {empresa}. Quedo atento a cualquier información adicional que necesiten.\n\nSaludos cordiales,\nAlex Santiago Vela Tirado',
    NULL
);

CREATE TABLE IF NOT EXISTS habilidades_usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    habilidad VARCHAR(100) NOT NULL UNIQUE
);

-- Precarga con las habilidades que ya declaraste en tu CV.
-- Agrega/quita según necesites: estas son las que el sistema busca en cada vacante.
INSERT IGNORE INTO habilidades_usuario (habilidad) VALUES
('python'), ('sql server'), ('mysql'), ('microsoft access'),
('c#'), ('.net'), ('javascript'), ('azure'), ('git'),
('numpy'), ('excel avanzado'), ('power bi'), ('scrum'),
('testing'), ('optimización de bd'), ('automatización de procesos'),
('inglés');
