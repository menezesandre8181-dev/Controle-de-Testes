import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA LINHA) ---
st.set_page_config(page_title="Vigilância em Saúde - Estoque", page_icon="⚙️", layout="wide")

# --- 2. CONEXÃO COM O BANCO DE DADOS ---
DATABASE_NAME = "estoque.db"

def obter_conexao():
    return sqlite3.connect(DATABASE_NAME)

# --- 3. SISTEMA DE LOGIN SEGURO (MÓDULO VISUAL NOVO) ---
def realizar_login():
    # Busca a senha cadastrada no painel Secrets do Streamlit
    senha_correta = st.secrets["PASSWORD_SISTEMA"]
    
    # Centralização do formulário em 3 colunas
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.write("") 
        st.write("")
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🔒 Acesso Restrito</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; margin-bottom: 25px;'>Vigilância em Saúde — Controle de Estoque</p>", unsafe_allow_html=True)
            
            senha = st.text_input("Digite a senha de acesso para continuar:", type="password", placeholder="Sua senha secreta")
            st.write("")
            
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                if Blackbox_check := (senha == senha_correta):
                    st.session_state["autenticado"] = True
                    st.success("Autenticado com sucesso! Carregando...")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Verifique os caracteres e tente novamente.")

# Controle de Sessão de Usuário
if "autenticado" not in st.session_state: 
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    realizar_login()
    st.stop() # Bloqueia o restante do app se não estiver logado


# --- 4. INICIALIZAÇÃO DO BANCO DE DADOS ---
def inicializar_banco():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Ativar suporte a chaves estrangeiras no SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS testes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        unidades_por_caixa INTEGER NOT NULL DEFAULT 25
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS unidades_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS lotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teste_id INTEGER,
        quantidade_inicial INTEGER NOT NULL,
        quantidade_atual INTEGER NOT NULL,
        data_entrada TEXT NOT NULL,
        origem TEXT,
        validade TEXT NOT NULL,
        FOREIGN KEY (teste_id) REFERENCES testes(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lote_id INTEGER,
        unidade_id INTEGER,
        quantidade_saida INTEGER NOT NULL,
        data_saida TEXT NOT NULL,
        FOREIGN KEY (lote_id) REFERENCES lotes(id),
        FOREIGN KEY (unidade_id) REFERENCES unidades_saude(id)
    )''')
    conn.commit()
    conn.close()

inicializar_banco()


# --- 5. ESTRUTURA DO MENU LATERAL ---
st.sidebar.title("⚙️ VIGILÂNCIA EM SAÚDE")
menu = st.sidebar.radio("Menu de Navegação", [
    "📊 Painel Geral", 
    "➕ Novo Teste", 
    "🏢 Nova Unidade", 
    "📥 Entrada de Estoque", 
    "📤 Saída (Distribuição)", 
    "🔍 Histórico de Movimentações",
    "✏️ Editar e Apagar"
])


# --- 6. LÓGICA DAS TELAS DO APP ---

# --- TELA: PAINEL GERAL ---
if menu == "📊 Painel Geral":
    st.title("📊 Painel Geral de Estoque")
    st.write("Visão consolidada dos saldos de testes disponíveis por lote e seus vencimentos.")
    
    conn = obter_conexao()
    query = '''
        SELECT t.nome as "Nome do Teste", l.origem as "Lote / Fabricante", 
               l.quantidade_atual as "Quantidade Atual (Unidades)", 
               (l.quantidade_atual / t.unidades_por_caixa) as "Qtd em Caixas",
               l.validade as "Data de Validade"
        FROM lotes l
        JOIN testes t ON t.id = l.teste_id
        WHERE l.quantidade_atual > 0
        ORDER BY l.validade ASC
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        st.info("O estoque está completamente vazio no momento.")
    else:
        # Mostra o painel interativo
        st.dataframe(df, use_container_width=True, hide_index=True)


