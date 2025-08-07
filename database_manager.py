"""
Módulo para gerenciar banco de dados SQLite
Armazena critérios de vagas e resultados de análise
"""

import sqlite3
import json
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="triagem_curriculos.db"):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            db_path (str): Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self.criar_tabelas()
        
    def criar_tabelas(self):
        """Cria as tabelas necessárias no banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela de vagas e critérios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vagas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome_vaga TEXT NOT NULL,
                        palavras_chave TEXT NOT NULL,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ativa BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Tabela de resultados de análise
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resultados (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_analise TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        email_remetente TEXT,
                        assunto TEXT,
                        data_email TEXT,
                        nome_arquivo TEXT,
                        pontuacao REAL,
                        status TEXT,
                        detalhes_json TEXT,
                        vaga_id INTEGER,
                        FOREIGN KEY (vaga_id) REFERENCES vagas (id)
                    )
                ''')
                
                # Tabela de anexos analisados
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS anexos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resultado_id INTEGER,
                        nome_arquivo TEXT,
                        tipo_arquivo TEXT,
                        tamanho_texto INTEGER,
                        pontuacao REAL,
                        palavras_encontradas TEXT,
                        FOREIGN KEY (resultado_id) REFERENCES resultados (id)
                    )
                ''')
                
                # Tabela de currículos aprovados por vaga
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aprovados_por_vaga (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vaga_id INTEGER,
                        nome_vaga TEXT,
                        email_remetente TEXT,
                        nome_candidato TEXT,
                        assunto_email TEXT,
                        nome_arquivo TEXT,
                        pontuacao REAL,
                        data_aprovacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_email TEXT,
                        detalhes_curriculo TEXT,
                        observacoes TEXT,
                        FOREIGN KEY (vaga_id) REFERENCES vagas (id)
                    )
                ''')
                
                conn.commit()
                print("Tabelas do banco de dados criadas/verificadas com sucesso")
                
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            
    def salvar_vaga(self, nome_vaga, palavras_chave):
        """
        Salva uma nova vaga com seus critérios
        
        Args:
            nome_vaga (str): Nome da vaga
            palavras_chave (list): Lista de palavras-chave
            
        Returns:
            int: ID da vaga salva ou None se erro
        """
        try:
            # Converter lista para JSON
            palavras_json = json.dumps(palavras_chave, ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Desativar vagas anteriores com o mesmo nome
                cursor.execute('''
                    UPDATE vagas SET ativa = FALSE 
                    WHERE nome_vaga = ? AND ativa = TRUE
                ''', (nome_vaga,))
                
                # Inserir nova vaga
                cursor.execute('''
                    INSERT INTO vagas (nome_vaga, palavras_chave)
                    VALUES (?, ?)
                ''', (nome_vaga, palavras_json))
                
                vaga_id = cursor.lastrowid
                conn.commit()
                
                print(f"Vaga '{nome_vaga}' salva com ID {vaga_id}")
                return vaga_id
                
        except Exception as e:
            print(f"Erro ao salvar vaga: {e}")
            return None
            
    def obter_vagas_ativas(self):
        """
        Obtém todas as vagas ativas
        
        Returns:
            list: Lista de vagas com suas informações
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, nome_vaga, palavras_chave, data_criacao
                    FROM vagas
                    WHERE ativa = TRUE
                    ORDER BY data_criacao DESC
                ''')
                
                vagas = []
                for row in cursor.fetchall():
                    vaga = {
                        'id': row[0],
                        'nome': row[1],
                        'palavras_chave': json.loads(row[2]),
                        'data_criacao': row[3]
                    }
                    vagas.append(vaga)
                    
                return vagas
                
        except Exception as e:
            print(f"Erro ao obter vagas: {e}")
            return []
            
    def salvar_resultado(self, resultado):
        """
        Salva um resultado de análise de currículo (evita duplicações)
        
        Args:
            resultado (dict): Dados do resultado da análise
            
        Returns:
            int: ID do resultado salvo ou None se erro
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se já existe registro com mesmo email e arquivo
                email_remetente = resultado.get('email_remetente', '')
                assunto = resultado.get('assunto', '')
                data_email = resultado.get('data_email', '')
                
                cursor.execute('''
                    SELECT id FROM resultados 
                    WHERE email_remetente = ? AND assunto = ? AND data_email = ?
                ''', (email_remetente, assunto, data_email))
                
                registro_existente = cursor.fetchone()
                
                if registro_existente:
                    print(f"📋 Resultado já existe para {email_remetente} - ignorando duplicação")
                    return registro_existente[0]
                
                # Preparar dados
                detalhes_json = json.dumps(resultado.get('anexos_analisados', []), 
                                         ensure_ascii=False)
                
                vaga_id = resultado.get('vaga_id', None)
                
                # Inserir resultado principal
                cursor.execute('''
                    INSERT INTO resultados 
                    (email_remetente, assunto, data_email, nome_arquivo, 
                     pontuacao, status, detalhes_json, vaga_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    email_remetente,
                    assunto,
                    data_email,
                    resultado.get('nome_arquivo', ''),
                    resultado.get('pontuacao', 0),
                    resultado.get('status', ''),
                    detalhes_json,
                    vaga_id
                ))
                
                resultado_id = cursor.lastrowid
                
                # Inserir anexos analisados
                anexos = resultado.get('anexos_analisados', [])
                for anexo in anexos:
                    palavras_json = json.dumps(anexo.get('palavras_encontradas', []), 
                                             ensure_ascii=False)
                    
                    cursor.execute('''
                        INSERT INTO anexos
                        (resultado_id, nome_arquivo, tipo_arquivo, tamanho_texto,
                         pontuacao, palavras_encontradas)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        resultado_id,
                        anexo.get('nome_arquivo', ''),
                        anexo.get('tipo_arquivo', ''),
                        anexo.get('tamanho_texto', 0),
                        anexo.get('pontuacao', 0),
                        palavras_json
                    ))
                
                conn.commit()
                print(f"Resultado salvo com ID {resultado_id}")
                return resultado_id
                
        except Exception as e:
            print(f"Erro ao salvar resultado: {e}")
            return None
            
    def obter_resultados_recentes(self, limite=50):
        """
        Obtém os resultados mais recentes
        
        Args:
            limite (int): Número máximo de resultados
            
        Returns:
            list: Lista de resultados
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, data_analise, email_remetente, assunto, 
                           nome_arquivo, pontuacao, status
                    FROM resultados
                    ORDER BY data_analise DESC
                    LIMIT ?
                ''', (limite,))
                
                resultados = []
                for row in cursor.fetchall():
                    resultado = {
                        'id': row[0],
                        'data': row[1],
                        'email_remetente': row[2],
                        'assunto': row[3],
                        'nome_arquivo': row[4],
                        'pontuacao': row[5],
                        'status': row[6]
                    }
                    resultados.append(resultado)
                    
                return resultados
                
        except Exception as e:
            print(f"Erro ao obter resultados: {e}")
            return []
            
    def obter_estatisticas(self):
        """
        Obtém estatísticas gerais do sistema
        
        Returns:
            dict: Estatísticas do sistema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total de análises
                cursor.execute('SELECT COUNT(*) FROM resultados')
                stats['total_analises'] = cursor.fetchone()[0]
                
                # Aprovados
                cursor.execute("SELECT COUNT(*) FROM resultados WHERE status = 'Aprovado'")
                stats['aprovados'] = cursor.fetchone()[0]
                
                # Para revisar
                cursor.execute("SELECT COUNT(*) FROM resultados WHERE status = 'Revisar'")
                stats['revisar'] = cursor.fetchone()[0]
                
                # Rejeitados
                cursor.execute("SELECT COUNT(*) FROM resultados WHERE status = 'Rejeitado'")
                stats['rejeitados'] = cursor.fetchone()[0]
                
                # Pontuação média
                cursor.execute('SELECT AVG(pontuacao) FROM resultados WHERE pontuacao > 0')
                resultado = cursor.fetchone()[0]
                stats['pontuacao_media'] = round(resultado, 2) if resultado else 0
                
                # Vagas ativas
                cursor.execute('SELECT COUNT(*) FROM vagas WHERE ativa = TRUE')
                stats['vagas_ativas'] = cursor.fetchone()[0]
                
                # Estatísticas de aprovados por vaga
                cursor.execute('SELECT COUNT(*) FROM aprovados_por_vaga')
                stats['total_aprovados_salvos'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT nome_vaga) FROM aprovados_por_vaga')
                stats['vagas_com_aprovados'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
            
    def exportar_resultados_csv(self, arquivo_saida):
        """
        Exporta resultados para arquivo CSV
        
        Args:
            arquivo_saida (str): Caminho do arquivo de saída
            
        Returns:
            bool: True se exportou com sucesso
        """
        try:
            import csv
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT data_analise, email_remetente, assunto, nome_arquivo,
                           pontuacao, status
                    FROM resultados
                    ORDER BY data_analise DESC
                ''')
                
                with open(arquivo_saida, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Cabeçalho
                    writer.writerow(['Data', 'Email Remetente', 'Assunto', 
                                   'Nome Arquivo', 'Pontuação', 'Status'])
                    
                    # Dados
                    for row in cursor.fetchall():
                        writer.writerow(row)
                        
                print(f"Resultados exportados para {arquivo_saida}")
                return True
                
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False
            
    def limpar_dados_antigos(self, dias=30):
        """
        Remove dados mais antigos que X dias
        
        Args:
            dias (int): Número de dias para manter
        """
        try:
            data_limite = datetime.now().timestamp() - (dias * 24 * 60 * 60)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remover anexos órfãos primeiro
                cursor.execute('''
                    DELETE FROM anexos 
                    WHERE resultado_id IN (
                        SELECT id FROM resultados 
                        WHERE data_analise < datetime(?, 'unixepoch')
                    )
                ''', (data_limite,))
                
                # Remover resultados antigos
                cursor.execute('''
                    DELETE FROM resultados 
                    WHERE data_analise < datetime(?, 'unixepoch')
                ''', (data_limite,))
                
                removidos = cursor.rowcount
                conn.commit()
                
                print(f"Removidos {removidos} registros antigos")
                
        except Exception as e:
            print(f"Erro ao limpar dados antigos: {e}")
            
    def obter_todos_resultados(self):
        """
        Obtém todos os resultados da análise de currículos
        
        Returns:
            list: Lista de tuplas com os resultados
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, data_analise, email_remetente, nome_arquivo, 
                           pontuacao, status, observacoes
                    FROM resultados
                    ORDER BY data_analise DESC
                ''')
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Erro ao obter resultados: {e}")
            return []
            
    def limpar_resultados(self):
        """
        Limpa todos os resultados da análise de currículos do banco de dados
        
        Returns:
            int: Número de registros removidos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar quantos registros serão removidos
                cursor.execute('SELECT COUNT(*) FROM resultados')
                total_registros = cursor.fetchone()[0]
                
                # Limpar todos os resultados
                cursor.execute('DELETE FROM resultados')
                
                # Resetar o contador de ID (opcional)
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="resultados"')
                
                conn.commit()
                
                print(f"✅ Removidos {total_registros} registros de resultados")
                return total_registros
                
        except Exception as e:
            print(f"❌ Erro ao limpar resultados: {e}")
            raise e
            
    def salvar_curriculo_aprovado(self, resultado, nome_vaga, vaga_id):
        """
        Salva um currículo aprovado organizadamente por vaga
        
        Args:
            resultado (dict): Dados completos do resultado da análise
            nome_vaga (str): Nome da vaga para organização
            vaga_id (int): ID da vaga no banco
            
        Returns:
            int: ID do registro salvo ou None se erro
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se já existe esse currículo aprovado para esta vaga
                cursor.execute('''
                    SELECT id FROM aprovados_por_vaga 
                    WHERE email_remetente = ? AND vaga_id = ? AND nome_arquivo = ?
                ''', (resultado.get('email_remetente', ''), vaga_id, resultado.get('nome_arquivo', '')))
                
                existente = cursor.fetchone()
                if existente:
                    print(f"📋 Currículo já salvo para vaga '{nome_vaga}': {resultado.get('email_remetente', '')}")
                    return existente[0]
                
                # Extrair nome do candidato do email ou arquivo
                nome_candidato = self._extrair_nome_candidato(resultado)
                
                # Preparar detalhes do currículo
                detalhes = {
                    'anexos_analisados': resultado.get('anexos_analisados', []),
                    'palavras_encontradas': [],
                    'pontuacao_detalhada': {}
                }
                
                for anexo in resultado.get('anexos_analisados', []):
                    if anexo.get('palavras_encontradas'):
                        detalhes['palavras_encontradas'].extend(anexo['palavras_encontradas'])
                    if anexo.get('detalhes'):
                        detalhes['pontuacao_detalhada'][anexo.get('nome_arquivo', '')] = anexo['detalhes']
                
                detalhes_json = json.dumps(detalhes, ensure_ascii=False)
                
                # Inserir currículo aprovado
                cursor.execute('''
                    INSERT INTO aprovados_por_vaga 
                    (vaga_id, nome_vaga, email_remetente, nome_candidato, assunto_email, 
                     nome_arquivo, pontuacao, data_email, detalhes_curriculo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vaga_id,
                    nome_vaga,
                    resultado.get('email_remetente', ''),
                    nome_candidato,
                    resultado.get('assunto', ''),
                    resultado.get('nome_arquivo', ''),
                    resultado.get('pontuacao', 0),
                    resultado.get('data_email', ''),
                    detalhes_json
                ))
                
                aprovado_id = cursor.lastrowid
                conn.commit()
                
                print(f"✅ Currículo aprovado salvo para vaga '{nome_vaga}': {nome_candidato}")
                return aprovado_id
                
        except Exception as e:
            print(f"❌ Erro ao salvar currículo aprovado: {e}")
            return None
            
    def _extrair_nome_candidato(self, resultado):
        """
        Tenta extrair nome do candidato do email ou arquivo
        
        Args:
            resultado (dict): Dados do resultado
            
        Returns:
            str: Nome do candidato ou email se não conseguir extrair
        """
        import re
        
        email = resultado.get('email_remetente', '')
        nome_arquivo = resultado.get('nome_arquivo', '')
        
        # Tentar extrair do nome do arquivo primeiro
        if nome_arquivo:
            # Remover extensões comuns
            nome_limpo = nome_arquivo.lower()
            for ext in ['.pdf', '.docx', '.doc', '.txt']:
                nome_limpo = nome_limpo.replace(ext, '')
            
            # Remover palavras comuns de currículos
            palavras_remover = ['curriculo', 'curriculum', 'cv', 'resume', 'vitae']
            for palavra in palavras_remover:
                nome_limpo = nome_limpo.replace(palavra, '')
            
            # Limpar caracteres especiais e espaços
            nome_limpo = re.sub(r'[_\-\.]', ' ', nome_limpo).strip()
            
            if len(nome_limpo) > 2:
                return nome_limpo.title()
        
        # Se não conseguir do arquivo, tentar do email
        if '@' in email:
            nome_email = email.split('@')[0]
            nome_email = re.sub(r'[_\-\.]', ' ', nome_email).strip()
            if len(nome_email) > 2:
                return nome_email.title()
        
        # Fallback: retornar o email
        return email
        
    def listar_aprovados_por_vaga(self, nome_vaga=None):
        """
        Lista currículos aprovados organizados por vaga
        
        Args:
            nome_vaga (str, optional): Filtrar por vaga específica
            
        Returns:
            dict: Currículos organizados por vaga
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if nome_vaga:
                    cursor.execute('''
                        SELECT nome_vaga, nome_candidato, email_remetente, 
                               nome_arquivo, pontuacao, data_aprovacao, observacoes
                        FROM aprovados_por_vaga 
                        WHERE nome_vaga = ?
                        ORDER BY pontuacao DESC, data_aprovacao DESC
                    ''', (nome_vaga,))
                else:
                    cursor.execute('''
                        SELECT nome_vaga, nome_candidato, email_remetente, 
                               nome_arquivo, pontuacao, data_aprovacao, observacoes
                        FROM aprovados_por_vaga 
                        ORDER BY nome_vaga, pontuacao DESC, data_aprovacao DESC
                    ''')
                
                resultados = cursor.fetchall()
                
                # Organizar por vaga
                aprovados_por_vaga = {}
                for linha in resultados:
                    vaga = linha[0]
                    if vaga not in aprovados_por_vaga:
                        aprovados_por_vaga[vaga] = []
                    
                    aprovados_por_vaga[vaga].append({
                        'nome_candidato': linha[1],
                        'email': linha[2],
                        'arquivo': linha[3],
                        'pontuacao': linha[4],
                        'data_aprovacao': linha[5],
                        'observacoes': linha[6]
                    })
                
                return aprovados_por_vaga
                
        except Exception as e:
            print(f"❌ Erro ao listar aprovados por vaga: {e}")
            return {}
            
    def obter_estatisticas_aprovados(self):
        """
        Obtém estatísticas dos currículos aprovados por vaga
        
        Returns:
            dict: Estatísticas organizadas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT nome_vaga, COUNT(*) as total, 
                           AVG(pontuacao) as pontuacao_media,
                           MAX(pontuacao) as pontuacao_maxima
                    FROM aprovados_por_vaga 
                    GROUP BY nome_vaga
                    ORDER BY total DESC
                ''')
                
                estatisticas = {}
                for linha in cursor.fetchall():
                    estatisticas[linha[0]] = {
                        'total_aprovados': linha[1],
                        'pontuacao_media': round(linha[2], 1),
                        'pontuacao_maxima': linha[3]
                    }
                
                return estatisticas
                
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}
