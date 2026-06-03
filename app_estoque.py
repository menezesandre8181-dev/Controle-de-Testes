import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha) ---
st.set_page_config(page_title="Vigilância em Saúde - Login", page_icon="🔒", layout="wide")

def realizar_login():
    # Recupera a senha dos segredos (Streamlit Secrets)
    senha_correta = st.secrets["PASSWORD_SISTEMA"]
    
    # Criamos 3 colunas para centralizar o formulário no meio da tela
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.write("") # Espaço em branco no topo para empurrar o bloco para baixo
        st.write("")
        
        # Um contêiner com borda simulada para parecer um cartão de login
        with st.container(border=True):
            # Cabeçalho elegante
            st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🔒 Acesso Restrito</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; margin-bottom: 25px;'>Vigilância em Saúde — Controle de Estoque</p>", unsafe_allow_html=True)
            
            # Campo de entrada de dados integrado
            senha = st.text_input("Digite a senha de acesso para continuar:", type="password", placeholder="Sua senha secreta")
            
            st.write("") # Pequeno espaçamento antes do botão
            
            # Botão centralizado ou expandido que ocupa a largura total
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                if senha == senha_correta:
                    st.session_state["autenticado"] = True
                    st.success("Autenticado com sucesso! Carregando...")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Verifique os caracteres e tente novamente.")

# --- CONTROLE DE SESSÃO ---
if "autenticado" not in st.session_state: 
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    realizar_login()
    st.stop() # Interrompe a execução do restante do app se não logar


# ==============================================================================
# SE O USUÁRIO FOR AUTENTICADO, O RESTANTE DO SEU CÓDIGO RODA DAQUI PARA BAIXO
# ==============================================================================

# --- FUNÇÕES DO BANCO DE DADOS ---
def obter_conexao():
    return sqlite3.connect('estoque_testes_v5.db')