# --- TELA: NOVO TESTE ---
elif menu == "➕ Novo Teste":
    st.title("➕ Cadastrar Novo Tipo de Teste")
    with st.form("form_novo_teste", clear_on_submit=True):
        nome = st.text_input("Nome do Teste Clínico (Ex: HIV, SÍFILIS, LEISHMANIOSE):").upper().strip()
        qtd_caixa = st.number_input("Quantidade de unidades que vêm dentro de cada Caixa:", min_value=1, value=25)
        
        if st.form_submit_button("Salvar Cadastro", type="primary"):
            if nome:
                conn = obter_conexao()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO testes (nome, unidades_por_caixa) VALUES (?, ?)", (nome, qtd_caixa))
                    conn.commit()
                    st.success(f"Teste '{nome}' cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Este teste já está cadastrado no sistema.")
                finally:
                    conn.close()
            else:
                st.warning("O nome do teste não pode ficar em branco.")


# --- TELA: NOVA UNIDADE ---
elif menu == "🏢 Nova Unidade":
    st.title("🏢 Cadastrar Nova Unidade de Saúde")
    with st.form("form_nova_unidade", clear_on_submit=True):
        nome_unidade = st.text_input("Nome do Posto / UBS / Hospital:").upper().strip()
        
        if st.form_submit_button("Salvar Unidade", type="primary"):
            if nome_unidade:
                conn = obter_conexao()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO unidades_saude (nome) VALUES (?)", (nome_unidade,))
                    conn.commit()
                    st.success(f"Unidade '{nome_unidade}' cadastrada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Esta unidade já está cadastrada no sistema.")
                finally:
                    conn.close()
            else:
                st.warning("O nome da unidade não pode ficar em branco.")


# --- TELA: ENTRADA DE ESTOQUE ---
elif menu == "📥 Entrada de Estoque":
    st.title("📥 Lançar Entrada de Lotes")
    
    conn = obter_conexao()
    testes_cadastrados = pd.read_sql("SELECT id, nome FROM testes ORDER BY nome", conn)
    conn.close()
    
    if testes_cadastrados.empty:
        st.warning("Por favor, cadastre um Tipo de Teste antes de dar entrada em lotes.")
    else:
        dict_testes = dict(zip(testes_cadastrados['nome'], testes_cadastrados['id']))
        
        with st.form("form_entrada"):
            teste_selecionado = st.selectbox("Selecione o Teste:", list(dict_testes.keys()))
            lote_fab = st.text_input("Lote / Fabricante (Ex: BIOCLIN / LOTE: 24015):").upper().strip()
            qtd_unidades = st.number_input("Quantidade Total de Unidades (Avulsas):", min_value=1, value=100)
            data_entrada = st.date_input("Data de Entrada no Almoxarifado:", value=datetime.today())
            validade = st.date_input("Data de Validade do Produto:")
            
            if st.form_submit_button("Confirmar Entrada no Estoque", type="primary"):
                if lote_fab:
                    conn = obter_conexao()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO lotes (teste_id, quantidade_inicial, quantidade_atual, data_entrada, origem, validade)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (dict_testes[teste_selecionado], qtd_unidades, qtd_unidades, str(data_entrada), lote_fab, str(validade)))
                    conn.commit()
                    conn.close()
                    st.success(f"Entrada registrada: {qtd_unidades} unidades adicionadas ao estoque!")
                else:
                    st.warning("Preencha a identificação do Lote/Fabricante.")


