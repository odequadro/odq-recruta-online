"""
Módulo para gerenciar conexão e operações com email
Responsável por conectar ao Gmail e baixar emails com anexos
"""

import imaplib
import email
from email.mime.multipart import MIMEMultipart
import os
import tempfile
from datetime import datetime, timedelta

class EmailClient:
    def __init__(self):
        self.imap_server = None
        self.email_address = None
        
    def conectar(self, email_address, password):
        """
        Conecta ao servidor Gmail usando IMAP
        
        Args:
            email_address (str): Endereço de email
            password (str): Senha do email
            
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        try:
            # Conectar ao Gmail IMAP
            self.imap_server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            self.imap_server.login(email_address, password)
            self.email_address = email_address
            
            # Selecionar caixa de entrada
            self.imap_server.select('INBOX')
            
            return True
            
        except imaplib.IMAP4.error as e:
            print(f"Erro de autenticação IMAP: {e}")
            return False
        except Exception as e:
            print(f"Erro na conexão: {e}")
            return False
            
    def buscar_emails_com_anexos(self, todos_emails=True, dias_atras=7, log_callback=None):
        """
        Busca emails com anexos - pode buscar todos ou apenas dos últimos dias
        
        Args:
            todos_emails (bool): Se True, busca todos os emails; se False, apenas dos últimos dias
            dias_atras (int): Número de dias para buscar emails (usado apenas se todos_emails=False)
            log_callback (function): Função para callback de log
            
        Returns:
            list: Lista de dicionários com dados dos emails e anexos
        """
        def log_message(msg):
            print(msg)
            if log_callback:
                log_callback(msg)
        
        if not self.imap_server:
            error_msg = "❌ ERRO: Cliente de email não conectado"
            log_message(error_msg)
            raise Exception("Cliente de email não conectado")
            
        try:
            # Verificar se a conexão ainda está ativa
            log_message("🔍 Verificando conexão IMAP...")
            status = self.imap_server.noop()
            log_message(f"✅ Conexão IMAP ativa: {status}")
            
            # Primeiro, buscar emails que tenham anexos diretamente via IMAP
            if todos_emails:
                log_message("🔍 Buscando emails com anexos usando filtro IMAP otimizado...")
                # Buscar apenas emails com anexos usando critério IMAP
                try:
                    # Tentar buscar emails com anexos diretamente
                    _, message_numbers = self.imap_server.search(None, 'HAS', 'ATTACHMENT')
                    if not message_numbers[0]:
                        # Fallback para busca tradicional se não suportar HAS ATTACHMENT
                        log_message("⚠️ Servidor não suporta busca por anexos, usando método alternativo...")
                        _, message_numbers = self.imap_server.search(None, 'ALL')
                    else:
                        log_message(f"✅ Busca otimizada por anexos executada")
                except:
                    # Fallback para busca tradicional
                    log_message("⚠️ Busca otimizada falhou, usando busca tradicional...")
                    _, message_numbers = self.imap_server.search(None, 'ALL')
                    
                log_message(f"🔍 Comando SEARCH executado, resultado: {len(message_numbers)}")
            else:
                # Calcular data de início da busca para os últimos dias
                data_inicio = datetime.now() - timedelta(days=dias_atras)
                data_str = data_inicio.strftime("%d-%b-%Y")
                log_message(f"🔍 Buscando emails com anexos dos últimos {dias_atras} dias (desde {data_str})...")
                
                # Usar formato de data compatível com Gmail
                try:
                    # Tentar combinar busca por data E anexos
                    _, message_numbers = self.imap_server.search(None, f'(SINCE {data_str} HAS ATTACHMENT)')
                    if not message_numbers[0]:
                        # Fallback apenas por data
                        _, message_numbers = self.imap_server.search(None, f'SINCE {data_str}')
                    log_message(f"🔍 Busca por data executada, resultado: {len(message_numbers)}")
                except Exception as search_error:
                    # Fallback: buscar últimos emails se a data falhar
                    log_message(f"⚠️ Problema com busca por data ({search_error}), buscando últimos emails...")
                    _, message_numbers = self.imap_server.search(None, 'ALL')
                    log_message(f"🔍 Busca fallback executada, resultado: {len(message_numbers)}")
            
            emails_processados = []
            
            if not message_numbers[0]:
                log_message("ℹ️ Nenhum email encontrado")
                return emails_processados
            
            message_list = message_numbers[0].split()
            total_emails = len(message_list)
            
            # Otimização: Limitar busca para performance quando é "todos"
            if todos_emails and total_emails > 1000:
                log_message(f"⚠️ Encontrados {total_emails} emails. Limitando busca aos últimos 1000 para otimização.")
                message_list = message_list[-1000:]  # Pegar os últimos 1000
                total_emails = len(message_list)
            
            log_message(f"📧 Processando {total_emails} emails...")
            
            # Otimização: processar emails em lotes maiores para reduzir tempo  
            batch_size = 100  # Aumentar para 100 emails por vez
            emails_processados = []
            curriculos_encontrados = 0
            
            # Reverter lista para processar emails mais recentes primeiro
            message_list = list(reversed(message_list))
            
            for batch_start in range(0, total_emails, batch_size):
                batch_end = min(batch_start + batch_size, total_emails)
                batch = message_list[batch_start:batch_end]
                
                log_message(f"📦 Processando lote {batch_start//batch_size + 1}/{(total_emails-1)//batch_size + 1} ({len(batch)} emails)")
                
                # Processar lote de emails
                for i, num in enumerate(batch):
                    email_index = batch_start + i + 1
                    
                    try:
                        # Log menos frequente para performance
                        if email_index % 50 == 0 or email_index <= 10:
                            log_message(f"📋 Processando emails {max(1, email_index-49)}-{min(email_index, total_emails)} de {total_emails}...")
                        
                        # Otimização: Buscar apenas estrutura primeiro (mais rápido)
                        _, header_data = self.imap_server.fetch(num, '(BODYSTRUCTURE)')
                        
                        # Verificar se tem anexos pela estrutura do corpo (pré-filtro rápido)
                        if len(header_data[0]) > 1:
                            bodystructure = str(header_data[0][1]).lower()
                            
                            # Pré-filtro otimizado: verificar se provavelmente tem anexos relevantes
                            tem_anexos_provavel = (
                                'attachment' in bodystructure and (
                                    'pdf' in bodystructure or 
                                    'msword' in bodystructure or
                                    'document' in bodystructure or
                                    'text/plain' in bodystructure
                                )
                            )
                            
                            if not tem_anexos_provavel:
                                continue  # Pular rapidamente emails sem anexos relevantes
                        else:
                            continue  # Pular se não conseguiu obter estrutura
                        
                        # Agora buscar o email completo apenas se passou no pré-filtro
                        _, msg = self.imap_server.fetch(num, '(RFC822)')
                        email_message = email.message_from_bytes(msg[0][1])
                        
                        # Extrair informações básicas
                        remetente = email_message.get('From', '')
                        assunto = email_message.get('Subject', '')
                        data_email = email_message.get('Date', '')
                    
                        # Verificar se tem anexos ANTES de processar
                        tem_anexos = False
                        for part in email_message.walk():
                            if part.get_content_disposition() == 'attachment':
                                filename = part.get_filename()
                                if filename:
                                    # Decodificar nome do arquivo se estiver codificado
                                    try:
                                        decoded_filename = email.header.decode_header(filename)[0][0]
                                        if isinstance(decoded_filename, bytes):
                                            decoded_filename = decoded_filename.decode('utf-8', errors='ignore')
                                        filename = decoded_filename
                                    except:
                                        pass
                                    
                                    # Log apenas se encontrou currículo
                                    extensoes_aceitas = ['.pdf', '.doc', '.docx', '.txt']
                                    nome_lower = filename.lower()
                                    if any(nome_lower.endswith(ext) for ext in extensoes_aceitas):
                                        tem_anexos = True
                                        log_message(f"✅ Currículo encontrado: {filename}")
                                        break
                        
                        # Só processar se tem anexos relevantes
                        if tem_anexos:
                            curriculos_encontrados += 1
                            log_message(f"📧 Email #{curriculos_encontrados} com currículo de: {remetente}")
                            
                            # Processar anexos
                            anexos = self._extrair_anexos(email_message, log_callback)
                            
                            if anexos:  # Só adicionar se conseguiu extrair anexos
                                email_data = {
                                    'numero': num.decode(),
                                    'remetente': remetente,
                                    'assunto': assunto,
                                    'data': data_email,
                                    'anexos': anexos
                                }
                                emails_processados.append(email_data)
                        
                    except Exception as e:
                        log_message(f"⚠️ Erro ao processar email {email_index}: {e}")
                        continue
                
                # Pausa entre lotes para não sobrecarregar o servidor
                if batch_end < total_emails:
                    import time
                    time.sleep(0.2)  # Pausa reduzida
                    
            log_message(f"🎯 Total de emails com currículos encontrados: {len(emails_processados)} de {curriculos_encontrados} emails com anexos")
            return emails_processados
            
        except Exception as e:
            log_message(f"Erro na busca de emails: {e}")
            return []
            
    def _extrair_anexos(self, email_message, log_callback=None):
        """
        Extrai anexos de um email
        
        Args:
            email_message: Objeto email
            log_callback (function): Função para callback de log
            
        Returns:
            list: Lista de dicionários com dados dos anexos
        """
        def log_message(msg):
            print(msg)
            if log_callback:
                log_callback(msg)
        
        anexos = []
        
        try:
            for part in email_message.walk():
                # Verificar se é anexo
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    
                    if filename:
                        # Decodificar nome do arquivo se estiver codificado
                        try:
                            # Decodificar header codificado (como =?iso-8859-1?Q?...?=)
                            decoded_filename = email.header.decode_header(filename)[0][0]
                            if isinstance(decoded_filename, bytes):
                                decoded_filename = decoded_filename.decode('utf-8', errors='ignore')
                            filename = decoded_filename
                        except:
                            # Se a decodificação falhar, usar o nome original
                            pass
                        
                        log_message(f"📎 Arquivo encontrado: {filename}")
                        
                        # Verificar se é arquivo de currículo (PDF, DOC, DOCX)
                        extensoes_aceitas = ['.pdf', '.doc', '.docx', '.txt']
                        nome_lower = filename.lower()
                        
                        if any(nome_lower.endswith(ext) for ext in extensoes_aceitas):
                            log_message(f"✅ Currículo identificado: {filename}")
                            
                            # Salvar arquivo temporariamente
                            conteudo = part.get_payload(decode=True)
                            
                            if conteudo:
                                # Criar arquivo temporário
                                temp_dir = tempfile.gettempdir()
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                # Usar nome seguro para arquivo temporário
                                nome_seguro = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
                                nome_temp = f"curriculo_{timestamp}_{nome_seguro}"
                                caminho_temp = os.path.join(temp_dir, nome_temp)
                                
                                with open(caminho_temp, 'wb') as f:
                                    f.write(conteudo)
                                    
                                anexos.append({
                                    'nome_original': filename,
                                    'caminho_temp': caminho_temp,
                                    'tamanho': len(conteudo),
                                    'tipo': self._detectar_tipo_arquivo(filename),
                                    'conteudo_bytes': conteudo  # Manter conteúdo para salvar depois
                                })
                        else:
                            log_message(f"⚠️ Arquivo ignorado (extensão não suportada): {filename}")
                                
        except Exception as e:
            log_message(f"Erro ao extrair anexos: {e}")
            
        return anexos
        
    def _detectar_tipo_arquivo(self, filename):
        """
        Detecta o tipo de arquivo baseado na extensão
        
        Args:
            filename (str): Nome do arquivo
            
        Returns:
            str: Tipo do arquivo
        """
        nome_lower = filename.lower()
        
        if nome_lower.endswith('.pdf'):
            return 'pdf'
        elif nome_lower.endswith('.doc'):
            return 'doc'
        elif nome_lower.endswith('.docx'):
            return 'docx'
        elif nome_lower.endswith('.txt'):
            return 'txt'
        else:
            return 'desconhecido'
            
    def desconectar(self):
        """Desconecta do servidor de email"""
        if self.imap_server:
            try:
                self.imap_server.close()
                self.imap_server.logout()
            except:
                pass
            finally:
                self.imap_server = None
                
    def __del__(self):
        """Destrutor - garantir desconexão"""
        self.desconectar()