def inicializar_banco():
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS testes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            unidades_por_caixa INTEGER NOT NULL DEFAULT 25
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unidades_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teste_id INTEGER,
            quantidade_inicial INTEGER NOT NULL,
            quantidade_atual INTEGER NOT NULL,
            data_entrada TEXT NOT NULL,
            origem TEXT,
            validade TEXT NOT NULL,
            FOREIGN KEY (teste_id) REFERENCES testes(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            unidade_id INTEGER,
            quantidade_saida INTEGER NOT NULL,
            data_saida TEXT NOT NULL,
            FOREIGN KEY (lote_id) REFERENCES lotes(id),
            FOREIGN KEY (unidade_id) REFERENCES unidades_saude(id)
        )
    ''')
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM testes")
    if cursor.fetchone()[0] == 0:
        dados_vigilancia = [
            ("COVID + INFLUENZA", 20, [(2840, "31/10/2027")]),
            ("SÍFILIS", 25, [(150, "31/03/2027"), (675, "31/05/2027")]),
            ("DENGUE NS1", 25, [(475, "30/06/2026")]),
            ("COVID", 25, [(1300, "21/03/2026")]),
            ("HEPATITE C", 25, [(225, "31/01/2027"), (300, "31/03/2027"), (250, "31/05/2027")]),
            ("HEPATITE B", 25, [(300, "31/10/2026"), (175, "30/09/2026")]),
            ("HIV 1/2 + SÍFILIS", 25, [(175, "31/12/2026"), (200, "13/12/2026"), (200, "10/12/2026")]),
            ("HIV 1 E 2", 25, [(350, "31/01/2027"), (300, "31/03/2027")]),
            ("HIV 1(MO) E 2", 10, [(50, "31/01/2027"), (10, "30/06/2027")]),
            ("LEISHMANIOSE CANINA", 20, [(280, "30/06/2026")])
        ]
        
        data_hoje = datetime.today().strftime('%d/%m/%Y')
        
        for nome_t, unid_cx, lotes in dados_vigilancia:
            cursor.execute("INSERT INTO testes (nome, unidades_por_caixa) VALUES (?, ?)", (nome_t, unid_cx))
            t_id = cursor.lastrowid
            
            for qtd, validade in lotes:
                cursor.execute('''
                    INSERT INTO lotes (teste_id, quantidade_inicial, quantidade_atual, data_entrada, origem, validade)
                    VALUES (?, ?, ?, ?, 'SEMSA', ?)
                ''', (t_id, qtd, qtd, data_hoje, validade))
                
        unidades_padrao = ["ESF XV", "ESF CAMPO GRANDE", "ESF KIMURA", "PRONTO SOCORRO"]
        for uni in unidades_padrao:
            cursor.execute("INSERT OR IGNORE INTO unidades_saude (nome) VALUES (?)", (uni,))
            
        conn.commit()
    conn.close()

# Inicializa banco
inicializar_banco()

# --- MENU LATERAL (Navegação) ---
st.sidebar.title("⚙️ ESTOQUE V5")
st.sidebar.write("Usuário: **Operador Vigilância**")

# Botão de Logoff no menu lateral
if st.sidebar.button("🔒 Sair do Sistema"):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    [
        "📊 Painel Geral & Alertas",
        "➕ Cadastrar Novo Teste",
        "🏢 Cadastrar Unidade (Posto)",
        "📥 Entrada de Carga (Lote)",
        "📤 Enviar para Unidade",
        "🔍 Histórico por Unidade"
    ]
)

# ==========================================
# TELA 1: DASHBOARD
# ==========================================
if menu == "📊 Painel Geral & Alertas":
    st.title("Painel Geral - Vigilância em Saúde")
    
    st.subheader("⚠️ ALERTAS DE VENCIMENTO (Próximos 90 dias)")
    
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.nome, l.validade, l.quantidade_atual 
        FROM lotes l 
        JOIN testes t ON l.teste_id = t.id 
        WHERE l.quantidade_atual > 0
    ''')
    
    alertas_encontrados = 0
    hoje = datetime.today()
    limite_alerta = hoje + timedelta(days=90)

    for nome, validade_str, qtd in cursor.fetchall():
        try:
            data_val = datetime.strptime(validade_str, "%d/%m/%Y")
            if data_val <= limite_alerta:
                dias_restantes = (data_val - hoje).days
                if dias_restantes < 0:
                    st.error(f"• **{nome}**: Lote com {qtd} un. [VENCIDO] - Validade: {validade_str}")
                elif dias_restantes < 30:
                    st.error(f"• **{nome}**: Lote com {qtd} un. [Vence em {dias_restantes} dias] - Validade: {validade_str}")
                else:
                    st.warning(f"• **{nome}**: Lote com {qtd} un. [Vence em {dias_restantes} dias] - Validade: {validade_str}")
                alertas_encontrados += 1
        except:
            pass

    if alertas_encontrados == 0:
        st.success("✓ Todos os lotes ativos estão com validades seguras.")
        
    st.markdown("---")
    
    st.subheader("Estoque Central Disponível")
    cursor.execute('''
        SELECT t.nome, SUM(l.quantidade_atual), t.unidades_por_caixa, MIN(l.validade)
        FROM testes t
        LEFT JOIN lotes l ON t.id = l.teste_id
        WHERE l.quantidade_atual > 0
        GROUP BY t.nome
        ORDER BY t.nome ASC
    ''')
    
    dados_tabela = []
    for nome, total_un, por_caixa, min_val in cursor.fetchall():
        caixas_aprox = round(total_un / por_caixa, 1) if por_caixa else 0
        dados_tabela.append({
            "Especificação do Teste Rápido": nome,
            "Qtd. Caixas (Aprox.)": f"{caixas_aprox} cx",
            "Total Unidades Centrais": f"{total_un} un",
            "Vencimento mais Próximo": min_val
        })
    conn.close()
    
    if dados_tabela:
        df = pd.DataFrame(dados_tabela)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Não há itens no estoque no momento.")

