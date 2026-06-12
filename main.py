import os, struct, math, tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/health')
def health():
    occ_ok = False
    ver = None
    try:
        import ifcopenshell
        occ_ok = True
        ver = ifcopenshell.version
    except:
        pass
    return jsonify({'status': 'ok', 'occ': occ_ok, 'version': ver or '1.0'})

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    ext = f.filename.rsplit('.', 1)[-1].lower()
    data = f.read()
    if ext == 'stl':
        return jsonify(parse_stl(data))
    elif ext in ('step', 'stp'):
        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as tmp:
            tmp.write(data); tmp_path = tmp.name
        try:
            return jsonify(parse_step_ifc(tmp_path))
        finally:
            os.unlink(tmp_path)
    return jsonify({'error': 'Format nesuportat'}), 501

def parse_step_ifc(filepath):
    import ifcopenshell
    import ifcopenshell.geom
    ifc = ifcopenshell.open(filepath)
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    faces_data = []
    for product in ifc.by_type('IfcProduct'):
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            verts = list(shape.geometry.verts)
            faces = list(
