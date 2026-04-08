# FERRAMENTA EDUCACIONAL ORIENTATIVA PARA ALUNOS DE GRADUAÇÃO
# NA DISCIPLINA DE MANUFATURA INTEGRADA DA UTFPR

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from modules.analyser import analisar_arquivo_grafcet

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xml'}

app = Flask(__name__)
CORS(app, origins=["https://anfugo.github.io"])  # permite acesso do GitHub Pages

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# UTIL
# =========================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =========================
# HEALTH CHECK (opcional)
# =========================
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "API GRAFCET funcionando"
    })

# =========================
# ENDPOINT PRINCIPAL
# =========================
@app.route('/analisar', methods=['POST'])
def analisar():

    # -------------------------
    # validação
    # -------------------------
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "filename": filename,
            "error": "Nenhum arquivo enviado"
        }), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({
            "success": False,
            "filename": filename,
            "error": "Nome de arquivo inválido"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "filename": filename,
            "error": "Extensão inválida. Use .xml"
        }), 400

    # -------------------------
    # processamento
    # -------------------------
    filename = secure_filename(file.filename)
    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(caminho_arquivo)

        resultado_da_analise = analisar_arquivo_grafcet(caminho_arquivo)

        # 🔴 se o analyser já detectou erro
        if not resultado_da_analise.get("success", True):
            return jsonify({
                "success": False,
                "filename": filename,
                "error": resultado_da_analise.get("error", "Erro na análise")
            }), 400

        # ✔ sucesso
        return jsonify({
            "success": True,
            "filename": filename,
            "resultados": resultado_da_analise["resultados"]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "filename": filename,
            "error": f"Erro ao processar arquivo: {str(e)}"
        }), 500

# =========================
# ERRO: arquivo grande
# =========================
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "Arquivo muito grande (máx 16MB)"
    }), 413

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)