# --- TELA: SAÍDA (DISTRIBUIÇÃO) ---
elif menu == "📤 Saída (Distribuição)":
    st.title("📤 Registrar Saída para Unidade de Saúde")
    
    conn = obter_conexao()
    lotes_disponiveis = pd.read_sql('''
        SELECT l.id, t.nome || " (" || l.origem || ") - Saldo: " || l.quantidade_atual as info 
        FROM lotes l JOIN testes t ON t.id = l.teste_id WHERE l.quantidade_atual > 0
    ''', conn)
    unidades = pd.read_sql("SELECT id, nome FROM unidades_saude ORDER BY nome", conn)
    conn.close()
    
    if lotes_disponiveis.empty or unidades.empty:
        st.warning("Certifique-se de ter Lotes com saldo e Unidades de Saúde cadastradas para realizar saídas.")
    else:
        with st.form("form_saida"):
            lote_escolhido = st.selectbox("Selecione o Lote de Origem:", lotes_disponiveis['info'].tolist())
            unidade_escolhida = st.selectbox("Selecione a Unidade de Destino:", unidades['nome'].tolist())
            qtd_saida = st.number_input("Quantidade de Unidades a transferir:", min_value=1, value=10)
            data_saida = st.date_input("Data da Transferência:", value=datetime.today())
            
            if st.form_submit_button("Confirmar Envio", type="primary"):
                # Extrair o ID do lote da string descritiva anterior
                conn = obter_conexao()
                cursor = conn.cursor()
                
                # Pegar o ID do lote real
                lotes_df_reverso = pd.read_sql('SELECT id, quantidade_atual FROM lotes WHERE quantidade_atual > 0', conn)
                idx_selecionado = lotes_disponiveis['info'].tolist().index(lote_escolhido)
                lote_id_real = int(lotes_disponiveis.iloc[idx_selecionado]['id'])
                saldo_atual = int(lotes_df_reverso[lotes_df_reverso['id'] == lote_id_real]['quantidade_atual'].iloc[0])
                
                # Pegar o ID da unidade
                unidade_id_real = int(unidades[unidades['nome'] == unidade_escolhida]['id'].iloc[0])
                
                if qtd_saida <= saldo_atual:
                    # Deduz do estoque
                    cursor.execute("UPDATE lotes SET quantidade_atual = quantidade_atual - ? WHERE id = ?", (qtd_saida, lote_id_real))
                    # Grava no histórico
                    cursor.execute('''
                        INSERT INTO movimentacoes (lote_id, unidade_id, quantidade_saida, data_saida)
                        VALUES (?, ?, ?, ?)
                    ''', (lote_id_real, unidade_id_real, qtd_saida, str(data_saida)))
                    conn.commit()
                    st.success("Saída registrada com sucesso e estoque atualizado!")
                else:
                    st.error(f"Quantidade indisponível. O saldo atual deste lote é de apenas {saldo_atual} unidades.")
                conn.close()


# --- TELA: HISTÓRICO DE MOVIMENTAÇÕES ---
elif menu == "🔍 Histórico de Movimentações":
    st.title("🔍 Histórico de Movimentações (Saídas)")
    
    conn = obter_conexao()
    query = '''
        SELECT m.data_saida as "Data da Saída", t.nome as "Teste", 
               l.origem as "Lote de Origem", u.nome as "Destino / Unidade", 
               m.quantidade_saida as "Qtd Enviada (Unidades)"
        FROM movimentacoes m
        JOIN lotes l ON l.id = m.lote_id
        JOIN testes t ON t.id = l.teste_id
        JOIN unidades_saude u ON u.id = m.unidade_id
        ORDER BY m.data_saida DESC
    '''
    df_mov = pd.read_sql(query, conn)
    conn.close()
    
    if df_mov.empty:
        st.info("Nenhuma movimentação de saída foi registrada ainda.")
    else:
        st.dataframe(df_mov, use_container_width=True, hide_index=True)


