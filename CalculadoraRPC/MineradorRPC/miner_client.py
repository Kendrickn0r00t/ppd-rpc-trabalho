# miner_client.py

import grpc
import miner_pb2
import miner_pb2_grpc
import hashlib
import threading
import random
import string
import sys # Para pegar o endereço do servidor
import time

# --- Variáveis Globais para Mineração ---
# Variável para sinalizar às threads que a solução foi encontrada
solution_found_event = threading.Event()
# Variável para armazenar a solução encontrada
global_solution = ""

# --- Lógica de Mineração (Worker) ---
def mine_worker(client_id, t_id, challenge_level, stub):
    """
    Esta função é executada por cada thread.
    Ela tenta encontrar a solução aleatoriamente.
    """
    global global_solution
    
    print(f"[Thread-{client_id}] Iniciando mineração para T_ID {t_id} (Challenge: {challenge_level})")
    
    target_zeros = '0' * challenge_level
    
    while not solution_found_event.is_set():
        # Gera uma string aleatória (nossa tentativa de solução)
        # Vamos usar 8 caracteres aleatórios
        attempt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Calcula o hash
        hash_object = hashlib.sha1(attempt.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        
        # A solução é válida?
        if hash_hex.endswith(target_zeros):
            # SUCESSO! Encontramos uma solução.
            
            # Sinaliza para todas as outras threads pararem
            solution_found_event.set() 
            
            # Armazena a solução
            global_solution = attempt
            
            print(f"\n[Thread-{client_id}] SOLUÇÃO ENCONTRADA! '{attempt}' -> Hash: {hash_hex}")
            break
            
    # print(f"[Thread-{client_id}] Parando.")


# --- Função Principal do Cliente ---
def run(host, client_id):
    global global_solution # Para acessar a variável global
    
    # Conecta ao servidor
    print(f"Tentando conectar ao servidor em {host}...")
    try:
        channel = grpc.insecure_channel(host)
        # Testa a conexão (espera ficar PRONTA)
        grpc.channel_ready_future(channel).result(timeout=10)
        stub = miner_pb2_grpc.MinerStub(channel)
        print("Conectado!")
    except Exception as e:
        print(f"Não foi possível conectar ao servidor: {e}")
        return

    # Loop do menu
    while True:
        print("\n--- Minerador RPC ---")
        print(f"Seu ClientID: {client_id}")
        print("1. getTransactionID (Ver transação atual)")
        print("2. getChallenge (Ver desafio de uma transação)")
        print("3. getTransactionStatus (Ver status de uma transação)")
        print("4. getWinner (Ver vencedor de uma transação)")
        print("5. getSolution (Ver solução de uma transação)")
        print("6. Mine (Tentar resolver o desafio atual)")
        print("7. Sair")
        
        choice = input("Escolha uma opção: ")

        try:
            if choice == '1':
                # 1. getTransactionID
                response = stub.GetTransactionID(miner_pb2.Empty())
                print(f"-> Transação atual pendente: {response.transactionID}")
            
            elif choice == '2':
                # 2. getChallenge
                tid = int(input("Digite o TransactionID: "))
                req = miner_pb2.TransactionRequest(transactionID=tid)
                response = stub.GetChallenge(req)
                if response.challenge == -1:
                    print(f"-> Erro: TransactionID {tid} é inválido.")
                else:
                    print(f"-> Desafio (Challenge) para T_ID {tid}: {response.challenge} (zeros)")

            elif choice == '3':
                # 3. getTransactionStatus
                tid = int(input("Digite o TransactionID: "))
                req = miner_pb2.TransactionRequest(transactionID=tid)
                response = stub.GetTransactionStatus(req)
                if response.status == -1:
                    print(f"-> Status: Inválido (T_ID {tid})")
                elif response.status == 0:
                    print(f"-> Status: Resolvido (T_ID {tid})")
                elif response.status == 1:
                    print(f"-> Status: Pendente (T_ID {tid})")

            elif choice == '4':
                # 4. getWinner
                tid = int(input("Digite o TransactionID: "))
                req = miner_pb2.TransactionRequest(transactionID=tid)
                response = stub.GetWinner(req)
                if response.clientID == -1:
                    print(f"-> Vencedor: Inválido (T_ID {tid})")
                elif response.clientID == 0:
                    print(f"-> Vencedor: Nenhum (T_ID {tid} ainda pendente)")
                else:
                    print(f"-> Vencedor: Cliente {response.clientID}")

            elif choice == '5':
                # 5. getSolution
                tid = int(input("Digite o TransactionID: "))
                req = miner_pb2.TransactionRequest(transactionID=tid)
                response = stub.GetSolution(req)
                if response.status == -1:
                    print(f"-> Erro: TransactionID {tid} é inválido.")
                else:
                    print(f"-> Solução para T_ID {tid}:")
                    print(f"   - Challenge: {response.challenge}")
                    print(f"   - Solution: '{response.solution}' (Vazio se não resolvido)")

            elif choice == '6':
                # 6. Mine (O processo complexo)
                print("[Mine] Iniciando processo de mineração...")
                
                # 1. Buscar transactionID atual
                print("[Mine] 1/6: Buscando T_ID atual...")
                tid_response = stub.GetTransactionID(miner_pb2.Empty())
                current_tid = tid_response.transactionID
                if current_tid == -1:
                    print("[Mine] Erro: Nenhuma transação disponível para minerar.")
                    continue
                print(f"[Mine] -> T_ID atual é: {current_tid}")
                
                # 2. Buscar a challenge (desafio)
                print(f"[Mine] 2/6: Buscando Challenge para T_ID {current_tid}...")
                challenge_req = miner_pb2.TransactionRequest(transactionID=current_tid)
                challenge_response = stub.GetChallenge(challenge_req)
                current_challenge = challenge_response.challenge
                if current_challenge == -1:
                    print("[Mine] Erro: T_ID inválido (o desafio pode ter acabado de ser resolvido).")
                    continue
                print(f"[Mine] -> Desafio é: {current_challenge} (zeros)")

                # 3. Buscar, localmente, uma solução (COM MÚLTIPLAS THREADS)
                print(f"[Mine] 3/6: Iniciando 4 threads de mineração local...")
                
                # Reseta os controles de thread
                solution_found_event.clear()
                global_solution = ""
                threads = []
                NUM_THREADS = 4 # Sugestão: use 4 threads
                
                start_time = time.time()
                
                for i in range(NUM_THREADS):
                    # Passamos (ID da thread, T_ID, Nível, Stub)
                    # O 'stub' não é usado no worker, mas poderia ser
                    # se quiséssemos que a thread submetesse.
                    t = threading.Thread(
                        target=mine_worker, 
                        args=(i, current_tid, current_challenge, stub)
                    )
                    threads.append(t)
                    t.start()
                
                # Espera todas as threads terminarem (ou seja, solution_found_event.set())
                for t in threads:
                    t.join()
                
                end_time = time.time()
                
                if not global_solution:
                    # Isso não deve acontecer se a lógica estiver correta
                    print("[Mine] Erro: Threads terminaram sem solução.")
                    continue

                print(f"[Mine] -> Mineração local levou {end_time - start_time:.2f} segundos.")

                # 4. Imprimir localmente a solução encontrada
                print(f"[Mine] 4/6: Solução local encontrada: '{global_solution}'")

                # 5. Submeter a solução ao servidor
                print("[Mine] 5/6: Submetendo solução ao servidor...")
                submit_req = miner_pb2.SubmitRequest(
                    transactionID=current_tid,
                    clientID=client_id,
                    solution=global_solution
                )
                submit_response = stub.SubmitChallenge(submit_req)

                # 6. Imprimir/Decodificar resposta do servidor
                print("[Mine] 6/6: Resposta do servidor recebida!")
                status = submit_response.status
                if status == 1:
                    print("="*30)
                    print("  VITÓRIA! Nossa solução foi a primeira!")
                    print("  O servidor aceitou a solução.")
                    print("="*30)
                elif status == 0:
                    print("-> FALHA. O servidor disse que nossa solução estava errada (hash inválido).")
                elif status == 2:
                    print("-> TARDE DEMAIS. Outro cliente resolveu este T_ID primeiro.")
                elif status == -1:
                    print("-> ERRO. O T_ID enviado era inválido.")

            elif choice == '7':
                print("Saindo...")
                break
            else:
                print("Opção inválida.")
        
        except grpc.RpcError as e:
            print(f"[ERRO RPC] Falha na comunicação com o servidor: {e.code()} - {e.details()}")
        except Exception as e:
            print(f"[ERRO INESPERADO] {e}")


if __name__ == '__main__':
    # O cliente deve receber o endereço do servidor (host:porta)
    if len(sys.argv) < 2:
        print("Erro: Forneça o endereço do servidor.")
        print(f"Uso: py {sys.argv[0]} <host>:<porta>")
        print(f"Exemplo: py {sys.argv[0]} localhost:50052")
        sys.exit(1)
        
    server_address = sys.argv[1]
    
    # Gera um ClientID aleatório para este usuário (entre 100 e 999)
    my_client_id = random.randint(100, 999)
    
    run(server_address, my_client_id)