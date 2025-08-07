import os
import re
from datetime import datetime
import tempfile
import unicodedata

try:
    import pypdf as PyPDF2
    PDF_DISPONIVEL = True
    USAR_PDFPLUMBER = False
except ImportError:
    try:
        import PyPDF2
        PDF_DISPONIVEL = True
        USAR_PDFPLUMBER = False
    except ImportError:
        try:
            import pdfplumber
            PDF_DISPONIVEL = True
            USAR_PDFPLUMBER = True
        except ImportError:
            PDF_DISPONIVEL = False
            USAR_PDFPLUMBER = False

try:
    from docx import Document
    DOCX_DISPONIVEL = True
except ImportError:
    DOCX_DISPONIVEL = False

# Importar analisador de IA (opcional)
try:
    from ai_analyzer import AIAnalyzer
    IA_DISPONIVEL = True
except ImportError:
    IA_DISPONIVEL = False

class CurriculumAnalyzer:
    def __init__(self):
        self.palavras_chave_default = [
            'experiência', 'experiencia', 'formação', 'formacao', 'graduação', 'graduacao',
            'curso', 'habilidades', 'conhecimento', 'competências', 'competencias', 
            'projetos', 'trabalho', 'técnico', 'tecnico'
        ]
        
        # Mapeamento de abreviações comuns
        self.abreviacoes = {
            'tst': ['técnico em segurança do trabalho', 'tecnico em seguranca do trabalho', 'segurança do trabalho', 'seguranca do trabalho'],
            'rh': ['recursos humanos', 'gestão de pessoas', 'gestao de pessoas'],
            'ti': ['tecnologia da informação', 'tecnologia da informacao', 'informatica', 'informática'],
            'adm': ['administração', 'administracao', 'administrativo'],
            'eng': ['engenharia', 'engenheiro', 'engenheira'],
            'tec': ['técnico', 'tecnico', 'tecnologia'],
            'sup': ['superior', 'supervisão', 'supervisao', 'supervisor'],
            'coord': ['coordenação', 'coordenacao', 'coordenador'],
            'ger': ['gerência', 'gerencia', 'gerente'],
            'dir': ['diretoria', 'diretor', 'diretora'],
            'aux': ['auxiliar', 'assistente'],
            'op': ['operação', 'operacao', 'operador'],
            'prod': ['produção', 'producao', 'produto'],
            'qual': ['qualidade', 'controle de qualidade'],
            'seg': ['segurança', 'seguranca'],
            'amb': ['ambiental', 'meio ambiente'],
            'cont': ['contabilidade', 'contador', 'contábil', 'contabil'],
            'fin': ['financeiro', 'finanças', 'financas'],
            'com': ['comercial', 'comércio', 'comercio', 'vendas'],
            'mkt': ['marketing', 'mercadologia'],
            'log': ['logística', 'logistica']
        }
        
        # Inicializar analisador de IA se disponível
        self.ai_analyzer = None
        if IA_DISPONIVEL:
            try:
                self.ai_analyzer = AIAnalyzer()
                print("🤖 Analisador de IA inicializado com sucesso!")
            except Exception as e:
                print(f"⚠️ Não foi possível inicializar a IA: {e}")
                self.ai_analyzer = None
        
    def _normalizar_texto(self, texto):
        if not texto:
            return ""
        texto_normalizado = unicodedata.normalize('NFD', texto)
        texto_sem_acentos = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
        return texto_sem_acentos.lower()
    
    def _expandir_palavras_chave(self, palavras_chave):
        """
        Expande lista de palavras-chave incluindo suas abreviações correspondentes
        
        Args:
            palavras_chave (list): Lista de palavras-chave originais
            
        Returns:
            list: Lista expandida com abreviações e termos completos
        """
        palavras_expandidas = list(palavras_chave)  # cópia da lista original
        
        for palavra in palavras_chave:
            palavra_norm = self._normalizar_texto(palavra)
            
            # Se a palavra é uma abreviação conhecida, adicionar termos completos
            if palavra_norm in self.abreviacoes:
                palavras_expandidas.extend(self.abreviacoes[palavra_norm])
            
            # Se a palavra corresponde a algum termo completo, adicionar a abreviação
            for abrev, termos_completos in self.abreviacoes.items():
                for termo in termos_completos:
                    if palavra_norm == self._normalizar_texto(termo):
                        palavras_expandidas.append(abrev)
                        break
        
        # Remover duplicatas mantendo a ordem
        palavras_unicas = []
        for palavra in palavras_expandidas:
            if palavra not in palavras_unicas:
                palavras_unicas.append(palavra)
                
        return palavras_unicas
        
    def analisar_curriculo(self, email_data, palavras_chave_vaga=None):
        try:
            palavras_chave = palavras_chave_vaga if palavras_chave_vaga else self.palavras_chave_default
            
            resultados_anexos = []
            pontuacao_total = 0
            
            for anexo in email_data.get('anexos', []):
                resultado_anexo = self._analisar_arquivo(anexo, palavras_chave)
                resultados_anexos.append(resultado_anexo)
                pontuacao_total += resultado_anexo.get('pontuacao', 0)
                
            num_anexos = len(resultados_anexos)
            pontuacao_media = pontuacao_total / num_anexos if num_anexos > 0 else 0
            
            if pontuacao_media >= 3.0:
                status = "Aprovado"
            elif pontuacao_media >= 1.5:
                status = "Revisar"
            else:
                status = "Rejeitado"
                
            resultado = {
                'data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'email_remetente': email_data.get('remetente', ''),
                'assunto': email_data.get('assunto', ''),
                'data_email': email_data.get('data', ''),
                'anexos_analisados': resultados_anexos,
                'pontuacao': pontuacao_media,
                'status': status,
                'nome_arquivo': ', '.join([a.get('nome_original', '') for a in email_data.get('anexos', [])])
            }
            
            return resultado
            
        except Exception as e:
            return {
                'data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'email_remetente': email_data.get('remetente', ''),
                'assunto': email_data.get('assunto', ''),
                'pontuacao': 0,
                'status': 'Erro',
                'erro': str(e),
                'nome_arquivo': 'Erro na análise'
            }
            
    def _analisar_arquivo(self, anexo, palavras_chave_vaga=None):
        """
        Analisa um arquivo específico
        
        Args:
            anexo (dict): Dados do anexo
            palavras_chave_vaga (list): Palavras-chave específicas da vaga
            
        Returns:
            dict: Resultado da análise do arquivo
        """
        try:
            caminho = anexo.get('caminho_temp', '')
            tipo = anexo.get('tipo', '')
            nome = anexo.get('nome_original', '')
            
            texto_extraido = self._extrair_texto(caminho, tipo)
            
            if not texto_extraido:
                return {
                    'nome_arquivo': nome,
                    'texto_extraido': False,
                    'pontuacao': 0,
                    'palavras_encontradas': [],
                    'erro': 'Não foi possível extrair texto'
                }
                
            analise = self._analisar_texto(texto_extraido, palavras_chave_vaga)
            
            resultado = {
                'nome_arquivo': nome,
                'tipo_arquivo': tipo,
                'tamanho_texto': len(texto_extraido),
                'texto_extraido': True,
                'pontuacao': analise['pontuacao'],
                'palavras_encontradas': analise['palavras_encontradas'],
                'detalhes': analise['detalhes']
            }
            
            # Limpar arquivo temporário
            try:
                os.remove(caminho)
            except:
                pass
                
            return resultado
            
        except Exception as e:
            return {
                'nome_arquivo': anexo.get('nome_original', ''),
                'pontuacao': 0,
                'erro': str(e)
            }
            
    def _extrair_texto(self, caminho_arquivo, tipo):
        """
        Extrai texto de diferentes tipos de arquivo
        
        Args:
            caminho_arquivo (str): Caminho para o arquivo
            tipo (str): Tipo do arquivo
            
        Returns:
            str: Texto extraído ou string vazia se erro
        """
        try:
            if tipo == 'pdf':
                return self._extrair_texto_pdf(caminho_arquivo)
            elif tipo == 'docx':
                return self._extrair_texto_docx(caminho_arquivo)
            elif tipo == 'doc':
                return self._extrair_texto_doc(caminho_arquivo)
            elif tipo == 'txt':
                return self._extrair_texto_txt(caminho_arquivo)
            else:
                return ""
                
        except Exception as e:
            print(f"Erro ao extrair texto de {caminho_arquivo}: {e}")
            return ""
            
    def _extrair_texto_pdf(self, caminho):
        """Extrai texto de arquivo PDF"""
        if not PDF_DISPONIVEL:
            return "Biblioteca PDF não disponível"
            
        texto = ""
        
        try:
            if 'USAR_PDFPLUMBER' in globals() and USAR_PDFPLUMBER:
                # Usar pdfplumber
                import pdfplumber
                with pdfplumber.open(caminho) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            texto += page_text + "\n"
            else:
                # Usar PyPDF2
                with open(caminho, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        texto += page.extract_text() + "\n"
                        
        except Exception as e:
            print(f"Erro ao extrair PDF: {e}")
            
        return texto
        
    def _extrair_texto_docx(self, caminho):
        """Extrai texto de arquivo DOCX"""
        if not DOCX_DISPONIVEL:
            return "Biblioteca DOCX não disponível"
            
        try:
            doc = Document(caminho)
            texto = ""
            for paragraph in doc.paragraphs:
                texto += paragraph.text + "\n"
            return texto
        except Exception as e:
            print(f"Erro ao extrair DOCX: {e}")
            return ""
            
    def _extrair_texto_doc(self, caminho):
        """Extrai texto de arquivo DOC (formato antigo)"""
        # Para arquivos .doc antigos, seria necessário usar python-docx2txt ou similar
        # Por simplicidade, retornar mensagem informativa
        return "Arquivo DOC antigo - recomenda-se converter para DOCX"
        
    def _extrair_texto_txt(self, caminho):
        """Extrai texto de arquivo TXT"""
        try:
            with open(caminho, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(caminho, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                print(f"Erro ao ler TXT: {e}")
                return ""
        except Exception as e:
            print(f"Erro ao extrair TXT: {e}")
            return ""
            
    def _analisar_texto(self, texto, palavras_chave=None):
        if palavras_chave is None:
            palavras_chave = self.palavras_chave_default
            
        texto_lower = texto.lower()
        palavras_encontradas = []
        pontuacao = 0
        detalhes = {}
        
        # Verificar se é busca por vaga específica ou busca geral
        if palavras_chave != self.palavras_chave_default:
            vaga_score = self._calcular_score_categoria(texto_lower, palavras_chave)
            detalhes['palavras_chave_vaga'] = vaga_score
            
            # FILTRO CRÍTICO APRIMORADO: Análise mais rigorosa para correspondência de vaga
            correspondencia_minima = self._verificar_correspondencia_vaga(texto_lower, palavras_chave)
            
            if correspondencia_minima < 2.0:  # Precisa de pelo menos 2 pontos de correspondência
                return {
                    'pontuacao': 0.0,
                    'palavras_encontradas': [],
                    'detalhes': {
                        'motivo_rejeicao': f'Currículo não corresponde à vaga. Palavras-chave encontradas: {correspondencia_minima:.1f}/10.0 pontos',
                        'analise_rejeicao': 'Currículo não possui palavras-chave suficientes para a vaga específica',
                        'palavras_buscadas': palavras_chave[:5],  # Mostrar primeiras 5 palavras buscadas
                        'correspondencia_score': correspondencia_minima
                    }
                }
            
            pontuacao += vaga_score['pontuacao'] * 2
        
        formacao_keywords = ['graduação', 'bacharelado', 'licenciatura', 'mestrado', 'doutorado', 
                           'técnico', 'superior', 'universidade', 'faculdade', 'curso']
        formacao_score = self._calcular_score_categoria(texto_lower, formacao_keywords)
        detalhes['formacao'] = formacao_score
        
        experiencia_keywords = ['experiência', 'trabalho', 'emprego', 'função', 'cargo', 
                              'atuação', 'atividade', 'responsabilidade', 'ano', 'anos']
        experiencia_score = self._calcular_score_categoria(texto_lower, experiencia_keywords)
        detalhes['experiencia'] = experiencia_score
        
        habilidades_keywords = ['conhecimento', 'habilidade', 'competência', 'domínio', 
                              'experiência em', 'trabalho com', 'utilização']
        habilidades_score = self._calcular_score_categoria(texto_lower, habilidades_keywords)
        detalhes['habilidades'] = habilidades_score
        
        pontuacao_formacao = formacao_score['pontuacao']
        pontuacao_experiencia = experiencia_score['pontuacao']
        pontuacao_habilidades = habilidades_score['pontuacao']
        
        if palavras_chave == self.palavras_chave_default:
            pontuacao = (pontuacao_formacao + pontuacao_experiencia + pontuacao_habilidades) / 3
            
            palavras_encontradas.extend(formacao_score['palavras_encontradas'])
            palavras_encontradas.extend(experiencia_score['palavras_encontradas'])
            palavras_encontradas.extend(habilidades_score['palavras_encontradas'])
        else:
            pontuacao_geral = (pontuacao_formacao + pontuacao_experiencia + pontuacao_habilidades) / 3
            pontuacao_vaga = detalhes['palavras_chave_vaga']['pontuacao']
            pontuacao = (pontuacao_vaga * 0.7) + (pontuacao_geral * 0.3)
            
            palavras_encontradas.extend(detalhes['palavras_chave_vaga']['palavras_encontradas'])
            palavras_encontradas.extend(formacao_score['palavras_encontradas'])
            palavras_encontradas.extend(experiencia_score['palavras_encontradas'])
            palavras_encontradas.extend(habilidades_score['palavras_encontradas'])
                
        # Análise com IA se disponível
        ai_analysis = None
        if self.ai_analyzer:
            try:
                # Criar descrição básica da vaga baseada nas palavras-chave
                job_description = {
                    'titulo': 'Vaga em análise',
                    'descricao': f"Vaga que requer conhecimentos em: {', '.join(palavras_chave[:10])}",
                    'requisitos': palavras_chave
                }
                
                # Realizar análise inteligente
                ai_result = self.ai_analyzer.analyze_curriculum(texto, job_description)
                if ai_result:
                    ai_analysis = ai_result
                    
                    # Ajustar pontuação baseada na análise de IA
                    if 'fit_score' in ai_result and ai_result['fit_score'] > 0:
                        ai_score = ai_result['fit_score'] / 10  # Normalizar para 0-10
                        # Combinar pontuação tradicional (70%) com IA (30%)
                        pontuacao = (pontuacao * 0.7) + (ai_score * 0.3)
                        detalhes['ai_enhancement'] = True
                        detalhes['ai_score'] = ai_score
                        
            except Exception as e:
                print(f"⚠️ Erro na análise de IA: {e}")
                ai_analysis = None
                
        return {
            'pontuacao': round(pontuacao, 1),
            'palavras_encontradas': palavras_encontradas,
            'detalhes': detalhes,
            'ai_analysis': ai_analysis
        }
        
    def _calcular_score_categoria(self, texto, keywords):
        texto_normalizado = self._normalizar_texto(texto)
        
        # Expandir palavras-chave incluindo abreviações
        palavras_expandidas = self._expandir_palavras_chave(keywords)
        
        palavras_encontradas = []
        for keyword in keywords:
            keyword_normalizado = self._normalizar_texto(keyword)
            
            # Verificar se a palavra-chave original ou suas variações estão no texto
            encontrou = False
            if keyword_normalizado in texto_normalizado:
                encontrou = True
            else:
                # Verificar abreviações e termos relacionados
                for palavra_expandida in palavras_expandidas:
                    if self._normalizar_texto(palavra_expandida) in texto_normalizado:
                        # Verificar se esta palavra expandida está relacionada à keyword original
                        keyword_norm = self._normalizar_texto(keyword)
                        palavra_exp_norm = self._normalizar_texto(palavra_expandida)
                        
                        # Verificar relação direta
                        if (keyword_norm in self.abreviacoes and palavra_exp_norm in [self._normalizar_texto(t) for t in self.abreviacoes[keyword_norm]]) or \
                           (palavra_exp_norm in self.abreviacoes and keyword_norm in [self._normalizar_texto(t) for t in self.abreviacoes[palavra_exp_norm]]):
                            encontrou = True
                            break
            
            if encontrou and keyword not in palavras_encontradas:
                palavras_encontradas.append(keyword)
                
        encontradas = len(palavras_encontradas)
        proporcao = encontradas / len(keywords) if len(keywords) > 0 else 0
        pontuacao = min(proporcao * 10, 10)
        
        return {
            'pontuacao': pontuacao,
            'palavras_encontradas': palavras_encontradas,
            'total_palavras_categoria': len(keywords)
        }
        
    def _verificar_correspondencia_vaga(self, texto, palavras_chave_vaga):
        """
        Verifica correspondência rigorosa com palavras-chave da vaga
        
        Args:
            texto (str): Texto do currículo normalizado
            palavras_chave_vaga (list): Lista de palavras-chave da vaga
            
        Returns:
            float: Pontuação de correspondência (0-10)
        """
        if not palavras_chave_vaga:
            return 0.0
            
        correspondencias = 0
        palavras_importantes_encontradas = []
        
        for palavra_chave in palavras_chave_vaga:
            palavra_norm = self._normalizar_texto(palavra_chave.strip())
            
            # Busca exata da palavra no texto
            if palavra_norm in texto:
                correspondencias += 1
                palavras_importantes_encontradas.append(palavra_chave)
                continue
                
            # Busca por palavras relacionadas/sinônimos
            palavras_relacionadas = []
            
            # Expandir abreviações se aplicável
            if palavra_norm in self.abreviacoes:
                palavras_relacionadas.extend(self.abreviacoes[palavra_norm])
            
            # Verificar se alguma palavra relacionada existe
            for palavra_relacionada in palavras_relacionadas:
                palavra_rel_norm = self._normalizar_texto(palavra_relacionada)
                if palavra_rel_norm in texto:
                    correspondencias += 0.7  # Peso menor para sinônimos
                    palavras_importantes_encontradas.append(f"{palavra_chave} (como {palavra_relacionada})")
                    break
        
        # Calcular pontuação final
        if len(palavras_chave_vaga) == 0:
            return 0.0
            
        pontuacao = (correspondencias / len(palavras_chave_vaga)) * 10
        return min(pontuacao, 10.0)
        
    def definir_palavras_chave_customizadas(self, palavras_chave):
        """
        Define palavras-chave customizadas para análise
        
        Args:
            palavras_chave (list): Lista de palavras-chave personalizadas
        """
        if isinstance(palavras_chave, list):
            self.palavras_chave_default = [p.lower().strip() for p in palavras_chave]