# --- TELA NOVA: EDITAR E APAGAR (A QUE VOCÊ ME PEDIU) ---
elif menu == "✏️ Editar e Apagar":
    st.title("✏️ Gerenciar e Modificar Registros")
    st.write("Corrija dados digitados incorretamente ou remova registros do banco de dados.")

    # Criação das Sub-Abas internas
    aba_lotes, aba_testes = st.tabs(["📦 Lotes em Estoque", "🧪 Nomes dos Testes"])

    # GERENCIAMENTO DE LOTES (Saldos/Validades)
    with aba_lotes:
        conn = obter_conexao()
        query_lotes = """
            SELECT l.id, t.nome as teste, l.origem as lote_fabricante, 
                   l.quantidade_atual, l.validade 
            FROM lotes l
            JOIN testes t ON t.id = l.teste_id
            ORDER BY t.nome, l.validade
        """
        df_lotes = pd.read_sql(query_lotes, conn)
        conn.close()

        if df_lotes.empty:
            st.warning("Nenhum lote localizado no banco de dados.")
        else:
            lista_opcoes = [f"ID {row['id']} - {row['teste']} ({row['lote_fabricante']})" for _, row in df_lotes.iterrows()]
            selecionado = st.selectbox("Selecione o lote que deseja gerenciar:", lista_opcoes, key="sel_lote")
            
            lote_id = int(selecionado.split(" ")[1])
            dados_lote = df_lotes[df_lotes['id'] == lote_id].iloc[0]

            col_edit, col_del = st.columns([2, 1])

            with col_edit:
                with st.container(border=True):
                    st.subheader("📝 Editar Dados do Lote")
                    novo_lote_fab = st.text_input("Identificação do Lote:", value=dados_lote['lote_fabricante'])
                    nova_qtd = st.number_input("Ajustar Quantidade Atual (Unidades):", value=int(dados_lote['quantidade_atual']), min_value=0)
                    nova_validade = st.text_input("Data de Validade (AAAA-MM-DD):", value=dados_lote['validade'])
                    
                    if st.button("💾 Salvar Alterações no Lote", type="primary", use_container_width=True):
                        conn = obter_conexao()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE lotes 
                            SET origem = ?, quantidade_atual = ?, validade = ? 
                            WHERE id = ?
                        """, (novo_lote_fab, nova_qtd, nova_validade, lote_id))
                        conn.commit()
                        conn.close()
                        st.success("Lote atualizado com sucesso!")
                        st.rerun()

            with col_del:
                with st.container(border=True):
                    st.subheader("⚠️ Exclusão Definitiva")
                    st.write("Atenção! Apagar o lote removerá permanentemente os registros físicos do estoque.")
                    
                    confirmar_lote = st.checkbox("Confirmo que quero apagar este lote permanentemente.", key="conf_lote")
                    
                    if st.button("🗑️ Deletar Lote", type="secondary", use_container_width=True, disabled=not confirmar_lote):
                        conn = obter_conexao()
                        cursor = conn.cursor()
                        # Apaga movimentações dependentes para evitar erros de chave estrangeira
                        cursor.execute("DELETE FROM movimentacoes WHERE lote_id = ?", (lote_id,))
                        cursor.execute("DELETE FROM lotes WHERE id = ?", (lote_id,))
                        conn.commit()
                        conn.close()
                        st.success("Lote removido completamente do sistema!")
                        st.rerun()

    # GERENCIAMENTO DE TIPOS DE TESTES
    with aba_testes:
        conn = obter_conexao()
        df_testes = pd.read_sql("SELECT id, nome, unidades_por_caixa FROM testes ORDER BY nome", conn)
        conn.close()

        if df_testes.empty:
            st.warning("Nenhum tipo de teste cadastrado.")
        else:
            lista_testes = [f"ID {row['id']} - {row['nome']}" for _, row in df_testes.iterrows()]
            selecionado_teste = st.selectbox("Selecione o tipo de teste:", lista_testes, key="sel_teste")
            
            teste_id = int(selecionado_teste.split(" ")[1])
            dados_teste = df_testes[df_testes['id'] == teste_id].iloc[0]

            col_t_edit, col_t_del = st.columns([2, 1])

            with col_t_edit:
                with st.container(border=True):
                    st.subheader("📝 Editar Configurações do Teste")
                    novo_nome = st.text_input("Nome do Teste Clínico:", value=dados_teste['nome']).upper()
                    novas_unidades = st.number_input("Unidades por Caixa Fechada:", value=int(dados_teste['unidades_por_caixa']), min_value=1)
                    
                    if st.button("💾 Salvar Alterações no Teste", type="primary", use_container_width=True):
                        conn = obter_conexao()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE testes SET nome = ?, unidades_por_caixa = ? WHERE id = ?", (novo_nome, novas_unidades, teste_id))
                        conn.commit()
                        conn.close()
                        st.success("Nome do teste atualizado no sistema!")
                        st.rerun()

            with col_t_del:
                with st.container(border=True):
                    st.subheader("⚠️ Excluir Categoria")
                    st.write("Isso removerá a categoria do banco de dados se não houver lotes vinculados.")
                    
                    confirmar_teste = st.checkbox("Confirmo que quero apagar esta categoria.", key="conf_teste")
                    
                    if st.button("🗑️ Deletar Categoria", type="secondary", use_container_width=True, disabled=not confirmar_teste):
                        try:
                            conn = obter_conexao()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM testes WHERE id = ?", (teste_id,))
                            conn.commit()
                            conn.close()
                            st.success("Categoria excluída com sucesso!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Erro de Integridade: Você não pode deletar este teste porque já existem lotes físicos vinculados a ele. Delete os lotes primeiro na aba ao lado.")
