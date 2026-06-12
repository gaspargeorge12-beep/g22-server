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
    except Exception:
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
            tmp.write(data)
            tmp_path = tmp.name
        try:
            return jsonify(parse_step_ifc(tmp_path))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
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
            faces = list(shape.geometry.faces)
            if not verts or not faces:
                continue
            tri_verts = []
            for i in range(0, len(faces), 3):
                for j in range(3):
                    idx = faces[i + j] * 3
                    tri_verts.extend(verts[idx:idx + 3])
            faces_data.append({
                'faceIdx': len(faces_data),
                'vertices': tri_verts,
                'normals': tri_verts,
                'area': 0,
                'nTriangles': len(faces) // 3
            })
        except Exception:
            continue
    if not faces_data:
        raise ValueError('Nicio geometrie gasita in fisierul STEP')
    return {'faces': faces_data, 'source': 'ifcopenshell', 'faceCount': len(faces_data)}

def parse_stl(data):
    if len(data) < 84:
        return {'faces': [], 'source': 'stl'}
    n = struct.unpack_from('<I', data, 80)[0]
    verts, norms = [], []
    o = 84
    for _ in range(n):
        nx, ny, nz = struct.unpack_from('<fff', data, o)
        o += 12
        for _ in range(3):
            x, y, z = struct.unpack_from('<fff', data, o)
            o += 12
            verts.extend([x, y, z])
            norms.extend([nx, ny, nz])
        o += 2
    return {
        'faces': [{'faceIdx': 0, 'vertices': verts, 'normals': norms, 'area': 0, 'nTriangles': n}],
        'source': 'stl'
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
