import os, struct, math
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'occ': False, 'version': '1.0'})

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext == 'stl':
        return jsonify(parse_stl(f.read()))
    return jsonify({'error': 'STEP suport în curând'}), 501

def parse_stl(data):
    n = struct.unpack_from('<I', data, 80)[0]
    verts, norms = [], []
    o = 84
    for _ in range(n):
        nx,ny,nz = struct.unpack_from('<fff', data, o); o+=12
        for _ in range(3):
            x,y,z = struct.unpack_from('<fff', data, o); o+=12
            verts.extend([x,y,z]); norms.extend([nx,ny,nz])
        o+=2
    return {'faces':[{'faceIdx':0,'vertices':verts,'normals':norms,'area':0,'nTriangles':n}],'source':'stl'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
