import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Vigilância em Saúde - Estoque", page_icon="⚙️", layout="wide")

# --- 2. CONEXÃO COM O BANCO DE DADOS ---
DATABASE_NAME = "estoque.db"

def obter_conexao():
    return sqlite3.connect(DATABASE_NAME)

# Funções auxiliares para tratamento de data (DD/MM/AAAA <-> AAAA-MM-DD)
def txt_para_data(data_txt):
    try:
        return datetime.strptime(data_txt.strip(), "%d/%m/%Y").date()
    except:
        try:
            return datetime.strptime(data_txt.strip(), "%Y-%m-%d").date()
        except:
            return datetime.today().date()

def data_para_txt(data_obj):
    return data_obj.strftime("%d/%m/%Y")


# --- 3. SISTEMA DE LOGIN SEGURO ---
def realizar_login():
    senha_correta = st.secrets["PASSWORD_SISTEMA"]
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
                if senha == senha_correta:
                    st.session_state["autenticado"] = True
                    st.success("Autenticado com sucesso! Carregando...")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Verifique os caracteres e tente novamente.")

if "autenticado" not in st.session_state: 
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    realizar_login()
    st.stop()


# --- 4. INICIALIZAÇÃO DO BANCO DE DADOS ---
def inicializar_banco():
    conn = obter_conexao()
    cursor = conn.cursor()
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


# --- 6. LÓGICA DAS TELAS ---

