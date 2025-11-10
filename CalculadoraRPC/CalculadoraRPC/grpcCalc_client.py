# grpcCalc_client.py

import grpc
# Importa os módulos gerados
import grpcCalc_pb2
import grpcCalc_pb2_grpc

def run():
    # Conecta ao servidor gRPC que está em 'localhost' na porta 50051
    print("Tentando conectar ao servidor em localhost:50051...")
    try:
        channel = grpc.insecure_channel('localhost:50051')
        # Cria o "stub" do cliente, que nos permite chamar as funções remotas
        stub = grpcCalc_pb2_grpc.CalculatorStub(channel)
    except Exception as e:
        print(f"Não foi possível conectar ao servidor: {e}")
        return

    # Loop do menu principal
    while True:
        print("\n--- Calculadora RPC Interativa (gRPC) ---")
        print("1. Somar")
        print("2. Subtrair")
        print("3. Multiplicar")
        print("4. Dividir")
        print("5. Sair")

        choice = input("Escolha uma opção: ")

        if choice == '5':
            print("Saindo...")
            break

        if choice not in ['1', '2', '3', '4']:
            print("Opção inválida. Tente novamente.")
            continue

        # Ler os operandos do usuário
        try:
            x = int(input("Digite o primeiro número (x): "))
            y = int(input("Digite o segundo número (y): "))
        except ValueError:
            print("Entrada inválida. Por favor, digite números inteiros.")
            continue

        # Cria a mensagem de "Operands" para enviar ao servidor
        # Note que usamos a classe "Operands" do arquivo gerado
        operands_request = grpcCalc_pb2.Operands(x=x, y=y)

        try:
            # Chama a função remota apropriada no servidor
            if choice == '1':
                response = stub.Add(operands_request)
                print(f"Resultado (Soma): {response.value}")
            elif choice == '2':
                response = stub.Sub(operands_request)
                print(f"Resultado (Subtração): {response.value}")
            elif choice == '3':
                response = stub.Mul(operands_request)
                print(f"Resultado (Multiplicação): {response.value}")
            elif choice == '4':
                response = stub.Div(operands_request)
                print(f"Resultado (Divisão): {response.value}")

        except grpc.RpcError as e:
            # Captura erros do servidor (como divisão por zero)
            print(f"[Cliente] Erro na chamada RPC: {e.details()}")

if __name__ == '__main__':
    run()