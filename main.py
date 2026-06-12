#!/usr/bin/env python3
import os, sys, json, tempfile, math, struct
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/health', methods=['GET'])
def health():
    try:
        import cadquery as cq
        occ_ok = True
        ver = cq.__version__
    except:
        try:
            from OCC.Core.STEPControl import STEPControl_Reader
            occ_ok = True
            ver = 'pythonocc'
        except:
            occ_ok = False
            ver = None
    return jsonify({'status': 'ok', 'occ': occ_ok, 'version': ver})

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    ext = f.filename.rsplit('.', 1)[-1].lower()
    data = f.read()

    with tempfile.NamedTemporaryFile(suffix='.'+ext, delete=False) as tmp:
        tmp.write(data); tmp_path = tmp.name

    try:
        if ext in ('step', 'stp'):
            result = parse_step(tmp_path)
        elif ext == 'stl':
            result = parse_stl(data)
        else:
            return jsonify({'error': f'Format nesuportat: {ext}'}), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try: os.unlink(tmp_path)
        except: pass

def parse_step(filepath):
    # Try CadQuery first
    try:
        import cadquery as cq
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.BRep import BRep_Tool
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_REVERSED
        from OCC.Core.TopoDS import topods

        shape = cq.importers.importStep(filepath).val()
        occ_shape = shape.wrapped

        BRepMesh_IncrementalMesh(occ_shape, 0.05, False, 0.3).Perform()
        return extract_faces(occ_shape)
    except ImportError:
        pass

    # Fallback: raw pythonocc
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

    reader = STEPControl_Reader()
    if reader.ReadFile(filepath) != 1:
        raise ValueError("STEP invalid")
    reader.TransferRoots()
    shape = reader.OneShape()
    BRepMesh_IncrementalMesh(shape, 0.05, False, 0.3).Perform()
    return extract_faces(shape)

def extract_faces(shape):
    from OCC.Core.BRep import BRep_Tool
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCC.Core.TopoDS import topods

    faces_data = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    face_idx = 0

    while exp.More():
        face = topods.Face(exp.Current())
        tri = BRep_Tool.Triangulation_s(face, face.Location())

        if tri is None or tri.NbNodes() == 0 or tri.NbTriangles() == 0:
            exp.Next(); continue

        is_rev = face.Orientation() == TopAbs_REVERSED
        n_tris = tri.NbTriangles()
        vertices, normals = [], []
        area = 0.0

        for i in range(1, n_tris + 1):
            n1, n2, n3 = tri.Triangle(i).Get()
            if is_rev: n2, n3 = n3, n2
            pts = [(tri.Node(n).X(), tri.Node(n).Y(), tri.Node(n).Z()) for n in (n1,n2,n3)]
            for pt in pts: vertices.extend(pt)

            ax,ay,az=pts[0]; bx,by,bz=pts[1]; cx,cy,cz=pts[2]
            ux,uy,uz=bx-ax,by-ay,bz-az; vx,vy,vz=cx-ax,cy-ay,cz-az
            nx_=uy*vz-uz*vy; ny_=uz*vx-ux*vz; nz_=ux*vy-uy*vx
            ln=math.sqrt(nx_*nx_+ny_*ny_+nz_*nz_) or 1
            nx_,ny_,nz_=nx_/ln,ny_/ln,nz_/ln
            for _ in range(3): normals.extend([nx_,ny_,nz_])
            area += math.sqrt((uy*vz-uz*vy)**2+(uz*vx-ux*vz)**2+(ux*vy-uy*vx)**2)/2

        faces_data.append({'faceIdx':face_idx,'vertices':vertices,'normals':normals,'area':area,'nTriangles':n_tris})
        face_idx += 1
        exp.Next()

    if not faces_data:
        raise ValueError("Nicio față găsită")
    return {'faces': faces_data, 'source': 'step_occ', 'faceCount': len(faces_data)}

def parse_stl(data):
    if len(data) < 84: raise ValueError("STL invalid")
    n_tri = struct.unpack_from('<I', data, 80)[0]
    verts, norms = [], []
    offset = 84
    for _ in range(n_tri):
        nx,ny,nz = struct.unpack_from('<fff', data, offset); offset+=12
        for _ in range(3):
            x,y,z = struct.unpack_from('<fff', data, offset); offset+=12
            verts.extend([x,y,z]); norms.extend([nx,ny,nz])
        offset += 2
    return {'faces':[{'faceIdx':0,'vertices':verts,'normals':norms,'area':0,'nTriangles':n_tri}],'source':'stl'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"G22 Server pe portul {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
