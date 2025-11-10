# grpcCalc_server.py

import grpc
# Importa os módulos que acabamos de gerar
import grpcCalc_pb2
import grpcCalc_pb2_grpc
from concurrent import futures # Para o pool de threads do servidor
import time

# Esta classe implementa a lógica do servidor.
# Ela herda da classe gerada "CalculatorServicer"
class CalculatorServicer(grpcCalc_pb2_grpc.CalculatorServicer):

    # Implementa a função Add, conforme definido no .proto
    def Add(self, request, context):
        print(f"[Servidor] Recebida requisição Add: ({request.x}, {request.y})")
        result = request.x + request.y
        # Retorna a mensagem de Resultado
        return grpcCalc_pb2.Result(value=result)

    # Implementa a função Sub
    def Sub(self, request, context):
        print(f"[Servidor] Recebida requisição Sub: ({request.x}, {request.y})")
        result = request.x - request.y
        return grpcCalc_pb2.Result(value=result)

    # Implementa a função Mul
    def Mul(self, request, context):
        print(f"[Servidor] Recebida requisição Mul: ({request.x}, {request.y})")
        result = request.x * request.y
        return grpcCalc_pb2.Result(value=result)

    # Implementa a função Div
    def Div(self, request, context):
        print(f"[Servidor] Recebida requisição Div: ({request.x}, {request.y})")

        # Tratamento de divisão por zero
        if request.y == 0:
            # Envia um erro de volta para o cliente
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Erro: Divisão por zero!")
            return grpcCalc_pb2.Result() # Retorna uma resposta vazia

        result = request.x // request.y # Divisão inteira
        return grpcCalc_pb2.Result(value=result)

# Função principal para iniciar o servidor
def serve():
    # Cria o servidor gRPC
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Adiciona nossa lógica (CalculatorServicer) ao servidor
    grpcCalc_pb2_grpc.add_CalculatorServicer_to_server(
        CalculatorServicer(), server
    )

    # Inicia o servidor na porta 50051 (pode ser qualquer porta)
    print("Iniciando servidor gRPC na porta 50051...")
    server.add_insecure_port('[::]:50051')
    server.start()

    # Mantém o servidor rodando
    try:
        while True:
            time.sleep(86400) # Dorme por um dia
    except KeyboardInterrupt:
        print("Parando o servidor...")
        server.stop(0)

if __name__ == '__main__':
    serve()