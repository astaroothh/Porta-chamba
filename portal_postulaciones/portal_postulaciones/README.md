# Portal de Postulaciones

## 1. Base de datos (en el VPS)
```bash
mysql -u root -p -e "CREATE DATABASE postulaciones CHARACTER SET utf8mb4"
mysql -u root -p postulaciones < backend/schema.sql
```
Revisa `backend/schema.sql`: ya viene precargada con las habilidades de tu CV.
Ajusta esa lista si aprendes algo nuevo o quieres afinar el % de match.

## 2. Backend (en el VPS)
Instala LibreOffice (se usa para exportar el CV editado a PDF):
```bash
sudo apt update && sudo apt install -y libreoffice --no-install-recommends
```
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DB_HOST=localhost DB_USER=root DB_PASS=tu_password DB_NAME=postulaciones
export API_TOKEN=$(python -c "import secrets; print(secrets.token_hex(32))")
echo "Guarda este token, lo necesitas también en tu PC: $API_TOKEN"

uvicorn main:app --host 0.0.0.0 --port 8000
```
Para producción real, corre esto detrás de Nginx con HTTPS (certbot) y
como servicio con systemd o `pm2`/`supervisor`, no dejando la terminal abierta.

Entra a `http://tu-ip:8000` (o tu dominio) y verás el dashboard. Ahí puedes
agregar vacantes manualmente, o apuntar tu scraper/consumidor de APIs a
`POST /api/vacantes` con el mismo formato JSON.

## 3. Script local — el que realmente envía los correos (en tu PC)
```bash
cd local_sender
pip install -r requirements.txt

export PORTAL_URL="https://tu-dominio-o-ip:8000"
export API_TOKEN="el_token_que_generaste_arriba"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="tucorreo@gmail.com"
export SMTP_PASS="tu_contraseña_de_aplicacion"

python send_pending.py
```
Puedes programarlo con el Programador de tareas (Windows) o cron/launchd
para que corra, por ejemplo, cada hora — así el envío queda repartido en
el día en vez de mandar 200 de una sola vez.

## Despliegue rápido para pruebas (Railway o Render)
Ambos te dan un subdominio público gratis sin necesidad de comprar dominio:
1. Sube esta carpeta a un repo de GitHub.
2. En Railway/Render: "New Project" → conecta el repo → selecciona la carpeta `backend`.
3. Agrega un servicio de MySQL desde el mismo panel (ambos lo ofrecen integrado)
   y copia sus credenciales a las variables de entorno `DB_HOST`, `DB_USER`, etc.
4. Define `API_TOKEN` como variable de entorno secreta.
5. Comando de arranque: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Te dan una URL pública (`tu-app.up.railway.app`) — esa es la que compartes para que la revise.

## Notas importantes
- **Scraping de portales de empleo**: LinkedIn, Computrabajo y similares
  suelen prohibirlo en sus términos de uso y pueden bloquear tu cuenta.
  Prioriza APIs oficiales o carga manual/semi-manual vía el formulario.
- **Volumen de correos**: para ~200/día, considera un servicio como Brevo,
  SendGrid o Amazon SES en vez de Gmail personal — mucho menos riesgo de
  que te bloqueen la cuenta a mitad de campaña.
- **El % de match es una guía, no una garantía**: mide coincidencia de
  palabras clave (que es justo lo que revisan los ATS), no si eres o no
  buen candidato.
