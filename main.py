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
        import cadquery as cq
        from OCP.BRep import BRep_Tool
        occ_ok = True
        ver = cq.__version__
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
            return jsonify(parse_step(tmp_path))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    return jsonify({'error': 'Format nesuportat'}), 501

def parse_step(filepath):
    import cadquery as cq
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRep import BRep_Tool
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopoDS import TopoDS_Face

    result = cq.importers.importStep(filepath)
    shape = result.val().wrapped

    BRepMesh_IncrementalMesh(shape, 0.05, False, 0.3).Perform()

    faces_data = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    face_idx = 0

    while exp.More():
        face = TopoDS_Face()
        face.__init__(exp.Current())
        tri = BRep_Tool.Triangulation_s(face, face.Location())

        if tri is None or tri.NbNodes() == 0 or tri.NbTriangles() == 0:
            exp.Next()
            continue

        is_rev = face.Orientation() == TopAbs_REVERSED
        n_tris = tri.NbTriangles()
        vertices = []
        normals = []
        area = 0.0

        for i in range(1, n_tris + 1):
            n1, n2, n3 = tri.Triangle(i).Get()
            if is_rev:
                n2, n3 = n3, n2
            pts = [
                (tri.Node(n1).X(), tri.Node(n1).Y(), tri.Node(n1).Z()),
                (tri.Node(n2).X(), tri.Node(n2).Y(), tri.Node(n2).Z()),
                (tri.Node(n3).X(), tri.Node(n3).Y(), tri.Node(n3).Z()),
            ]
            for pt in pts:
                vertices.extend(pt)

            ax, ay, az = pts[0]
            bx, by, bz = pts[1]
            cx, cy, cz = pts[2]
            ux, uy, uz = bx-ax, by-ay, bz-az
            vx, vy, vz = cx-ax, cy-ay, cz-az
            nx_ = uy*vz - uz*vy
            ny_ = uz*vx - ux*vz
            nz_ = ux*vy - uy*vx
            ln = math.sqrt(nx_*nx_ + ny_*ny_ + nz_*nz_) or 1
            nx_, ny_, nz_ = nx_/ln, ny_/ln, nz_/ln
            for _ in range(3):
                normals.extend([nx_, ny_, nz_])
            area += math.sqrt((uy*vz-uz*vy)**2 + (uz*vx-ux*vz)**2 + (ux*vy-uy*vx)**2) / 2

        faces_data.append({
            'faceIdx': face_idx,
            'vertices': vertices,
            'normals': normals,
            'area': area,
            'nTriangles': n_tris
        })
        face_idx += 1
        exp.Next()

    if not faces_data:
        raise ValueError('Nicio fata gasita in fisierul STEP')

    return {'faces': faces_data, 'source': 'cadquery+OCP', 'faceCount': len(faces_data)}

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
