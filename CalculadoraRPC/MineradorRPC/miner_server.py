# miner_server.py

import grpc
import miner_pb2
import miner_pb2_grpc
from concurrent import futures
import time
import random
import hashlib # Para o SHA-1
import threading # Para travar o acesso à tabela

# --- Estrutura de Dados do Servidor ---
# Vamos usar uma classe para agrupar os dados e a trava
class TransactionDatabase:
    def __init__(self):
        # A tabela de transações.
        # Estrutura: { transactionID: [Challenge, Solution, WinnerClientID] }
        self.table = {}
        # Trava (lock) para evitar que dois clientes escrevam na tabela ao mesmo tempo
        self.lock = threading.Lock()
        # O ID da transação atual que está aberta para mineração
        self.current_transaction_id = -1
        # Contador para gerar novos IDs
        self.next_transaction_id = 0

    def create_new_challenge(self):
        with self.lock: # Trava a tabela
            # Gera um novo desafio
            t_id = self.next_transaction_id
            challenge = random.randint(1, 5) # Desafio [1..5]
            solution = "" # Solução ainda não encontrada
            winner = -1   # Ninguém venceu ainda

            # Armazena na tabela
            self.table[t_id] = [challenge, solution, winner]
            
            # Define este como o desafio atual
            self.current_transaction_id = t_id
            
            # Incrementa o contador para a próxima vez
            self.next_transaction_id += 1
            
            print(f"[Servidor] Novo desafio criado! ID: {t_id}, Challenge: {t_id}")
            return t_id, challenge
    
    # Função helper para verificar se um ID existe
    def is_valid_tid(self, t_id):
        return t_id in self.table

    # Função helper para verificar se um ID já foi resolvido
    def is_solved(self, t_id):
        if not self.is_valid_tid(t_id):
            return False
        return self.table[t_id][2] != -1 # Se Winner != -1, está resolvido


# Instância global do nosso "banco de dados"
DB = TransactionDatabase()
# --- Fim da Estrutura de Dados ---


# --- Implementação do Servidor gRPC ---
class MinerServicer(miner_pb2_grpc.MinerServicer):

    def GetTransactionID(self, request, context):
        # Retorna o ID da transação que ainda está pendente
        # Usamos DB.lock para ler com segurança, embora aqui não seja 100%
        # necessário, é uma boa prática.
        with DB.lock:
            tid = DB.current_transaction_id
        return miner_pb2.TransactionIDResponse(transactionID=tid)

    def GetChallenge(self, request, context):
        t_id = request.transactionID
        
        # Acessa a tabela (apenas leitura, não precisa de trava)
        if not DB.is_valid_tid(t_id):
            return miner_pb2.ChallengeResponse(challenge=-1) # ID Inválido
        
        challenge = DB.table[t_id][0]
        return miner_pb2.ChallengeResponse(challenge=challenge)

    def GetTransactionStatus(self, request, context):
        t_id = request.transactionID
        
        if not DB.is_valid_tid(t_id):
            return miner_pb2.StatusResponse(status=-1) # ID Inválido
        
        if DB.is_solved(t_id):
            return miner_pb2.StatusResponse(status=0) # Resolvido
        else:
            return miner_pb2.StatusResponse(status=1) # Pendente

    def GetWinner(self, request, context):
        t_id = request.transactionID
        
        if not DB.is_valid_tid(t_id):
            return miner_pb2.WinnerResponse(clientID=-1) # ID Inválido
        
        winner_id = DB.table[t_id][2] # Pega o ID do vencedor
        
        if winner_id == -1:
            return miner_pb2.WinnerResponse(clientID=0) # Sem vencedor ainda
        else:
            return miner_pb2.WinnerResponse(clientID=winner_id)

    def GetSolution(self, request, context):
        t_id = request.transactionID
        
        if not DB.is_valid_tid(t_id):
            # Retorna status inválido e dados vazios
            return miner_pb2.SolutionResponse(status=-1, solution="", challenge=0)
        
        # Pega os dados da tabela
        challenge, solution, winner = DB.table[t_id]
        
        return miner_pb2.SolutionResponse(status=1, solution=solution, challenge=challenge)

    def SubmitChallenge(self, request, context):
        t_id = request.transactionID
        client_id = request.clientID
        solution = request.solution

        print(f"[Servidor] Recebida tentativa de solução para T_ID {t_id} do Cliente {client_id} (Sol: '{solution}')")

        # --- Ponto Crítico ---
        # Precisamos travar o banco de dados, pois vamos LER e ESCREVER
        with DB.lock:
            if not DB.is_valid_tid(t_id):
                return miner_pb2.SubmitResponse(status=-1) # ID Inválido

            # Verifica se já foi solucionado
            if DB.is_solved(t_id):
                return miner_pb2.SubmitResponse(status=2) # Já solucionado

            # Se chegou aqui, o T_ID é válido e está pendente.
            # Vamos verificar a solução.
            challenge_level = DB.table[t_id][0]
            
            # --- Lógica de Validação ---
            # O desafio é: encontrar uma 'solution' (string) que, 
            # quando aplicada ao SHA-1, o resultado (hash) termine
            # com N zeros, onde N é o 'challenge_level'.
            
            hash_object = hashlib.sha1(solution.encode('utf-8'))
            hash_hex = hash_object.hexdigest()
            
            # O "target" (alvo) é uma string de N zeros
            target_zeros = '0' * challenge_level
            
            # A solução é válida?
            if hash_hex.endswith(target_zeros):
                # SOLUÇÃO VÁLIDA!
                print(f"[Servidor] SUCESSO! Cliente {client_id} resolveu o T_ID {t_id} com o hash {hash_hex}")
                
                # Atualiza a tabela
                DB.table[t_id][1] = solution # Salva a solução
                DB.table[t_id][2] = client_id # Salva o Vencedor
                
                # O desafio atual agora é outro!
                # Criamos um novo desafio para o futuro
                DB.create_new_challenge()
                
                return miner_pb2.SubmitResponse(status=1) # 1 = Solução Válida
            else:
                # SOLUÇÃO INVÁLIDA!
                print(f"[Servidor] FALHA. Cliente {client_id} errou. Hash: {hash_hex}")
                return miner_pb2.SubmitResponse(status=0) # 0 = Solução Inválida

# --- Fim da Implementação gRPC ---


def serve():
    # 1. Inicia o banco de dados criando o primeiro desafio (TransactionID = 0)
    print("[Servidor] Carregando...")
    DB.create_new_challenge() # Isso cria o T_ID 0

    # 2. Inicia o servidor gRPC
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    miner_pb2_grpc.add_MinerServicer_to_server(MinerServicer(), server)
    server.add_insecure_port('[::]:50052') # Usando porta 50052 (diferente da calculadora)
    print("[Servidor] Servidor gRPC iniciado na porta 50052.")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Parando o servidor...")
        server.stop(0)

if __name__ == '__main__':
    serve()