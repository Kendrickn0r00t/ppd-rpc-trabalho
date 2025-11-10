PPD-RPC: Calculadora e Minerador gRPC
Trabalho da disciplina de PPD sobre Chamada de Procedimento Remoto (RPC) usando Python e gRPC.

Grupo:
Kendrick Henrique Vescovi Xavier 2212258
Henrique Borghi Machado 2214338 

Link para o Vídeo de Demonstração:
https://drive.google.com/file/d/1dcB9tXXWbYOJ6x1OmRq7UV0IapGjXf_v/view?usp=drive_link

Relatório Técnico

1. Metodologia de Implementação,

Ambas as atividades foram implementadas seguindo a arquitetura Cliente/Servidor utilizando o framework gRPC da Google sobre a linguagem Python.
O fluxo de desenvolvimento seguiu os seguintes passos:
1- Definição do Serviço: Criação de um arquivo .proto (Protobuf) para definir formalmente os serviços, funções (RPCs) e mensagens (estruturas de dados) a serem trocadas.
2- Geração de Stubs: Utilização da ferramenta grpc_tools.protoc (chamada via py -m grpc_tools.protoc ...) para gerar automaticamente os códigos "stub" de cliente e servidor (_pb2.py e _pb2_grpc.py).
3- Implementação do Servidor: Criação de um script _server.py que importa os stubs gerados, implementa a lógica de negócio (as funções do serviço) e inicia um servidor gRPC para aguardar conexões.
4- Implementação do Cliente: Criação de um script _client.py que importa os stubs, se conecta ao servidor e fornece uma interface de linha de comando (menu) para o usuário invocar as funções remotas.

2. Atividade 1: Calculadora RPC

* Descrição: Implementa uma calculadora remota com as quatro operações básicas (soma, subtração, multiplicação e divisão).
* Servidor (grpcCalc_server.py): Implementa as funções Add, Sub, Mul e Div. Inclui um tratamento de erro para divisão por zero, retornando um status INVALID_ARGUMENT ao cliente.
* Cliente (grpcCalc_client.py): Apresenta um menu interativo onde o usuário escolhe a operação e insere os dois operandos. O cliente então chama a RPC correspondente e exibe o resultado ou a mensagem de erro vinda do servidor.

3. Atividade 1 (Parte 2): Minerador RPC gRPC

* Descrição: Simula um sistema de mineração de criptomoedas simplificado, onde clientes competem para resolver um desafio criptográfico (prova de trabalho) proposto pelo servidor.
* Servidor (miner_server.py):
  * Tabela de Transações: Mantém uma tabela (um dicionário Python) com o estado de cada transação (Challenge, Solution, Winner).
  * Segurança de Threads (Locks): Utiliza um threading.Lock para garantir que o acesso à tabela seja thread-safe. Isso é crucial para evitar que dois clientes submetam uma solução ao mesmo tempo e corrompam o estado (condição de corrida). A trava é usada em pontos críticos, como SubmitChallenge (onde há leitura e escrita) e na criação de um novo desafio.
  * Lógica do Desafio: O desafio (Challenge) é um número N. A solução é encontrar uma string que, ao passar pela função de hash SHA-1, gere um hash terminado em N zeros.
  * Funções RPC: Implementa as 6 funções requisitadas (GetTransactionID, GetChallenge, GetTransactionStatus, SubmitChallenge, GetWinner, GetSolution).
  * Novo Desafio: Ao receber uma solução correta (SubmitChallenge), o servidor marca o vencedor, salva a solução e automaticamente cria um novo desafio, incrementando o TransactionID atual.

* Cliente (miner_client.py):
  * Menu de Interação: Fornece um menu para o usuário inspecionar o estado da "blockchain" (consultando o servidor com as várias funções get...).
  * Função "Mine" (Opção 6): Este é o núcleo do cliente.
    1- Ele primeiro pergunta ao servidor qual é o desafio atual (GetTransactionID e GetChallenge).
    2- Em seguida, dispara múltiplas threads (4, no nosso caso) para procurar a solução localmente (conforme sugerido no documento).
    3- As threads competem localmente para encontrar a solução. Elas usam um threading.Event para sinalizar umas às outras quando uma solução é encontrada, fazendo com que todas parem.
    4- A primeira thread a encontrar a solução a submete ao servidor (SubmitChallenge).
    5- O cliente então informa ao usuário se ele foi o vencedor ("VITÓRIA!") ou se outro cliente foi mais rápido ("TARDE DEMAIS").

4. Testes e Resultados Encontrados
Os testes foram realizados localmente no Windows 11 usando o VS Code com múltiplos terminais integrados.

* Calculadora: O teste foi executado com um servidor e um cliente. Todas as operações funcionaram como esperado. O teste de divisão por zero (10 / 0) demonstrou o cliente recebendo corretamente a mensagem de erro do servidor ([Cliente] Erro na chamada RPC: Erro: Divisão por zero!).
* Minerador: O teste foi executado com um servidor e dois clientes rodando simultaneamente para simular a competição.
  * Ambos os clientes receberam o mesmo TransactionID: 0 e o mesmo Challenge.
  * Ambos executaram a função "Mine" (Opção 6) ao mesmo tempo.
  * Resultado: Conforme esperado, um cliente encontrou a solução e a submeteu primeiro, recebendo a mensagem "VITÓRIA!". O segundo cliente, ao submeter sua solução (mesmo que correta) logo em seguida, recebeu a mensagem "TARDE DEMAIS".
  * O log do servidor mostrou a sequência correta: uma tentativa de solução foi aceita (SUCESSO), e a segunda foi rejeitada (Já solucionado). O servidor então criou o próximo desafio (TransactionID: 1).
  * Isso valida o uso correto do threading.Lock no servidor para gerenciar o estado da competição.

Instruções de Compilação e Execução

1. Pré-requisitos
  1. Ter o Python instalado (testado com Python 3.10+).
  2 .Instalar as bibliotecas grpcio e grpcio-tools via pip: (Use py -m pip se pip não for reconhecido)
      py -m pip install grpcio
      py -m pip install grpcio-tools

2. Geração dos Stubs
Antes de executar, você deve gerar os arquivos "stub" (_pb2.py e _pb2_grpc.py) para cada projeto.
  1- Para a Calculadora: Navegue até a pasta CalculadoraRPC e execute:
    py -m grpc_tools.protoc --proto_path=. ./grpcCalc.proto --python_out=. --grpc_python_out=.

  2.Para o Minerador: Navegue até a pasta MineradorRPC e execute:
    py -m grpc_tools.protoc --proto_path=. ./miner.proto --python_out=. --grpc_python_out=.

3. Execução da Atividade 1 (Calculadora)
  1- Abra um terminal na pasta CalculadoraRPC e inicie o servidor:
    py grpcCalc_server.py
   
  2- Abra um segundo terminal na pasta CalculadoraRPC e inicie o cliente:
    py grpcCalc_client.py

4. Execução da Atividade 2 (Minerador)
  1- Abra um terminal na pasta MineradorRPC e inicie o servidor:
    py miner_server.py

  2- Abra um segundo terminal na pasta MineradorRPC e inicie o primeiro cliente:
    py miner_client.py localhost:50052

  3- (Opcional) Abra um terceiro terminal na pasta MineradorRPC e inicie o segundo cliente para ver a competição:
py miner_client.py localhost:50052
