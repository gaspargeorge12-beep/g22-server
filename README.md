# G22 Manufacturing — Server STEP

## Deploy pe Railway

1. Mergi la https://railway.app și loghează-te cu GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Upload sau conectează folderul `g22-server`
4. Railway detectează automat Python și instalează dependențele
5. Copiază URL-ul generat (ex: `https://g22-server.up.railway.app`)
6. Pune URL-ul în G22_Manufacturing.html (vezi instrucțiunile din app)

## Test local
```bash
pip install flask flask-cors pythonocc-core
python main.py
```
