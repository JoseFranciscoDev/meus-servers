import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# TEMPLATES
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
<html>
    <body>
        <h1>404 Not Found</h1>
        <p>Error code: 404</p>
        <p>Message: File not found.</p>
    </body>
</html>
"""

MIME_TYPES = {
    "html": "text/html; charset=utf-8",
    "txt": "text/plain",
    "js": "text/javascript",
    "css": "text/css",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "py": "text/x-python",
    "default": "text/html; charset=utf-8"
}

class MeuHandlerHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        # o path vem como '/diretorio/'
        caminho_local = "." + self.path
        
        content = b"" # bytizando a resposta
        status = 200
        content_type = MIME_TYPES["default"]
        if os.path.isdir(caminho_local) and not self.path.endswith("/"):
            self.send_response(301)
            self.send_header("Location", self.path + "/")
            self.end_headers()
            return 
        try:
            if os.path.isdir(caminho_local):
                # Bora ver se tem um index.html
                index_path = os.path.join(caminho_local, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "rb") as f:
                        content = f.read()
                        content_type = MIME_TYPES["html"]
                else:
                    # Montar o djabo do html
                    html = INDEX_BEGIN_TEMPLATE.format(FILE_PATH=self.path)
                    html += FILE_NAME_TEMPLATE.format(RESOURC_PATH="..", FILE_NAME="Voltar")
                    
                    with os.scandir(caminho_local) as entries:
                        for entry in entries:
                            caminho_recurso = entry.name + ("/" if entry.is_dir() else "")
                            nome = entry.name + ("/" if entry.is_dir() else "")
                            html += FILE_NAME_TEMPLATE.format(FILE_NAME=nome, RESOURC_PATH=caminho_recurso)
                    html += INDEX_END_TEMPLATE
                    content = html.encode("utf-8")
                    content_type = MIME_TYPES["html"]
            
            else:
                
                with open(caminho_local, "rb") as f:
                    content = f.read()
                    extensao = caminho_local.split(".")[-1].lower()
                    content_type = MIME_TYPES.get(extensao, MIME_TYPES["default"])

        except FileNotFoundError:
            status = 404
            content = NOT_FOUND_TEMPLATE.encode("utf-8")
            content_type = MIME_TYPES["html"]
        except Exception as e:
            status = 500
            content = f"<h1>Erro Interno: {e}</h1>".encode("utf-8")


        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

endereco = ("0.0.0.0", 8080)
meu_servidor_http = HTTPServer(endereco, MeuHandlerHTTP)
try:
    print(f'Servidor rodando em http://{endereco[0]}:{endereco[1]}')
    meu_servidor_http.serve_forever(poll_interval=0.5)
except KeyboardInterrupt:
    print('Servidor interrompido pelo usuário.')
except Exception as e:
    print(f'Erro no servidor: {e}')
finally: meu_servidor_http.server_close() 