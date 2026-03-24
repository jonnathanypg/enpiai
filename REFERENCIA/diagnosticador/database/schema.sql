CREATE DATABASE IF NOT EXISTS u854386804_encuesta_salud;
USE u854386804_encuesta_salud;

CREATE TABLE IF NOT EXISTS usuarios (
  usuario_id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellido VARCHAR(100) NOT NULL,
  identificacion VARCHAR(50) NOT NULL UNIQUE,
  telefono VARCHAR(50) NOT NULL,
  correo VARCHAR(100) NOT NULL UNIQUE,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS encuestas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  nombre_encuestado VARCHAR(200) NOT NULL,
  telefono VARCHAR(50) NOT NULL,
  correo VARCHAR(100) NOT NULL,
  edad INT NOT NULL,
  peso FLOAT NOT NULL,
  estatura FLOAT NOT NULL,
  presion_arterial VARCHAR(20) NOT NULL,
  nivel_energia INT NOT NULL DEFAULT 5,
  sintomas TEXT NOT NULL,
  observaciones TEXT,
  nombre_encuestador VARCHAR(200),
  encuestador_id INT,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
);

CREATE TABLE IF NOT EXISTS diagnosticos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  encuesta_id INT NOT NULL,
  diagnostico TEXT NOT NULL,
  recomendaciones TEXT,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
  FOREIGN KEY (encuesta_id) REFERENCES encuestas(id)
);
