import socket


while True:
    print("Tá funfando na porta http://localhost:2000")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 2000))
        """
        aqui é onde a gente define quantas conexões a gente
        quer deixar enfileirado enquanto o servidor atende as ativas
        """
        s.listen(5)
        conexao, endereco_origem = s.accept()

        with conexao:
            dados_recebidos = conexao.recv(1024)

            """Uma resposta HTTP para o Browser saber o que fazer com a resposta"""
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(dados_recebidos)}\r\n"
                "\r\n"
                f"{dados_recebidos.decode(encoding='utf-8')}"
            )
            conexao.sendall(response.encode())
