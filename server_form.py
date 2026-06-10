import os
import re
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse
from jinja2 import Environment, FileSystemLoader

jinja_environment = Environment(loader=FileSystemLoader("templates"), autoescape=True)

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
    "default": "text/html; charset=utf-8",
}


class MeuHandlerHTTP(BaseHTTPRequestHandler):
    user = {}

    errors = {
        "user_name": [],
        "user_email": [],
        "user_password": [],
        "user_birthday": [],
    }

    def do_GET(self):

        if self.path == "/":
            template = jinja_environment.get_template("form.tmpt.html")
            empty_user = {"name": "", "birthday": "", "email": ""}

            content = template.render(user=empty_user, errors=self.errors, hasError=False).encode(
                "utf-8"
            )

            self.send_response(200)
            self.send_header("Content-Type", MIME_TYPES["html"])
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        # o path vem como '/diretorio/'
        caminho_local = "." + self.path
        content = b""  # bytizando a resposta
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
                            html += FILE_NAME_TEMPLATE.format(
                                FILE_NAME=nome, RESOURC_PATH=caminho_recurso
                            )
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

    def do_POST(self):
        self.errors = {
            "user_name": [],
            "user_email": [],
            "user_password": [],
            "user_birthday": [],
        }
        if not self.path.startswith("/usuario/criar/"):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        form_data_bytes = self.rfile.read(content_length)
        form_data_string = form_data_bytes.decode(encoding="utf-8")

        dados = parse.parse_qs(form_data_string)

        user_name = dados.get("user_name", [""])[0]
        user_email = dados.get("user_email", [""])[0]
        user_password = dados.get("user_password", [""])[0]
        user_birthday_str = dados.get("user_birthday", [""])[0]

        user = {
            "name": user_name,
            "email": user_email,
            "birthday": user_birthday_str,
        }

        if len(user_name) > 256:
            self.errors["user_name"].append(
                "Nome de Usuário inválido: não pode ser maior que 256 caracteres"
            )
        if len(user_name) < 6:
            self.errors["user_name"].append(
                "Nome de Usuário inválido: não pode ser menor que 6 caracteres"
            )

        if len(user_email) > 256:
            self.errors["user_email"].append(
                "E-mail inválido: não pode ser maior que 256 caracteres"
            )
        if "@" not in user_email:
            self.errors["user_email"].append("E-mail inválido: deve possuir o @")
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user_email):
            self.errors["user_email"].append("E-mail inválido")

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", user_birthday_str):
            self.errors["user_birthday"].append("Data de Aniversário inválida")
        else:
            partes_data = user_birthday_str.split("-")
            try:
                ano, mes, dia = (
                    int(partes_data[0]),
                    int(partes_data[1]),
                    int(partes_data[2]),
                )
                user_birthday_date = datetime.datetime(ano, mes, dia)

                if datetime.datetime.now() < user_birthday_date:
                    self.errors["user_birthday"].append(
                        "Data de Aniversário inválida: não pode ser uma data futura"
                    )
            except ValueError:
                self.errors["user_birthday"].append("Data de Aniversário inválida")

        if len(user_password) > 128:
            self.errors["user_password"].append(
                "Senha inválida: não pode ser maior que 128 caracteres"
            )
        if len(user_password) < 8:
            self.errors["user_password"].append(
                "Senha inválida: não pode ser menor que 8 caracteres"
            )
        if not re.search(r"[a-zA-Z]", user_password):
            self.errors["user_password"].append("Senha inválida: deve conter pelo menos uma letra")
        if not re.search(r"[0-9]", user_password):
            self.errors["user_password"].append("Senha inválida: deve conter pelo menos um número")
        if not re.search(r"[@$!%*?&]", user_password):
            self.errors["user_password"].append(
                "Senha inválida: deve conter pelo menos um caractere especial como @$!%*?&"
            )

        has_error = any(len(lista) > 0 for lista in self.errors.values())

        if has_error:
            template = jinja_environment.get_template("form.tmpt.html")
            conteudo_renderizado = template.render(
                hasError=has_error, errors=self.errors, user=user
            )
        else:
            user["name"] = user["name"].upper()
            user["birthday"] = user_birthday_date.strftime("%d/%m/%Y")
            template = jinja_environment.get_template("user.tmpt.html")
            conteudo_renderizado = template.render(user=user)
        content = conteudo_renderizado.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", MIME_TYPES["html"])
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)  # Agora o diabo vai rodar melhor que o do Nailton, José.


endereco = ("0.0.0.0", 8080)
meu_servidor_http = HTTPServer(endereco, MeuHandlerHTTP)

try:
    print(f"Servidor rodando em http://{endereco[0]}:{endereco[1]}")
    meu_servidor_http.serve_forever(poll_interval=0.5)
except KeyboardInterrupt:
    print("Servidor interrompido pelo usuário.")
except Exception as e:
    print(f"Erro no servidor: {e}")
finally:
    meu_servidor_http.server_close()
