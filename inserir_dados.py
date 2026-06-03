import sqlite3
from datetime import datetime

# 1. Conectar ao banco de dados local (substitua pelo nome correto do seu arquivo .db)
DATABASE_NAME = "estoque.db" 

def lançar_dados_planilha():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    print("🔄 Iniciando o lançamento dos dados de Leishmaniose...")

    # Step 1: Garantir que o teste de Leishmaniose está cadastrado na tabela 'testes'
    # Baseado na planilha, a apresentação padrão é Caixa com 10 unidades
    nome_teste = "LEISHMANIOSE TESTE RÁPIDO"
    unidades_por_caixa = 10
    
    cursor.execute("""
        INSERT INTO testes (nome, unidades_por_caixa) 
        VALUES (?, ?) 
        ON CONFLICT(nome) DO UPDATE SET unidades_por_caixa=excluded.unidades_por_caixa
    """, (nome_teste, unidades_por_caixa))
    
    # Pegar o ID do teste que acabou de ser inserido ou já existia
    cursor.execute("SELECT id FROM testes WHERE nome = ?", (nome_teste,))
    teste_id = cursor.fetchone()[0]

    # Step 2: Lista com todos os lotes e saldos da sua imagem
    # Estrutura: (Lote/Fabricante, Saldo Inicial/Atual, Data de Entrada, Origem, Validade)
    lotes_planilha = [
        ("BIOCLIN / LOTE: 24015", 100, "2026-06-03", "Almoxarifado Central", "2025-11-30"),
        ("BIOCLIN / LOTE: 24016", 50, "2026-06-03", "Almoxarifado Central", "2025-11-30"),
        ("BIOCLIN / LOTE: 24017", 10, "2026-06-03", "Almoxarifado Central", "2025-12-31"),
        ("BIOCLIN / LOTE: 24020", 30, "2026-06-03", "Almoxarifado Central", "2026-01-31"),
        ("BIOCLIN / LOTE: 24022", 80, "2026-06-03", "Almoxarifado Central", "2026-02-28"),
        ("BIOCLIN / LOTE: 24025", 120, "2026-06-03", "Almoxarifado Central", "2026-03-31")
    ]

    # Step 3: Inserir cada lote no banco de dados
    lotes_inseridos = 0
    for origem_lote, saldo, data_entrada, origem, validade in lotes_planilha:
        # Verifica se este lote específico já não foi inserido antes para não duplicar
        cursor.execute("SELECT id FROM lotes WHERE teste_id = ? AND origem = ? AND validade = ?", 
                       (teste_id, origem_lote, validade))
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO lotes (teste_id, quantidade_inicial, quantidade_atual, data_entrada, origem, validade)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (teste_id, saldo, saldo, data_entrada, origem_lote, validade))
            lotes_inseridos += 1

    conn.commit()
    conn.close()
    
    print(f"🎉 Sucesso! {lotes_inseridos} novos lotes de Leishmaniose foram lançados no sistema.")

if __name__ == "__main__":
    lançar_dados_planilha()
