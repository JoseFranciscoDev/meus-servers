import re
import datetime
from urllib import parse
from wsgiref.simple_server import make_server
from jinja2 import Environment, FileSystemLoader

jinja_environment = Environment(loader=FileSystemLoader("templates"), autoescape=True)

MIME_TYPES = {
    "html": "text/html; charset=utf-8",
    "txt": "text/plain",
    "js": "text/javascript",
    "css": "text/css",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "py": "text/x-python",
}


# ---------------------------------------------------------------------------
# Helpers de resposta
# Encapsulam o padrão "chamar start_response + retornar body" que se repete
# ---------------------------------------------------------------------------


def resposta_html(start_response, status, html_str):
    """Retorna uma resposta HTML a partir de uma string."""
    body = html_str.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", MIME_TYPES["html"]),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def resposta_redirect(start_response, location):
    """Retorna um redirect 301."""
    start_response("301 Moved Permanently", [("Location", location)])
    return [b""]


# ---------------------------------------------------------------------------
# Handlers — cada um cuida de uma rota/verbo
# ---------------------------------------------------------------------------


def handle_get_form(environ, start_response):
    """GET / — exibe o formulário vazio."""
    template = jinja_environment.get_template("form.tmpt.html")
    html = template.render(
        user={"name": "", "birthday": "", "email": ""},
        errors={"user_name": [], "user_email": [], "user_password": [], "user_birthday": []},
        hasError=False,
    )
    return resposta_html(start_response, "200 OK", html)


def handle_post_usuario(environ, start_response):
    """POST /usuario/criar/ — valida e processa o formulário."""
    errors = {
        "user_name": [],
        "user_email": [],
        "user_password": [],
        "user_birthday": [],
    }

    # Lendo o body — environ['wsgi.input'] equivale ao self.rfile do BaseHTTPRequestHandler
    content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
    body = environ["wsgi.input"].read(content_length).decode("utf-8")
    dados = parse.parse_qs(body)

    user_name = dados.get("user_name", [""])[0]
    user_email = dados.get("user_email", [""])[0]
    user_password = dados.get("user_password", [""])[0]
    user_birthday_str = dados.get("user_birthday", [""])[0]

    user = {"name": user_name, "email": user_email, "birthday": user_birthday_str}

    # Validações (mesma lógica de antes)
    if len(user_name) > 256:
        errors["user_name"].append("Nome inválido: não pode ser maior que 256 caracteres")
    if len(user_name) < 6:
        errors["user_name"].append("Nome inválido: não pode ser menor que 6 caracteres")

    if len(user_email) > 256:
        errors["user_email"].append("E-mail inválido: não pode ser maior que 256 caracteres")
    if "@" not in user_email:
        errors["user_email"].append("E-mail inválido: deve possuir o @")
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user_email):
        errors["user_email"].append("E-mail inválido")

    user_birthday_date = None
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", user_birthday_str):
        errors["user_birthday"].append("Data de Aniversário inválida")
    else:
        try:
            ano, mes, dia = map(int, user_birthday_str.split("-"))
            user_birthday_date = datetime.datetime(ano, mes, dia)
            if datetime.datetime.now() < user_birthday_date:
                errors["user_birthday"].append("Data de Aniversário inválida: não pode ser futura")
        except ValueError:
            errors["user_birthday"].append("Data de Aniversário inválida")

    if len(user_password) > 128:
        errors["user_password"].append("Senha inválida: não pode ser maior que 128 caracteres")
    if len(user_password) < 8:
        errors["user_password"].append("Senha inválida: não pode ser menor que 8 caracteres")
    if not re.search(r"[a-zA-Z]", user_password):
        errors["user_password"].append("Senha inválida: deve conter pelo menos uma letra")
    if not re.search(r"[0-9]", user_password):
        errors["user_password"].append("Senha inválida: deve conter pelo menos um número")
    if not re.search(r"[@$!%*?&]", user_password):
        errors["user_password"].append(
            "Senha inválida: deve conter pelo menos um caractere especial"
        )

    has_error = any(errors[k] for k in errors)

    if has_error:
        template = jinja_environment.get_template("form.tmpt.html")
        html = template.render(hasError=True, errors=errors, user=user)
    else:
        user["name"] = user["name"].upper()
        user["birthday"] = user_birthday_date.strftime("%d/%m/%Y")
        template = jinja_environment.get_template("user.tmpt.html")
        html = template.render(user=user)

    return resposta_html(start_response, "200 OK", html)


def app(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = environ["PATH_INFO"]

    if method == "GET" and path == "/":
        return handle_get_form(environ, start_response)

    if method == "POST" and path.startswith("/usuario/criar/"):
        return handle_post_usuario(environ, start_response)

    return resposta_html(start_response, "404 Not Found", "<h1>404 Not Found</h1>")


if __name__ == "__main__":
    servidor = make_server("0.0.0.0", 8080, app)
    print("Servidor WSGI rodando em http://0.0.0.0:8080")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Servidor interrompido.")
