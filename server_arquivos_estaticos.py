import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- TEMPLATES ---
INDEX_BEGIN_TEMPLATE = """
<!DOCTYPE HTML>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>Directory listing for {FILE_PATH}</title>
</head>
<body>
    <h1>Directory listing for {FILE_PATH}</h1>
    <hr>
    <ul>
"""

FILE_NAME_TEMPLATE = '<li><a href="{RESOURC_PATH}">{FILE_NAME}</a></li>'

INDEX_END_TEMPLATE = "</ul><hr></body></html>"

NOT_FOUND_TEMPLATE = """
<!DOCTYPE HTML>
<html lang="pt-br">
    <head><meta charset="utf-8"><title>404 Not Found</title></head>
    <body><h1>404 Not Found</h1><p>O arquivo ou diretório não existe.</p></body>
</html>
"""

MIME_TYPES = {
    "html": "text/html; charset=utf-8",
    "txt": "text/plain",
    "js": "text/javascript",
    "css": "text/css",
    "png": "image/png",
    "jpg": "image/jpeg",
    "py": "text/x-python",
    "default": "text/html; charset=utf-8"
}

class MeuHandlerHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        # Tradução do caminho da URL para o sistema de arquivos local
        # o path vem como '/diretorio/'
        caminho_local = "." + self.path
        
        content = b""
        status = 200
        content_type = MIME_TYPES["default"]

        try:
            if os.path.isdir(caminho_local):

                # Bora ver se tem um index.html
                index_path = os.path.join(caminho_local, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "rb") as f:
                        content = f.read()
                        content_type = MIME_TYPES["html"]
                else:
                    # Gerar Listagem de Diretório
                    html = INDEX_BEGIN_TEMPLATE.format(FILE_PATH=self.path)
                    html += FILE_NAME_TEMPLATE.format(RESOURC_PATH="..", FILE_NAME="Voltar")
                    
                    with os.scandir(caminho_local) as entries:
                        for entry in entries:
                            nome_recurso = entry.name + ("/" if entry.is_dir() else "")
                            nome = entry.name + ("/" if entry.is_dir() else "")
                            html += FILE_NAME_TEMPLATE.format(FILE_NAME=nome, RESOURC_PATH=nome_recurso)
                    
                    html += INDEX_END_TEMPLATE
                    content = html.encode("utf-8")
                    content_type = MIME_TYPES["html"]
            
            else:
                
                with open(caminho_local, "rb") as f:
                    content = f.read()
                    ext = caminho_local.split(".")[-1]
                    content_type = MIME_TYPES.get(ext, MIME_TYPES["default"])

        except FileNotFoundError:
            status = 404
            content = NOT_FOUND_TEMPLATE.encode("utf-8")
            content_type = MIME_TYPES["html"]
        except Exception as e:
            status = 500
            content = f"<h1>Erro Interno: {e}</h1>".encode("utf-8")

        # A gente tem que preparar a resposta com o status, headers e o conteúdo
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

endereco = ("localhost", 8080)
meu_servidor_http = HTTPServer(endereco, MeuHandlerHTTP)
try:
    print(f'Servidor rodando em http://{endereco[0]}:{endereco[1]}')
    meu_servidor_http.serve_forever(poll_interval=0.5)
except KeyboardInterrupt:
    print('Servidor interrompido pelo usuário.')
except Exception as e:
    print(f'Erro no servidor: {e}')
finally: meu_servidor_http.server_close() 