# ==========================================
# TELA 2: CADASTRO DE TESTE
# ==========================================
elif menu == "➕ Cadastrar Novo Teste":
    st.title("Cadastrar Especificação de Teste")
    
    with st.form("form_cadastro_teste", clear_on_submit=True):
        nome_teste = st.text_input("Nome/Modelo do Teste:").strip().upper()
        padrao_caixa = st.number_input("Padrão de Unidades por Caixa:", min_value=1, value=25, step=1)
        btn_salvar = st.form_submit_button("Salvar Configuração")
        
        if btn_salvar:
            if not nome_teste:
                st.error("Por favor, preencha o nome do teste.")
            else:
                conn = obter_conexao()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO testes (nome, unidades_por_caixa) VALUES (?, ?)", (nome_teste, padrao_caixa))
                    conn.commit()
                    st.success(f"Teste '{nome_teste}' cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Esse teste já está cadastrado.")
                finally:
                    conn.close()

# ==========================================
# TELA 3: CADASTRO DE UNIDADE
# ==========================================
elif menu == "🏢 Cadastrar Unidade (Posto)":
    st.title("Cadastrar Unidade de Saúde (Destino)")
    
    with st.form("form_cadastro_unidade", clear_on_submit=True):
        nome_unidade = st.text_input("Nome Oficial da Unidade:").strip().upper()
        btn_salvar = st.form_submit_button("Cadastrar Local")
        
        if btn_salvar:
            if not nome_unidade:
                st.error("Por favor, digite o nome do local.")
            else:
                conn = obter_conexao()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO unidades_saude (nome) VALUES (?)", (nome_unidade,))
                    conn.commit()
                    st.success(f"Unidade '{nome_unidade}' cadastrada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Esta unidade já está cadastrada.")
                finally:
                    conn.close()

