"""
Módulo para gerenciar o salvamento e organização de currículos
Organiza currículos em pastas baseado no resultado da triagem
"""

import os
import shutil
from datetime import datetime
import re

class CurriculumManager:
    def __init__(self, pasta_base="Curriculos_Triados"):
        """
        Inicializa o gerenciador de currículos
        
        Args:
            pasta_base (str): Nome da pasta base para salvar currículos
        """
        # Criar pasta base no Desktop ou em Downloads
        self.pasta_base = self._obter_pasta_base(pasta_base)
        self.criar_estrutura_pastas()
        
    def _obter_pasta_base(self, nome_pasta):
        """
        Obtém o caminho da pasta base, preferencialmente no Desktop
        
        Args:
            nome_pasta (str): Nome da pasta
            
        Returns:
            str: Caminho completo da pasta base
        """
        try:
            # Tentar Desktop primeiro
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(desktop):
                return os.path.join(desktop, nome_pasta)
        except:
            pass
            
        try:
            # Fallback para Downloads
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads):
                return os.path.join(downloads, nome_pasta)
        except:
            pass
            
        # Fallback final para pasta atual
        return os.path.join(os.getcwd(), nome_pasta)
        
    def criar_estrutura_pastas(self, nome_vaga=None):
        """
        Cria a estrutura de pastas para organizar os currículos
        
        Args:
            nome_vaga (str): Nome da vaga específica para criar subpastas
        """
        try:
            # Pasta principal
            os.makedirs(self.pasta_base, exist_ok=True)
            
            # 🆕 NOVA FUNCIONALIDADE: Pastas organizadas por vaga
            if nome_vaga:
                # Limpar nome da vaga para usar como nome de pasta
                nome_vaga_limpo = self._limpar_nome_pasta(nome_vaga)
                self.pasta_vaga_atual = os.path.join(self.pasta_base, f"VAGA_{nome_vaga_limpo}")
                os.makedirs(self.pasta_vaga_atual, exist_ok=True)
                
                # Subpastas por status dentro da pasta da vaga
                self.pasta_aprovados = os.path.join(self.pasta_vaga_atual, "01_Aprovados")
                self.pasta_revisar = os.path.join(self.pasta_vaga_atual, "02_Para_Revisar")
                self.pasta_rejeitados = os.path.join(self.pasta_vaga_atual, "03_Rejeitados")
                self.pasta_erro = os.path.join(self.pasta_vaga_atual, "04_Erros")
                
                print(f"📁 Estrutura criada para vaga: {nome_vaga}")
            else:
                # Estrutura padrão (sem vaga específica)
                self.pasta_vaga_atual = None
                self.pasta_aprovados = os.path.join(self.pasta_base, "01_Aprovados")
                self.pasta_revisar = os.path.join(self.pasta_base, "02_Para_Revisar")
                self.pasta_rejeitados = os.path.join(self.pasta_base, "03_Rejeitados")
                self.pasta_erro = os.path.join(self.pasta_base, "04_Erros")
            
            # Criar todas as pastas
            for pasta in [self.pasta_aprovados, self.pasta_revisar, self.pasta_rejeitados, self.pasta_erro]:
                os.makedirs(pasta, exist_ok=True)
                
            print(f"📂 Estrutura de pastas criada em: {self.pasta_base}")
            
        except Exception as e:
            print(f"Erro ao criar estrutura de pastas: {e}")
            
    def _limpar_nome_pasta(self, nome):
        """
        Limpa o nome para usar como nome de pasta válido
        
        Args:
            nome (str): Nome original
            
        Returns:
            str: Nome limpo para pasta
        """
        # Remover caracteres especiais e espaços
        nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
        nome_limpo = re.sub(r'\s+', '_', nome_limpo)  # Substituir espaços por underscore
        nome_limpo = nome_limpo[:50]  # Limitar tamanho
        return nome_limpo.upper() if nome_limpo else "VAGA_SEM_NOME"
            
    def salvar_curriculo(self, resultado_analise, email_data, salvar_rejeitados=True):
        """
        Salva o currículo na pasta apropriada baseado no resultado da análise
        
        Args:
            resultado_analise (dict): Resultado da análise do currículo
            email_data (dict): Dados do email original
            salvar_rejeitados (bool): Se deve salvar currículos rejeitados
            
        Returns:
            list: Lista de caminhos dos arquivos salvos
        """
        try:
            status = resultado_analise.get('status', 'Erro')
            pontuacao = resultado_analise.get('pontuacao', 0)
            remetente = resultado_analise.get('email_remetente', 'desconhecido')
            
            # ❌ OTIMIZAÇÃO: Não salvar currículos rejeitados quando há filtro de vaga específica
            if status == "Rejeitado" and not salvar_rejeitados:
                print(f"🗑️ Currículo rejeitado não salvo: {remetente} (Pontuação: {pontuacao})")
                return []
            
            # Determinar pasta de destino
            if status == "Aprovado":
                pasta_destino = self.pasta_aprovados
            elif status == "Revisar":
                pasta_destino = self.pasta_revisar
            elif status == "Rejeitado":
                pasta_destino = self.pasta_rejeitados
            else:
                pasta_destino = self.pasta_erro
                
            arquivos_salvos = []
            
            # Processar cada anexo
            for i, anexo in enumerate(email_data.get('anexos', [])):
                try:
                    arquivo_salvo = self._salvar_anexo(anexo, pasta_destino, remetente, pontuacao, i)
                    if arquivo_salvo:
                        arquivos_salvos.append(arquivo_salvo)
                except Exception as e:
                    print(f"Erro ao salvar anexo {anexo.get('nome_original', '')}: {e}")
                    
            # Arquivo de resumo desabilitado por preferência do usuário
            # self._criar_arquivo_resumo(pasta_destino, resultado_analise, remetente)
            
            return arquivos_salvos
            
        except Exception as e:
            print(f"Erro ao salvar currículo: {e}")
            return []
            
    def _salvar_anexo(self, anexo, pasta_destino, remetente, pontuacao, indice):
        """
        Salva um anexo específico
        
        Args:
            anexo (dict): Dados do anexo
            pasta_destino (str): Pasta onde salvar
            remetente (str): Email do remetente
            pontuacao (float): Pontuação obtida
            indice (int): Índice do anexo
            
        Returns:
            str: Caminho do arquivo salvo ou None se erro
        """
        try:
            nome_original = anexo.get('nome_original', f'anexo_{indice}')
            conteudo_bytes = anexo.get('conteudo_bytes')
            
            if not conteudo_bytes:
                # Tentar ler do arquivo temporário
                caminho_temp = anexo.get('caminho_temp')
                if caminho_temp and os.path.exists(caminho_temp):
                    with open(caminho_temp, 'rb') as f:
                        conteudo_bytes = f.read()
                else:
                    return None
                    
            # Limpar nome do remetente para usar no nome do arquivo
            remetente_limpo = self._limpar_nome_arquivo(remetente)
            
            # Criar nome do arquivo com informações úteis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extensao = os.path.splitext(nome_original)[1]
            nome_base = os.path.splitext(nome_original)[0]
            
            nome_arquivo = f"[{pontuacao:.1f}] {remetente_limpo}_{nome_base}_{timestamp}{extensao}"
            
            # Garantir que o nome não seja muito longo
            if len(nome_arquivo) > 200:
                nome_arquivo = f"[{pontuacao:.1f}] {remetente_limpo[:50]}_{timestamp}{extensao}"
                
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            # Salvar arquivo
            with open(caminho_completo, 'wb') as f:
                f.write(conteudo_bytes)
                
            print(f"Currículo salvo: {caminho_completo}")
            return caminho_completo
            
        except Exception as e:
            print(f"Erro ao salvar anexo: {e}")
            return None
            
    def _limpar_nome_arquivo(self, texto):
        """
        Limpa texto para usar em nome de arquivo
        
        Args:
            texto (str): Texto a limpar
            
        Returns:
            str: Texto limpo
        """
        # Extrair apenas o email se for um endereço completo
        if '<' in texto and '>' in texto:
            match = re.search(r'<([^>]+)>', texto)
            if match:
                texto = match.group(1)
        elif '@' in texto:
            # Usar apenas a parte antes do @
            texto = texto.split('@')[0]
            
        # Remover caracteres especiais
        texto_limpo = re.sub(r'[<>:"/\\|?*]', '_', texto)
        texto_limpo = re.sub(r'[^\w\-_.]', '_', texto_limpo)
        
        # Limitar tamanho
        return texto_limpo[:50] if len(texto_limpo) > 50 else texto_limpo
        
    def _criar_arquivo_resumo(self, pasta_destino, resultado_analise, remetente):
        """
        Cria um arquivo de texto com resumo da análise
        
        Args:
            pasta_destino (str): Pasta onde salvar
            resultado_analise (dict): Resultado da análise
            remetente (str): Email do remetente
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            remetente_limpo = self._limpar_nome_arquivo(remetente)
            
            nome_resumo = f"RESUMO_{remetente_limpo}_{timestamp}.txt"
            caminho_resumo = os.path.join(pasta_destino, nome_resumo)
            
            # Criar conteúdo do resumo
            conteudo = f"""RESUMO DA ANÁLISE DE CURRÍCULO
