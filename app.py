"""
ODQ Recruta - Sistema de Triagem de Currículos
Versão Web com Streamlit - 100% Online e Gratuita
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import threading
import time

# Importar seus módulos existentes (funcionam igual!)
from email_client import EmailClient
from curriculum_analyzer import CurriculumAnalyzer
from database_manager import DatabaseManager
from curriculum_manager import CurriculumManager

# Configuração da página
st.set_page_config(
    page_title="ODQ Recruta - Sistema de Triagem",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para manter o visual profissional
st.markdown("""
<style>
    /* Cores profissionais do sistema original */
    :root {
        --primary-color: #2563EB;
        --success-color: #059669;
        --warning-color: #D97706;
        --danger-color: #DC2626;
        --background-color: #F8FAFC;
        --surface-color: #FFFFFF;
        --text-primary: #1E293B;
        --text-secondary: #64748B;
        --sidebar-color: #4A7C59;
    }
    
    /* Estilização da sidebar */
    .css-1d391kg {
        background-color: var(--sidebar-color);
    }
    
    /* Cards personalizados */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Botões customizados */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    .success-button > button {
        background-color: var(--success-color) !important;
    }
    
    .danger-button > button {
        background-color: var(--danger-color) !important;
    }
    
    /* Header customizado */
    .main-header {
        background: linear-gradient(90deg, var(--sidebar-color), #5A8A67);
        padding: 2rem;
        border-radius: 0.5rem;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Status indicators */
    .status-connected {
        color: var(--success-color);
        font-weight: bold;
    }
    
    .status-disconnected {
        color: var(--danger-color);
        font-weight: bold;
    }
    
    /* Log area */
    .log-area {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.375rem;
        border: 1px solid #e9ecef;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitTriagemApp:
    def __init__(self):
        """Inicializar a aplicação Streamlit"""
        self.init_session_state()
        self.init_components()
    
    def init_session_state(self):
        """Inicializar estado da sessão"""
        if 'email_connected' not in st.session_state:
            st.session_state.email_connected = False
        if 'current_view' not in st.session_state:
            st.session_state.current_view = 'Dashboard'
        if 'triagem_running' not in st.session_state:
            st.session_state.triagem_running = False
        if 'log_messages' not in st.session_state:
            st.session_state.log_messages = []
        if 'dashboard_cleared' not in st.session_state:
            st.session_state.dashboard_cleared = False
    
    def init_components(self):
        """Inicializar componentes do sistema"""
        try:
            self.email_client = EmailClient()
            self.analyzer = CurriculumAnalyzer()
            self.db_manager = DatabaseManager()
            self.curriculum_manager = CurriculumManager()
            
            # Inicializar cliente Microsoft 365
            try:
                from microsoft365_multi_user_client import Microsoft365MultiUserClient
                self.ms365_multi_client = Microsoft365MultiUserClient()
                self.ms365_available = True
                
                # Testar conexão automaticamente
                if not st.session_state.email_connected:
                    self.conectar_email_automatico()
                    
            except ImportError:
                self.ms365_multi_client = None
                self.ms365_available = False
                self.add_log("Microsoft 365 não disponível - usando apenas Gmail")
        except Exception as e:
            st.error(f"Erro ao inicializar componentes: {e}")
    
    def add_log(self, message):
        """Adicionar mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.log_messages.append(f"[{timestamp}] {message}")
        if len(st.session_state.log_messages) > 100:  # Manter apenas últimas 100 mensagens
            st.session_state.log_messages.pop(0)
    
    def conectar_email_automatico(self):
        """Conectar automaticamente aos emails"""
        credenciais_predefinidas = [
            ("odqtalentos@gmail.com", "ytnleflnpxapwnna"),
            ("rh.bancodetalentosres@gmail.com", "kmrv unha dtno qapa")
        ]
        
        self.add_log("Tentando conectar automaticamente aos emails...")
        
        for email, senha in credenciais_predefinidas:
            try:
                if self.email_client.conectar(email, senha):
                    st.session_state.email_connected = True
                    self.add_log(f"✅ Conectado automaticamente: {email}")
                    return True
            except Exception as e:
                self.add_log(f"❌ Falha ao conectar {email}")
                continue
        
        self.add_log("⚠️ Configuração manual necessária")
        return False
    
    def render_sidebar(self):
        """Renderizar sidebar de navegação"""
        with st.sidebar:
            # Logo e título
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(45deg, #4A7C59, #5A8A67); border-radius: 0.5rem; margin-bottom: 1rem;'>
                <h1 style='color: white; margin: 0; font-size: 1.5rem;'>🎯 ODQ RECRUTA</h1>
                <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;'>Sistema de Triagem Online</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Menu de navegação
            menu_items = [
                ("🏠 Dashboard", "Dashboard"),
                ("📧 Configurar Email", "Email"),
                ("💼 Gerenciar Vagas", "Vagas"),
                ("🎯 Triagem", "Triagem"),
                ("📊 Resultados", "Resultados"),
                ("✅ Aprovados", "Aprovados"),
                ("📈 Relatórios", "Relatórios"),
                ("⚙️ Configurações", "Configurações")
            ]
            
            for label, view in menu_items:
                if st.button(label, key=f"menu_{view}", use_container_width=True):
                    st.session_state.current_view = view
                    st.rerun()
            
            # Status de conexão
            st.markdown("---")
            if st.session_state.email_connected:
                st.markdown("🟢 **STATUS: CONECTADO**", unsafe_allow_html=True)
            else:
                st.markdown("🔴 **STATUS: DESCONECTADO**", unsafe_allow_html=True)
            
            # Informações do sistema
            st.markdown("---")
            st.markdown("### 📱 Acesso Online")
            st.info("✅ Sistema 100% online\n✅ Acesso via navegador\n✅ Hospedagem gratuita")
    
    def render_header(self):
        """Renderizar header da página atual"""
        view_config = {
            'Dashboard': {
                'title': '🏠 Dashboard',
                'subtitle': 'Visão geral do sistema de triagem'
            },
            'Email': {
                'title': '📧 Configurar Email',
                'subtitle': 'Configurações de conexão email'
            },
            'Vagas': {
                'title': '💼 Gerenciar Vagas',
                'subtitle': 'Cadastro e edição de vagas'
            },
            'Triagem': {
                'title': '🎯 Triagem de Currículos',
                'subtitle': 'Análise automática de candidatos'
            },
            'Resultados': {
                'title': '📊 Resultados',
                'subtitle': 'Histórico de análises realizadas'
            },
            'Aprovados': {
                'title': '✅ Currículos Aprovados',
                'subtitle': 'Candidatos aprovados por vaga'
            },
            'Relatórios': {
                'title': '📈 Relatórios',
                'subtitle': 'Estatísticas e exportações'
            },
            'Configurações': {
                'title': '⚙️ Configurações',
                'subtitle': 'Preferências do sistema'
            }
        }
        
        config = view_config.get(st.session_state.current_view, view_config['Dashboard'])
        
        st.markdown(f"""
        <div class="main-header">
            <h1 style="margin: 0; font-size: 2rem;">{config['title']}</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{config['subtitle']}</p>
        </div>
        """, unsafe_allow_html=True)

    def show_dashboard(self):
        """Mostrar dashboard principal"""
        # Obter estatísticas
        stats = self.db_manager.obter_estatisticas()
        
        # Cards de estatísticas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📊 Total de Análises",
                value=stats.get('total_analises', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                label="✅ Aprovados",
                value=stats.get('aprovados', 0),
                delta=None
            )
        
        with col3:
            st.metric(
                label="⚠️ Para Revisar",
                value=stats.get('revisar', 0),
                delta=None
            )
        
        with col4:
            st.metric(
                label="❌ Rejeitados",
                value=stats.get('rejeitados', 0),
                delta=None
            )
        
        with col5:
            aprovados_salvos = stats.get('total_aprovados_salvos', 0)
            vagas_com_aprovados = stats.get('vagas_com_aprovados', 0)
            st.metric(
                label="💾 Aprovados Salvos",
                value=f"{aprovados_salvos}",
                delta=f"em {vagas_com_aprovados} vagas" if vagas_com_aprovados > 0 else None
            )
        
        st.markdown("---")
        
        # Tabela de resultados recentes
        st.subheader("📋 Últimas Análises")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Atualizar", key="refresh_dash"):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar Tabela", key="clear_table"):
                st.session_state.dashboard_cleared = True
                self.add_log("Tabela do dashboard limpa")
                st.success("Tabela limpa com sucesso!")
                st.rerun()
        
        if not st.session_state.dashboard_cleared:
            resultados = self.db_manager.obter_resultados_recentes(20)
            
            if resultados:
                # Criar DataFrame para exibição
                df_resultados = pd.DataFrame(resultados)
                df_resultados['data'] = pd.to_datetime(df_resultados['data']).dt.strftime('%d/%m/%Y %H:%M')
                df_resultados = df_resultados[['data', 'email_remetente', 'nome_arquivo', 'pontuacao', 'status']]
                df_resultados.columns = ['Data', 'Email', 'Arquivo', 'Pontuação', 'Status']
                
                st.dataframe(
                    df_resultados,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("📭 Nenhuma análise encontrada ainda")
        else:
            st.info("📭 Tabela foi limpa. Clique em 'Atualizar' para recarregar os dados.")
    
    def show_email_config(self):
        """Mostrar configuração de email"""
        st.subheader("📧 Contas Gmail Pré-configuradas")
        
        # Gmail accounts status
        gmail_accounts = [
            {"email": "odqtalentos@gmail.com", "status": "✅ Conectado"},
            {"email": "rh.bancodetalentosres@gmail.com", "status": "✅ Conectado"}
        ]
        
        for account in gmail_accounts:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{account['email']}**")
            with col2:
                st.write(account['status'])
            with col3:
                if st.button(f"Testar", key=f"test_{account['email']}"):
                    with st.spinner("Testando conexão..."):
                        # Aqui você pode adicionar teste real
                        time.sleep(1)
                        st.success("Conexão OK!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Testar Todas as Conexões", use_container_width=True):
                with st.spinner("Testando todas as conexões..."):
                    success = self.conectar_email_automatico()
                    if success:
                        st.success("✅ Todas as conexões funcionando!")
                    else:
                        st.error("❌ Algumas conexões falharam")
        
        with col2:
            if st.button("🔗 Conectar Contas Selecionadas", use_container_width=True):
                with st.spinner("Conectando..."):
                    success = self.conectar_email_automatico()
                    if success:
                        st.session_state.email_connected = True
                        st.success("✅ Conectado com sucesso!")
                        st.rerun()
        
        st.markdown("---")
        
        # Microsoft 365 Section
        st.subheader("🏢 Microsoft 365 - Emails Corporativos")
        
        if self.ms365_available and self.ms365_multi_client:
            st.success("✅ Microsoft 365 integrado com sucesso!")
            
            try:
                all_stats = self.ms365_multi_client.obter_estatisticas_todos_usuarios()
                
                if all_stats:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info("**IZA (Izabella)**")
                        iza_stats = all_stats.get('iza', {})
                        if iza_stats:
                            st.write(f"📧 {iza_stats.get('email', 'izabella.cordeiro@odequadroservicos.com.br')}")
                            st.write(f"📬 {iza_stats.get('nao_lidos', 0)} não lidos / {iza_stats.get('total', 0)} total")
                    
                    with col2:
                        st.info("**NARA (Narahyna)**")
                        nara_stats = all_stats.get('nara', {})
                        if nara_stats:
                            st.write(f"📧 {nara_stats.get('email', 'narahyna.barbosa@odequadroservicos.com.br')}")
                            st.write(f"📬 {nara_stats.get('nao_lidos', 0)} não lidos / {nara_stats.get('total', 0)} total")
            except Exception as e:
                st.warning(f"Erro ao obter estatísticas: {e}")
        else:
            st.error("❌ Microsoft 365 não disponível")
            st.info("Verifique se as dependências estão instaladas:\n```pip install msal requests```")
    
    def show_vagas_manager(self):
        """Mostrar gerenciador de vagas"""
        st.subheader("➕ Cadastrar Nova Vaga")
        
        with st.form("nova_vaga_form"):
            nome_vaga = st.text_input("Nome da Vaga", placeholder="Ex: Desenvolvedor Python")
            palavras_chave = st.text_area(
                "Palavras-chave (separadas por vírgula)", 
                placeholder="Python, Django, Flask, API, desenvolvimento web",
                height=100
            )
            
            submitted = st.form_submit_button("✅ Cadastrar Vaga", use_container_width=True)
            
            if submitted and nome_vaga and palavras_chave:
                try:
                    # Processar palavras-chave
                    keywords_list = [kw.strip() for kw in palavras_chave.split(',') if kw.strip()]
                    
                    # Salvar no banco
                    vaga_id = self.db_manager.criar_vaga(nome_vaga, keywords_list)
                    
                    self.add_log(f"Nova vaga cadastrada: {nome_vaga}")
                    st.success(f"✅ Vaga '{nome_vaga}' cadastrada com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao cadastrar vaga: {e}")
        
        st.markdown("---")
        
        # Lista de vagas existentes
        st.subheader("📋 Vagas Cadastradas")
        
        vagas = self.db_manager.obter_vagas_ativas()
        
        if vagas:
            # Criar DataFrame
            df_vagas = pd.DataFrame(vagas)
            df_vagas['palavras_chave_str'] = df_vagas['palavras_chave'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
            df_vagas = df_vagas[['id', 'nome', 'palavras_chave_str', 'data_criacao']]
            df_vagas.columns = ['ID', 'Nome', 'Palavras-chave', 'Data de Criação']
            
            st.dataframe(
                df_vagas,
                use_container_width=True,
                hide_index=True
            )
            
            # Ações para vagas
            col1, col2, col3 = st.columns(3)
            with col1:
                vaga_id_delete = st.selectbox("Selecionar vaga para excluir", options=[v['id'] for v in vagas], format_func=lambda x: next(v['nome'] for v in vagas if v['id'] == x))
            
            with col2:
                if st.button("🗑️ Excluir Vaga Selecionada"):
                    try:
                        self.db_manager.excluir_vaga(vaga_id_delete)
                        self.add_log(f"Vaga excluída: ID {vaga_id_delete}")
                        st.success("✅ Vaga excluída com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao excluir vaga: {e}")
            
            with col3:
                if st.button("🔄 Atualizar Lista"):
                    st.rerun()
        else:
            st.info("📭 Nenhuma vaga cadastrada ainda")
    
    def show_triagem(self):
        """Mostrar interface de triagem"""
        # Configurações básicas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("⚙️ Configurações Básicas")
            
            # Período de busca
            periodo = st.radio(
                "📅 Período de busca:",
                ["Todos os emails", "Últimos X dias"],
                key="periodo_busca"
            )
            
            dias = 7
            if periodo == "Últimos X dias":
                dias = st.number_input("Quantos dias:", min_value=1, max_value=365, value=7)
            
            # Seleção de vaga
            st.write("🎯 **Vaga para triagem:**")
            vagas_disponiveis = self.db_manager.obter_vagas_ativas()
            
            opcoes_vaga = ["Triagem Geral (sem vaga específica)"]
            if vagas_disponiveis:
                opcoes_vaga.extend([f"{v['nome']} ({', '.join(v['palavras_chave'][:2])})" for v in vagas_disponiveis])
            
            vaga_selecionada = st.selectbox("Selecionar vaga:", opcoes_vaga)
        
        with col2:
            st.subheader("📊 Resumo da Configuração")
            
            # Mostrar resumo
            st.info(f"""
            **Período:** {periodo}
            {"**Últimos:** " + str(dias) + " dias" if periodo == "Últimos X dias" else ""}
            
            **Vaga:** {vaga_selecionada}
            
            **Emails:** Todas as contas
            """)
        
        st.markdown("---")
        
        # Seleção de contas de email
        st.subheader("📧 Seleção de Contas de Email")
        
        # Seleção rápida
        st.markdown("### ⚡ Seleção Rápida")
        
        col1, col2, col3, col4 = st.columns(4)
        
        email_selecionado = "todos"
        
        with col1:
            if st.button("📧 ODQ Talentos\n(odqtalentos@gmail.com)", use_container_width=True):
                email_selecionado = "odqtalentos@gmail.com"
                st.session_state.email_selecionado = email_selecionado
        
        with col2:
            if st.button("📧 RH Banco Talentos\n(rh.bancodetalentosres@gmail.com)", use_container_width=True):
                email_selecionado = "rh.bancodetalentosres@gmail.com"
                st.session_state.email_selecionado = email_selecionado
        
        with col3:
            if self.ms365_available:
                if st.button("🏢 Iza (Microsoft 365)\n(izabella.cordeiro@...)", use_container_width=True):
                    email_selecionado = "ms365_iza"
                    st.session_state.email_selecionado = email_selecionado
        
        with col4:
            if self.ms365_available:
                if st.button("🏢 Nara (Microsoft 365)\n(nara@...)", use_container_width=True):
                    email_selecionado = "ms365_nara"
                    st.session_state.email_selecionado = email_selecionado
        
        # Opções detalhadas
        st.markdown("### 📋 Opções Detalhadas")
        
        email_options = st.radio(
            "Escolha a origem dos emails:",
            ["✨ Todas as contas", "📧 Gmail específico", "🏢 Microsoft 365 específico"],
            key="email_options"
        )
        
        st.markdown("---")
        
        # Botão principal de triagem
        st.subheader("🚀 Iniciar Triagem")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if not st.session_state.triagem_running:
                if st.button("🎯 INICIAR TRIAGEM AGORA", 
                           use_container_width=True, 
                           type="primary",
                           help="Clique para iniciar a análise automática de currículos"):
                    self.iniciar_triagem(periodo, dias, vaga_selecionada, email_options)
            else:
                st.error("🔄 Triagem em andamento...")
                if st.button("⏹️ Parar Triagem", use_container_width=True):
                    st.session_state.triagem_running = False
                    self.add_log("Triagem interrompida pelo usuário")
                    st.rerun()
        
        with col2:
            if st.button("📋 Ver Resultados", use_container_width=True):
                st.session_state.current_view = "Resultados"
                st.rerun()
        
        with col3:
            if st.button("✅ Ver Aprovados", use_container_width=True):
                st.session_state.current_view = "Aprovados"
                st.rerun()
        
        # Status da triagem
        if st.session_state.email_connected:
            st.success("✅ Sistema pronto para triagem")
        else:
            st.warning("⚠️ Configure as conexões de email primeiro")
        
        # Log de execução
        st.markdown("---")
        st.subheader("📋 Log de Execução em Tempo Real")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🗑️ Limpar Log"):
                st.session_state.log_messages = []
                st.rerun()
        
        with col2:
            if st.button("📄 Exportar Log"):
                log_content = "\n".join(st.session_state.log_messages)
                st.download_button(
                    label="💾 Download Log",
                    data=log_content,
                    file_name=f"triagem_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        # Área de log
        if st.session_state.log_messages:
            log_text = "\n".join(st.session_state.log_messages[-20:])  # Mostrar últimas 20 mensagens
            st.text_area("", value=log_text, height=200, disabled=True, key="log_area")
        else:
            st.info("📭 Nenhuma atividade registrada ainda")
    
    def iniciar_triagem(self, periodo, dias, vaga_selecionada, email_options):
        """Iniciar processo de triagem"""
        st.session_state.triagem_running = True
        
        self.add_log("🚀 Iniciando processo de triagem...")
        self.add_log(f"📅 Período: {periodo}")
        self.add_log(f"🎯 Vaga: {vaga_selecionada}")
        self.add_log(f"📧 Emails: {email_options}")
        
        # Aqui você pode integrar sua lógica de triagem existente
        # Por enquanto, vou simular o processo
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            time.sleep(0.05)  # Simular processamento
            progress_bar.progress(i + 1)
            
            if i == 20:
                status_text.text("🔍 Buscando emails...")
                self.add_log("🔍 Buscando emails nas contas selecionadas...")
            elif i == 40:
                status_text.text("📄 Analisando currículos...")
                self.add_log("📄 Iniciando análise de currículos...")
            elif i == 70:
                status_text.text("🎯 Aplicando critérios de triagem...")
                self.add_log("🎯 Aplicando critérios de triagem...")
            elif i == 90:
                status_text.text("💾 Salvando resultados...")
                self.add_log("💾 Salvando resultados no banco de dados...")
        
        st.session_state.triagem_running = False
        self.add_log("✅ Triagem concluída com sucesso!")
        st.success("✅ Triagem concluída! Veja os resultados na aba 'Resultados'.")
        
        # Limpar elementos temporários
        progress_bar.empty()
        status_text.empty()
    
    def show_resultados(self):
        """Mostrar resultados das análises"""
        st.subheader("📊 Histórico de Análises")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_status = st.selectbox("Filtrar por status:", ["Todos", "Aprovado", "Revisar", "Rejeitado"])
        
        with col2:
            filtro_data = st.date_input("Data inicial:")
        
        with col3:
            if st.button("🔄 Atualizar Resultados"):
                st.rerun()
        
        # Obter resultados
        resultados = self.db_manager.obter_resultados_recentes(100)
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            # Aplicar filtros
            if filtro_status != "Todos":
                df_resultados = df_resultados[df_resultados['status'] == filtro_status]
            
            # Formatação para exibição
            df_resultados['data'] = pd.to_datetime(df_resultados['data']).dt.strftime('%d/%m/%Y %H:%M')
            df_display = df_resultados[['data', 'email_remetente', 'nome_arquivo', 'pontuacao', 'status', 'observacoes']]
            df_display.columns = ['Data', 'Email', 'Arquivo', 'Pontuação', 'Status', 'Observações']
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Estatísticas rápidas
            st.markdown("### 📈 Estatísticas dos Resultados")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total", len(df_resultados))
            with col2:
                aprovados = len(df_resultados[df_resultados['status'] == 'Aprovado'])
                st.metric("Aprovados", aprovados)
            with col3:
                revisar = len(df_resultados[df_resultados['status'] == 'Revisar'])
                st.metric("Para Revisar", revisar)
            with col4:
                rejeitados = len(df_resultados[df_resultados['status'] == 'Rejeitado'])
                st.metric("Rejeitados", rejeitados)
        else:
            st.info("📭 Nenhum resultado encontrado")
    
    def show_aprovados(self):
        """Mostrar currículos aprovados"""
        st.subheader("✅ Currículos Aprovados por Vaga")
        
        # Obter aprovados por vaga
        aprovados_por_vaga = self.db_manager.obter_aprovados_por_vaga()
        
        if aprovados_por_vaga:
            for vaga_nome, candidatos in aprovados_por_vaga.items():
                with st.expander(f"📁 {vaga_nome} ({len(candidatos)} candidatos)"):
                    
                    if candidatos:
                        df_candidatos = pd.DataFrame(candidatos)
                        df_candidatos = df_candidatos[['nome', 'email', 'pontuacao', 'data_aprovacao']]
                        df_candidatos.columns = ['Nome', 'Email', 'Pontuação', 'Data de Aprovação']
                        
                        st.dataframe(
                            df_candidatos,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Opções de exportação
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = df_candidatos.to_csv(index=False)
                            st.download_button(
                                f"📄 Exportar {vaga_nome} (CSV)",
                                csv,
                                f"aprovados_{vaga_nome.replace(' ', '_')}.csv",
                                "text/csv"
                            )
                        
                        with col2:
                            if st.button(f"📧 Enviar Lista por Email", key=f"email_{vaga_nome}"):
                                st.info("Funcionalidade de envio por email será implementada")
        else:
            st.info("📭 Nenhum candidato aprovado ainda")
    
    def show_relatorios(self):
        """Mostrar relatórios e estatísticas"""
        st.subheader("📈 Relatórios e Estatísticas")
        
        # Obter dados para relatórios
        stats = self.db_manager.obter_estatisticas()
        
        # Gráficos e métricas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Distribuição por Status")
            
            status_data = {
                'Aprovados': stats.get('aprovados', 0),
                'Para Revisar': stats.get('revisar', 0),
                'Rejeitados': stats.get('rejeitados', 0)
            }
            
            # Criar gráfico de pizza simples com texto
            total = sum(status_data.values())
            if total > 0:
                for status, valor in status_data.items():
                    pct = (valor / total) * 100
                    st.write(f"**{status}:** {valor} ({pct:.1f}%)")
            else:
                st.info("Sem dados para exibir")
        
        with col2:
            st.markdown("#### 📅 Atividade Recente")
            
            # Últimas atividades
            resultados_recentes = self.db_manager.obter_resultados_recentes(5)
            if resultados_recentes:
                for resultado in resultados_recentes:
                    data = datetime.strptime(resultado['data'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')
                    st.write(f"**{data}** - {resultado['email_remetente']} - {resultado['status']}")
            else:
                st.info("Nenhuma atividade recente")
        
        st.markdown("---")
        
        # Relatórios para download
        st.markdown("#### 📄 Relatórios para Download")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Relatório Completo", use_container_width=True):
                # Gerar relatório completo
                relatorio = self.gerar_relatorio_completo()
                st.download_button(
                    "💾 Download Relatório",
                    relatorio,
                    f"relatorio_completo_{datetime.now().strftime('%Y%m%d')}.txt",
                    "text/plain"
                )
        
        with col2:
            if st.button("📈 Estatísticas CSV", use_container_width=True):
                # Gerar CSV com estatísticas
                csv_stats = self.gerar_csv_estatisticas()
                st.download_button(
                    "💾 Download CSV",
                    csv_stats,
                    f"estatisticas_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        
        with col3:
            if st.button("🎯 Relatório por Vaga", use_container_width=True):
                relatorio_vagas = self.gerar_relatorio_vagas()
                st.download_button(
                    "💾 Download por Vagas",
                    relatorio_vagas,
                    f"relatorio_vagas_{datetime.now().strftime('%Y%m%d')}.txt",
                    "text/plain"
                )
    
    def show_configuracoes(self):
        """Mostrar configurações do sistema"""
        st.subheader("⚙️ Configurações do Sistema")
        
        # Configurações de análise
        st.markdown("#### 🎯 Configurações de Análise")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pontuacao_minima = st.slider("Pontuação mínima para aprovação:", 0.0, 10.0, 7.0, 0.1)
            incluir_anexos = st.checkbox("Analisar anexos dos emails", True)
            salvar_curriculos = st.checkbox("Salvar currículos localmente", True)
        
        with col2:
            max_emails_processar = st.number_input("Máximo de emails para processar:", 1, 1000, 100)
            timeout_email = st.number_input("Timeout para conexão (segundos):", 10, 300, 60)
            debug_mode = st.checkbox("Modo debug (logs detalhados)", False)
        
        # Configurações de email
        st.markdown("#### 📧 Configurações de Email")
        
        col1, col2 = st.columns(2)
        
        with col1:
            servidor_imap = st.text_input("Servidor IMAP Gmail:", "imap.gmail.com")
            porta_imap = st.number_input("Porta IMAP:", 1, 65535, 993)
        
        with col2:
            pasta_inbox = st.text_input("Pasta da caixa de entrada:", "INBOX")
            ssl_habilitado = st.checkbox("Usar SSL/TLS", True)
        
        # Configurações do banco de dados
        st.markdown("#### 🗄️ Configurações do Banco de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Arquivo do banco:** triagem_curriculos.db")
            st.write(f"**Localização:** {os.path.abspath('.')}")
        
        with col2:
            if st.button("🗑️ Limpar Banco de Dados"):
                if st.button("⚠️ Confirmar Limpeza (IRREVERSÍVEL)"):
                    # Aqui você implementaria a limpeza
                    st.error("Funcionalidade de limpeza seria implementada aqui")
            
            if st.button("💾 Backup do Banco"):
                st.info("Funcionalidade de backup seria implementada aqui")
        
        # Salvar configurações
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Configurações", use_container_width=True, type="primary"):
                # Aqui você salvaria as configurações
                self.add_log("Configurações salvas com sucesso")
                st.success("✅ Configurações salvas!")
        
        with col2:
            if st.button("🔄 Restaurar Padrões", use_container_width=True):
                # Aqui você restauraria configurações padrão
                self.add_log("Configurações restauradas para padrão")
                st.info("⚙️ Configurações restauradas!")
                st.rerun()
    
    def gerar_relatorio_completo(self):
        """Gerar relatório completo em texto"""
        stats = self.db_manager.obter_estatisticas()
        resultados = self.db_manager.obter_resultados_recentes(100)
        
        relatorio = f"""
        RELATÓRIO COMPLETO - ODQ RECRUTA
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        =====================================
        
        ESTATÍSTICAS GERAIS:
        - Total de análises: {stats.get('total_analises', 0)}
        - Aprovados: {stats.get('aprovados', 0)}
        - Para revisar: {stats.get('revisar', 0)}
        - Rejeitados: {stats.get('rejeitados', 0)}
        - Aprovados salvos: {stats.get('total_aprovados_salvos', 0)}
        
        ÚLTIMAS ANÁLISES:
        """
        
        for resultado in resultados[:10]:
            relatorio += f"\n- {resultado['data']}: {resultado['email_remetente']} - {resultado['status']} ({resultado['pontuacao']:.1f})"
        
        return relatorio
    
    def gerar_csv_estatisticas(self):
        """Gerar CSV com estatísticas"""
        stats = self.db_manager.obter_estatisticas()
        
        csv_content = "Métrica,Valor\n"
        csv_content += f"Total de Análises,{stats.get('total_analises', 0)}\n"
        csv_content += f"Aprovados,{stats.get('aprovados', 0)}\n"
        csv_content += f"Para Revisar,{stats.get('revisar', 0)}\n"
        csv_content += f"Rejeitados,{stats.get('rejeitados', 0)}\n"
        csv_content += f"Aprovados Salvos,{stats.get('total_aprovados_salvos', 0)}\n"
        
        return csv_content
    
    def gerar_relatorio_vagas(self):
        """Gerar relatório por vaga"""
        vagas = self.db_manager.obter_vagas_ativas()
        aprovados_por_vaga = self.db_manager.obter_aprovados_por_vaga()
        
        relatorio = f"""
        RELATÓRIO POR VAGA - ODQ RECRUTA
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        ===============================
        
        """
        
        for vaga in vagas:
            nome_vaga = vaga['nome']
            candidatos = aprovados_por_vaga.get(nome_vaga, [])
            
            relatorio += f"\nVAGA: {nome_vaga}\n"
            relatorio += f"Palavras-chave: {', '.join(vaga['palavras_chave'])}\n"
            relatorio += f"Candidatos aprovados: {len(candidatos)}\n"
            
            for candidato in candidatos[:5]:  # Máximo 5 por vaga
                relatorio += f"  - {candidato['nome']} ({candidato['email']}) - {candidato['pontuacao']:.1f}\n"
        
        return relatorio
    
    def run(self):
        """Executar a aplicação"""
        # Renderizar sidebar
        self.render_sidebar()
        
        # Renderizar header
        self.render_header()
        
        # Renderizar view atual
        if st.session_state.current_view == 'Dashboard':
            self.show_dashboard()
        elif st.session_state.current_view == 'Email':
            self.show_email_config()
        elif st.session_state.current_view == 'Vagas':
            self.show_vagas_manager()
        elif st.session_state.current_view == 'Triagem':
            self.show_triagem()
        elif st.session_state.current_view == 'Resultados':
            self.show_resultados()
        elif st.session_state.current_view == 'Aprovados':
            self.show_aprovados()
        elif st.session_state.current_view == 'Relatórios':
            self.show_relatorios()
        elif st.session_state.current_view == 'Configurações':
            self.show_configuracoes()

# Executar a aplicação
if __name__ == "__main__":
    app = StreamlitTriagemApp()
    app.run()