# ==========================================
# TELA 4: ENTRADA DE LOTE
# ==========================================
elif menu == "📥 Entrada de Carga (Lote)":
    st.title("Registrar Entrada de Lote")
    
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, unidades_por_caixa FROM testes ORDER BY nome ASC")
    dict_testes = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    
    if not dict_testes:
        st.warning("Cadastre um teste primeiro na aba correspondente!")
    else:
        teste_selecionado = st.selectbox("Selecione o Teste:", list(dict_testes.keys()))
        origem = st.text_input("Origem/Fornecedor:", value="SEMSA").strip().upper()
        
        col1, col2 = st.columns(2)
        with col1:
            caixas = st.number_input("Quantidade de Caixas:", min_value=0.0, step=0.5, value=0.0)
        with col2:
            fator = dict_testes[teste_selecionado]
            total_unidades = int(caixas * fator)
            st.text_input("Total em Unidades (Calculado automaticamente):", value=str(total_unidades), disabled=True)
            
        validade_data = st.date_input("Data de Validade:", min_value=datetime.today())
        
        if st.button("Efetuar Entrada"):
            if caixas <= 0 or not origem:
                st.error("Preencha a quantidade de caixas e a origem corretamente.")
            else:
                validade_formatada = validade_data.strftime('%d/%m/%Y')
                data_atual = datetime.today().strftime('%d/%m/%Y')
                
                conn = obter_conexao()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM testes WHERE nome = ?", (teste_selecionado,))
                t_id = cursor.fetchone()[0]
                
                cursor.execute('''
                    INSERT INTO lotes (teste_id, quantidade_inicial, quantidade_atual, data_entrada, origem, validade) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (t_id, total_unidades, total_unidades, data_atual, origem, validade_formatada))
                conn.commit()
                conn.close()
                st.success(f"Lote de entrada com {total_unidades} unidades adicionado com sucesso!")

# ==========================================
# TELA 5: SAÍDA DE MATERIAL
# ==========================================
elif menu == "📤 Enviar para Unidade":
    st.title("Enviar Carga para Unidade de Saúde")
    
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, unidades_por_caixa FROM testes ORDER BY nome ASC")
    dict_testes = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT nome FROM unidades_saude ORDER BY nome ASC")
    lista_unidades = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not dict_testes or not lista_unidades:
        st.warning("Certifique-se de ter Testes e Unidades de Saúde cadastrados primeiro.")
    else:
        teste_selecionado = st.selectbox("Selecione o Teste:", list(dict_testes.keys()))
        unidade_destino = st.selectbox("Selecione a Unidade de Destino:", lista_unidades)
        
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT l.validade FROM lotes l 
            JOIN testes t ON l.teste_id = t.id
            WHERE t.nome = ? AND l.quantidade_atual > 0
            ORDER BY l.validade ASC
        ''', (teste_selecionado,))
        validades = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not validades:
            st.error("🚨 NÃO HÁ ESTOQUE DISPONÍVEL PARA ESTE TESTE!")
        else:
            validade_selecionada = st.selectbox("Selecione a Validade do Lote Disponível:", validades)
            
            col1, col2 = st.columns(2)
            with col1:
                caixas_saida = st.number_input("Quantidade de Caixas a Enviar:", min_value=0.0, step=0.5, value=0.0)
            with col2:
                fator = dict_testes[teste_selecionado]
                qtd_solicitada = int(caixas_saida * fator)
                st.text_input("Total em Unidades a Baixar:", value=str(qtd_solicitada), disabled=True)
                
            if st.button("Dar Baixa e Enviar"):
                if qtd_solicitada <= 0:
                    st.error("A quantidade deve ser maior que zero.")
                else:
                    conn = obter_conexao()
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT l.id, l.quantidade_atual FROM lotes l JOIN testes t ON l.teste_id = t.id
                        WHERE t.nome = ? AND l.validade = ? AND l.quantidade_atual > 0
                        ORDER BY l.id ASC
                    ''', (teste_selecionado, validade_selecionada))
                    lote = cursor.fetchone()
                    
                    if not lote:
                        st.error("Lote não encontrado ou zerado.")
                    else:
                        lote_id, qtd_atual = lote
                        if qtd_atual < qtd_solicitada:
                            st.error(f"Saldo insuficiente no lote! Este lote possui apenas {qtd_atual} unidades (você pediu {qtd_solicitada}).")
                        else:
                            data_atual = datetime.today().strftime('%d/%m/%Y')
                            
                            cursor.execute("SELECT id FROM unidades_saude WHERE nome = ?", (unidade_destino,))
                            unidade_id = cursor.fetchone()[0]
                            
                            cursor.execute("UPDATE lotes SET quantidade_atual = ? WHERE id = ?", (qtd_atual - qtd_solicitada, lote_id))
                            cursor.execute("INSERT INTO movimentacoes (lote_id, unidade_id, quantidade_saida, data_saida) VALUES (?, ?, ?, ?)", 
                                           (lote_id, unidade_id, qtd_solicitada, data_atual))
                            conn.commit()
                            st.success(f"Sucesso! Baixa efetuada. {qtd_solicitada} un. enviadas para {unidade_destino}.")
                    conn.close()

# ==========================================
# TELA 6: HISTÓRICO DAS UNIDADES
# ==========================================
elif menu == "🔍 Histórico por Unidade":
    st.title("Histórico de Cargas Enviadas para as Unidades")
    
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM unidades_saude ORDER BY nome ASC")
    unidades = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not unidades:
        st.info("Nenhuma unidade cadastrada.")
    else:
        unidade_selecionada = st.selectbox("Selecione a Unidade para Rastrear:", unidades)
        
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.nome, m.quantidade_saida, l.validade, m.data_saida
            FROM movimentacoes m
            JOIN unidades_saude u ON m.unidade_id = u.id
            JOIN lotes l ON m.lote_id = l.id
            JOIN testes t ON l.teste_id = t.id
            WHERE u.nome = ?
            ORDER BY m.id DESC
        ''', (unidade_selecionada,))
        
        historico = cursor.fetchall()
        conn.close()
        
        if historico:
            df_hist = pd.DataFrame(historico, columns=["Teste Entregue", "Qtd (Unidades)", "Validade do Lote", "Data do Envio"])
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nenhum envio registrado para {unidade_selecionada} até o momento.")