# --- TELA: PAINEL GERAL ---
if menu == "📊 Painel Geral":
    st.title("📊 Painel Geral de Estoque")
    
    # Alertas Baseados na Validade
    conn = obter_conexao()
    df_alertas = pd.read_sql('''
        SELECT t.nome, l.validade, l.quantidade_atual, t.unidades_por_caixa
        FROM lotes l JOIN testes t ON t.id = l.teste_id WHERE l.quantidade_atual > 0
    ''', conn)
    conn.close()
    
    hoje = datetime.today().date()
    limite_alerta = hoje + timedelta(days=30)
    
    alertas_vencidos = []
    alertas_proximos = []
    
    for _, row in df_alertas.iterrows():
        dt_val = txt_para_data(row['validade'])
        caixas_alerta = row['quantidade_atual'] / row['unidades_por_caixa']
        if dt_val < hoje:
            alertas_vencidos.append(f"❌ **{row['nome']}** — VENCIDO em {data_para_txt(dt_val)} ({caixas_alerta} cx disponíveis)")
        elif dt_val <= limite_alerta:
            alertas_proximos.append(f"⚠️ **{row['nome']}** — Vence em {data_para_txt(dt_val)} ({caixas_alerta} cx restantes)")
            
    if alertas_vencidos:
        with st.error("🚨 PRODUTOS VENCIDOS NO ESTOQUE DETECTADOS:"):
            for item in alertas_vencidos: st.write(item)
    if alertas_proximos:
        with st.warning("⏳ PRODUTOS COM VENCIMENTO PRÓXIMO (MENOS DE 30 DIAS):"):
            for item in alertas_proximos: st.write(item)
            
    st.write("### Saldos Atuais Disponíveis")
    conn = obter_conexao()
    query = '''
        SELECT t.nome as "Nome do Teste", 
               l.quantidade_atual as "Total Unidades", 
               t.unidades_por_caixa as "Un/Caixa",
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
        df['Qtd em Caixas'] = df['Total Unidades'] / df['Un/Caixa']
        df['Data de Validade'] = df['Data de Validade'].apply(lambda x: data_para_txt(txt_para_data(x)))
        
        colunas_ordenadas = ["Nome do Teste", "Qtd em Caixas", "Data de Validade"]
        st.dataframe(df[colunas_ordenadas], use_container_width=True, hide_index=True)


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
    st.title("📥 Lançar Entrada por Caixas")
    
    conn = obter_conexao()
    testes_cadastrados = pd.read_sql("SELECT id, nome, unidades_por_caixa FROM testes ORDER BY nome", conn)
    conn.close()
    
    if testes_cadastrados.empty:
        st.warning("Por favor, cadastre um Tipo de Teste antes de dar entrada em lotes.")
    else:
        dict_testes = dict(zip(testes_cadastrados['nome'], testes_cadastrados['id']))
        dict_unidades = dict(zip(testes_cadastrados['nome'], testes_cadastrados['unidades_por_caixa']))
        
        with st.form("form_entrada"):
            teste_selecionado = st.selectbox("Selecione o Teste:", list(dict_testes.keys()))
            st.info(f"ℹ️ Este teste está configurado para conter **{dict_unidades[teste_selecionado]} unidades por caixa**.")
            
            qtd_caixas = st.number_input("Quantidade de Caixas Fechadas que entraram:", min_value=0.1, value=1.0, step=1.0)
            data_entrada_opc = st.date_input("Data de Entrada no Almoxarifado:", value=datetime.today())
            validade_opc = st.date_input("Data de Validade do Produto:")
            
            if st.form_submit_button("Confirmar Entrada no Estoque", type="primary"):
                fator_conversao = dict_unidades[teste_selecionado]
                total_unidades_calculado = int(qtd_caixas * fator_conversao)
                
                conn = obter_conexao()
                cursor = conn.cursor()
                # Salva como 'ESTOQUE GERAL' no campo de origem do banco apenas para manter a integridade da tabela
                cursor.execute('''
                    INSERT INTO lotes (teste_id, quantidade_inicial, quantidade_atual, data_entrada, origem, validade)
                    VALUES (?, ?, ?, ?, 'ESTOQUE GERAL', ?)
                ''', (dict_testes[teste_selecionado], total_unidades_calculado, total_unidades_calculado, 
                      str(data_entrada_opc), str(validade_opc)))
                conn.commit()
                conn.close()
                st.success(f"🎉 Lançamento realizado! {qtd_caixas} caixas ({total_unidades_calculado} unidades) inseridas com sucesso.")


# --- TELA: SAÍDA (ORDENADO POR VENCIMENTO, SEM CAMPO DE LOTE) ---
elif menu == "📤 Saída (Distribuição)":
    st.title("📤 Registrar Saída por Número de Caixas")
    
    conn = obter_conexao()
    lotes_disponiveis = pd.read_sql('''
        SELECT l.id, t.nome, l.validade, l.quantidade_atual, t.unidades_por_caixa
        FROM lotes l 
        JOIN testes t ON t.id = l.teste_id 
        WHERE l.quantidade_atual > 0
        ORDER BY l.validade ASC
    ''', conn)
    unidades = pd.read_sql("SELECT id, nome FROM unidades_saude ORDER BY nome", conn)
    conn.close()
    
    if lotes_disponiveis.empty or unidades.empty:
        st.warning("Certifique-se de ter testes em estoque e Unidades de Saúde cadastradas para realizar saídas.")
    else:
        listagem_lotes_texto = []
        for _, r in lotes_disponiveis.iterrows():
            saldo_caixas = r['quantidade_atual'] / r['unidades_por_caixa']
            data_formatada = data_para_txt(txt_para_data(r['validade']))
            listagem_lotes_texto.append(f"{r['nome']} — Vence em: {data_formatada} | Saldo: {saldo_caixas} caixas")
            
        with st.form("form_saida"):
            lote_escolhido = st.selectbox("Selecione o Produto (Mais próximos do vencimento listados primeiro):", listagem_lotes_texto)
            unidade_escolhida = st.selectbox("Selecione a Unidade de Destino:", unidades['nome'].tolist())
            
            qtd_caixas_saida = st.number_input("Quantidade de Caixas a enviar:", min_value=0.01, value=1.0, step=0.5)
            data_saida_opc = st.date_input("Data da Transferência:", value=datetime.today())
            
            if st.form_submit_button("Confirmar Envio", type="primary"):
                posicao = listagem_lotes_texto.index(lote_escolhido)
                lote_id_real = int(lotes_disponiveis.iloc[posicao]['id'])
                unidades_por_caixa_fator = int(lotes_disponiveis.iloc[posicao]['unidades_por_caixa'])
                saldo_atual_unidades = int(lotes_disponiveis.iloc[posicao]['quantidade_atual'])
                
                total_saida_unidades = int(qtd_caixas_saida * unidades_por_caixa_fator)
                unidade_id_real = int(unidades[unidades['nome'] == unidade_escolhida]['id'].iloc[0])
                
                if total_saida_unidades <= saldo_atual_unidades:
                    conn = obter_conexao()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE lotes SET quantidade_atual = quantidade_atual - ? WHERE id = ?", (total_saida_unidades, lote_id_real))
                    
                    try:
                        cursor.execute('''
                            INSERT INTO movimentacoes (lote_id, unidade_id, quantidade_saida, data_saida)
                            VALUES (?, ?, ?, ?)
                        ''', (lote_id_real, unidade_id_real, total_saida_unidades, str(data_saida_opc)))
                    except:
                        cursor.execute('''
                            INSERT INTO movimentacoes (lote_id, unity_id, quantidade_saida, data_saida)
                            VALUES (?, ?, ?, ?)
                        ''', (lote_id_real, unidade_id_real, total_saida_unidades, str(data_saida_opc)))
                        
                    conn.commit()
                    conn.close()
                    st.success(f"🎉 Distribuição concluída! {qtd_caixas_saida} caixa(s) foram enviadas para {unidade_escolhida}.")
                    st.rerun()
                else:
                    caixas_maximas = saldo_atual_unidades / unidades_por_caixa_fator
                    st.error(f"Estoque insuficiente. Este produto possui apenas {caixas_maximas} caixas com essa data de validade.")


# --- TELA: HISTÓRICO DE MOVIMENTAÇÕES ---
elif menu == "🔍 Histórico de Movimentações":
    st.title("🔍 Histórico de Movimentações (Saídas)")
    
    conn = obter_conexao()
    query = '''
        SELECT m.data_saida as "Data da Saída", t.nome as "Teste", 
               u.nome as "Destino / Unidade", 
               m.quantidade_saida as "Unidades", t.unidades_por_caixa as "Fator"
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
        df_mov['Caixas Enviadas'] = df_mov['Unidades'] / df_mov['Fator']
        df_mov['Data da Saída'] = df_mov['Data da Saída'].apply(lambda x: data_para_txt(txt_para_data(x)))
        
        cols_viz = ["Data da Saída", "Teste", "Destino / Unidade", "Caixas Enviadas"]
        st.dataframe(df_mov[cols_viz], use_container_width=True, hide_index=True)


