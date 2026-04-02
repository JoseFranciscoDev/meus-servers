from http.server import HTTPServer, SimpleHTTPRequestHandler

endereco = ('', 8000)

meu_servidor_http = HTTPServer(
    endereco,
    SimpleHTTPRequestHandler,
    keyfile=None,
    alpn_protocols=["http/1.1"],
)

# O serve_forever() permite que nosso servidor escute uma requisição por vez enquanto o servidor viver e a fica verificando se há novas requisições a cada periodo settado no argumento poll_interval(em ms)
meu_servidor_http.serve_forever(poll_interval=0.5)