===============================

Data da Análise: {resultado_analise.get('data', 'N/A')}
Email Remetente: {resultado_analise.get('email_remetente', 'N/A')}
Assunto: {resultado_analise.get('assunto', 'N/A')}
Data do Email: {resultado_analise.get('data_email', 'N/A')}

RESULTADO DA TRIAGEM:
- Status: {resultado_analise.get('status', 'N/A')}
- Pontuação: {resultado_analise.get('pontuacao', 0):.1f}/10.0

ARQUIVOS ANALISADOS:
{resultado_analise.get('nome_arquivo', 'N/A')}

DETALHES DA ANÁLISE:
"""
            
            # Adicionar detalhes dos anexos analisados
            anexos_analisados = resultado_analise.get('anexos_analisados', [])
            for i, anexo in enumerate(anexos_analisados, 1):
                conteudo += f"""
Arquivo {i}: {anexo.get('nome_arquivo', 'N/A')}
- Tipo: {anexo.get('tipo_arquivo', 'N/A')}
- Pontuação: {anexo.get('pontuacao', 0):.1f}
- Palavras-chave encontradas: {', '.join(anexo.get('palavras_encontradas', []))}
"""
                
            # Salvar arquivo
            with open(caminho_resumo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
                
        except Exception as e:
            print(f"Erro ao criar arquivo de resumo: {e}")
            
    def obter_estatisticas_pastas(self):
        """
        Obtém estatísticas dos arquivos nas pastas
        
        Returns:
            dict: Estatísticas das pastas
        """
        try:
            stats = {
                'aprovados': 0,
                'revisar': 0,
                'rejeitados': 0,
                'erros': 0,
                'total': 0
            }
            
            # Contar arquivos em cada pasta (excluindo resumos)
            for pasta, chave in [(self.pasta_aprovados, 'aprovados'),
                               (self.pasta_revisar, 'revisar'),
                               (self.pasta_rejeitados, 'rejeitados'),
                               (self.pasta_erro, 'erros')]:
                if os.path.exists(pasta):
                    arquivos = [f for f in os.listdir(pasta) 
                              if not f.startswith('RESUMO_') and os.path.isfile(os.path.join(pasta, f))]
                    stats[chave] = len(arquivos)
                    
            stats['total'] = sum(stats.values()) - stats['erros']  # Não contar erros no total
            
            return stats
            
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
            
    def abrir_pasta_curriculos(self):
        """Abre a pasta de currículos no explorador de arquivos"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.pasta_base)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{self.pasta_base}"' if sys.platform == 'darwin' 
                         else f'xdg-open "{self.pasta_base}"')
        except Exception as e:
            print(f"Erro ao abrir pasta: {e}")
            
    def limpar_pastas_antigas(self, dias=30):
        """
        Remove currículos mais antigos que X dias
        
        Args:
            dias (int): Número de dias para manter arquivos
        """
        try:
            import time
            cutoff_time = time.time() - (dias * 24 * 60 * 60)
            
            for pasta in [self.pasta_aprovados, self.pasta_revisar, self.pasta_rejeitados, self.pasta_erro]:
                if os.path.exists(pasta):
                    for arquivo in os.listdir(pasta):
                        caminho_arquivo = os.path.join(pasta, arquivo)
                        if os.path.isfile(caminho_arquivo):
                            if os.path.getmtime(caminho_arquivo) < cutoff_time:
                                os.remove(caminho_arquivo)
                                print(f"Arquivo antigo removido: {arquivo}")
                                
        except Exception as e:
            print(f"Erro ao limpar arquivos antigos: {e}")