# --- TELA: EDITAR E APAGAR ---
elif menu == "✏️ Editar e Apagar":
    st.title("✏️ Gerenciar e Modificar Registros")
    
    aba_lotes, aba_testes = st.tabs(["📦 Estoque e Validades", "🧪 Nomes dos Testes"])

    with aba_lotes:
        conn = obter_conexao()
        query_lotes = """
            SELECT l.id, t.nome as teste, l.quantidade_atual, l.validade, t.unidades_por_caixa 
            FROM lotes l JOIN testes t ON t.id = l.teste_id ORDER BY t.nome, l.validade
        """
        df_lotes = pd.read_sql(query_lotes, conn)
        conn.close()

        if df_lotes.empty:
            st.warning("Nenhum registro localizado no banco de dados.")
        else:
            # Lista as opções de edição ocultando o lote e focando no nome e validade
            lista_opcoes = [f"ID {row['id']} - {row['teste']} (Vence em: {data_para_txt(txt_para_data(row['validade']))}) | Saldo: {row['quantidade_atual']/row['unidades_por_caixa']} cx" for _, row in df_lotes.iterrows()]
            selecionado = st.selectbox("Selecione o registro que deseja gerenciar:", lista_opcoes, key="sel_lote")
            
            lote_id = int(selecionado.split(" ")[1])
            dados_lote = df_lotes[df_lotes['id'] == lote_id].iloc[0]

            col_edit, col_del = st.columns([2, 1])

            with col_edit:
                with st.container(border=True):
                    st.subheader("📝 Editar Dados")
                    nova_qtd = st.number_input("Ajustar Quantidade Atual (Unidades brutas):", value=int(dados_lote['quantidade_atual']), min_value=0)
                    
                    data_convertida_exibir = data_para_txt(txt_para_data(dados_lote['validade']))
                    nova_validade_txt = st.text_input("Data de Validade (DD/MM/AAAA):", value=data_convertida_exibir)
                    
                    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                        data_bd_salvar = str(txt_para_data(nova_validade_txt))
                        
                        conn = obter_conexao()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE lotes SET quantidade_atual = ?, validade = ? WHERE id = ?
                        """, (nova_qtd, data_bd_salvar, lote_id))
                        conn.commit()
                        conn.close()
                        st.success("Registro atualizado com sucesso!")
                        st.rerun()

            with col_del:
                with st.container(border=True):
                    st.subheader("⚠️ Exclusão Definitiva")
                    st.write("Apagar o registro removerá permanentemente o lote de estoque do sistema.")
                    
                    confirmar_lote = st.checkbox("Confirmo que quero apagar este registro permanentemente.", key="conf_lote")
                    if st.button("🗑️ Deletar Registro", type="secondary", use_container_width=True, disabled=not confirmar_lote):
                        conn = obter_conexao()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM movimentacoes WHERE lote_id = ?", (lote_id,))
                        cursor.execute("DELETE FROM lotes WHERE id = ?", (lote_id,))
                        conn.commit()
                        conn.close()
                        st.success("Removido completamente!")
                        st.rerun()

    with aba_testes:
        conn = obter_conexao()
        df_testes = pd.read_sql("SELECT id, nome, unidades_por_caixa FROM testes ORDER BY nome", conn)
        conn.close()

        if df_testes.empty:
            st.warning("Nenhum tipo de testado cadastrado.")
        else:
            lista_testes = [f"ID {row['id']} - {row['nome']}" for _, row in df_testes.iterrows()]
            selecionado_teste = st.selectbox("Selecione o tipo de teste:", lista_testes, key="sel_teste")
            
            teste_id = int(selecionado_teste.split(" ")[1])
            dados_teste = df_testes[df_testes['id'] == teste_id].iloc[0]

            col_t_edit, col_t_del = st.columns([2, 1])

            with col_t_edit:
                with st.container(border=True):
                    st.subheader("📝 Editar Configurações")
                    novo_nome = st.text_input("Nome do Teste Clínico:", value=dados_teste['nome']).upper()
                    novas_unidades = st.number_input("Unidades por Caixa Fechada:", value=int(dados_teste['unidades_por_caixa']), min_value=1)
                    
                    if st.button("💾 Salvar Alterações no Teste", type="primary", use_container_width=True):
                        conn = obter_conexao()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE testes SET nome = ?, unidades_por_caixa = ? WHERE id = ?", (novo_nome, novas_unidades, teste_id))
                        conn.commit()
                        conn.close()
                        st.success("Nome atualizado!")
                        st.rerun()

            with col_t_del:
                with st.container(border=True):
                    st.subheader("⚠️ Excluir Categoria")
                    confirmar_teste = st.checkbox("Confirmo que quero apagar esta categoria.", key="conf_teste")
                    if st.button("🗑️ Deletar Categoria", type="secondary", use_container_width=True, disabled=not confirmar_teste):
                        try:
                            conn = obter_conexao()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM testes WHERE id = ?", (teste_id,))
                            conn.commit()
                            conn.close()
                            st.success("Categoria excluída!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Erro: existem lotes vinculados a esta categoria. Remova-os primeiro.")
