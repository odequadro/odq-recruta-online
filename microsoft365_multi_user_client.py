#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 CLIENTE MICROSOFT 365 MULTI-USUÁRIO
================================================================

Cliente Microsoft 365 aprimorado para suportar múltiplos usuários
da organização O. DE QUADROS:

• Iza: izabella.cordeiro@odequadroservicos.com.br
• Nara: narahyna.barbosa@odequadroservicos.com.br

Usa Application Permissions para acessar emails de qualquer usuário
da organização via Microsoft Graph API.
"""

import json
import os
import requests
from datetime import datetime, timedelta
import msal

class Microsoft365MultiUserClient:
    """
    Cliente Microsoft 365 para múltiplos usuários da ODQ
    """
    
    def __init__(self):
        """
        Inicializar cliente multi-usuário
        """
        # Carregar credenciais Azure
        try:
            from credentials_azure import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
            self.client_id = AZURE_CLIENT_ID
            self.client_secret = AZURE_CLIENT_SECRET  
            self.tenant_id = AZURE_TENANT_ID
        except ImportError:
            raise Exception("❌ Arquivo credentials_azure.py não encontrado")
        
        # Configurar MSAL
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret
        )
        
        # Escopos para Application Permissions
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        # Emails configurados
        self.usuarios = {
            'iza': 'izabella.cordeiro@odequadroservicos.com.br',
            'nara': 'narahyna.barbosa@odequadroservicos.com.br'
        }
        
        print("🔧 Cliente Microsoft 365 Multi-Usuário inicializado")
    
    def _get_access_token(self):
        """
        Obter token de acesso via Application Permissions
        """
        try:
            # Tentar obter token do cache
            result = self.app.acquire_token_silent(self.scopes, account=None)
            
            if not result:
                # Obter novo token via client credentials
                result = self.app.acquire_token_for_client(scopes=self.scopes)
            
            if "access_token" in result:
                return result["access_token"]
            else:
                print(f"❌ Erro ao obter token: {result.get('error_description', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na autenticação: {str(e)}")
            return None
    
    def conectar(self):
        """
        Testar conexão com Microsoft 365
        """
        token = self._get_access_token()
        if token:
            print("✅ Microsoft 365 Multi-Usuário conectado")
            return True
        else:
            print("❌ Falha na conexão Microsoft 365")
            return False
    
    def buscar_emails_usuario(self, email_usuario, filtro_dias=7, limite=50, apenas_nao_lidos=False):
        """
        Buscar emails de um usuário específico
        
        Args:
            email_usuario: Email do usuário (iza ou nara)
            filtro_dias: Buscar emails dos últimos X dias
            limite: Máximo de emails a retornar
            apenas_nao_lidos: Se True, busca apenas emails não lidos
        """
        token = self._get_access_token()
        if not token:
            return []
        
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Resolver nome do usuário para email
            if email_usuario.lower() in self.usuarios:
                email_real = self.usuarios[email_usuario.lower()]
            else:
                email_real = email_usuario
            
            # Montar filtro de data
            data_limite = datetime.now() - timedelta(days=filtro_dias)
            data_filtro = data_limite.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Montar URL
            url = f'https://graph.microsoft.com/v1.0/users/{email_real}/messages'
            
            # Parâmetros base
            params = {
                '$select': 'id,subject,from,receivedDateTime,hasAttachments,bodyPreview,isRead',
                '$filter': f'receivedDateTime ge {data_filtro}',
                '$orderby': 'receivedDateTime desc',
                '$top': limite
            }
            
            # Adicionar filtro para emails não lidos
            if apenas_nao_lidos:
                params['$filter'] += ' and isRead eq false'
            
            print(f"📧 Buscando emails de {email_real}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('value', [])
                print(f"✅ {len(emails)} emails encontrados para {email_real}")
                return emails
            else:
                print(f"❌ Erro ao buscar emails: {response.status_code}")
                print(f"Resposta: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Erro na busca de emails: {str(e)}")
            return []
    
    def contar_emails_nao_lidos(self, email_usuario):
        """
        Contar emails não lidos de um usuário
        """
        token = self._get_access_token()
        if not token:
            return 0
        
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Resolver nome do usuário para email
            if email_usuario.lower() in self.usuarios:
                email_real = self.usuarios[email_usuario.lower()]
            else:
                email_real = email_usuario
            
            # URL para contar emails não lidos
            url = f'https://graph.microsoft.com/v1.0/users/{email_real}/mailFolders/Inbox'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                nao_lidos = data.get('unreadItemCount', 0)
                total = data.get('totalItemCount', 0)
                return nao_lidos, total
            else:
                print(f"❌ Erro ao contar emails: {response.status_code}")
                return 0, 0
                
        except Exception as e:
            print(f"❌ Erro ao contar emails: {str(e)}")
            return 0, 0
    
    def obter_estatisticas_todos_usuarios(self):
        """
        Obter estatísticas de todos os usuários configurados
        """
        estatisticas = {}
        
        for nome, email in self.usuarios.items():
            try:
                nao_lidos, total = self.contar_emails_nao_lidos(email)
                estatisticas[nome] = {
                    'email': email,
                    'nao_lidos': nao_lidos,
                    'total': total
                }
            except Exception as e:
                print(f"❌ Erro ao obter estatísticas de {nome}: {str(e)}")
                estatisticas[nome] = {
                    'email': email,
                    'nao_lidos': 0,
                    'total': 0,
                    'erro': str(e)
                }
        
        return estatisticas
    
    def buscar_emails_todos_usuarios(self, filtro_dias=7, limite=50):
        """
        Buscar emails de todos os usuários configurados
        """
        todos_emails = {}
        
        for nome, email in self.usuarios.items():
            try:
                emails = self.buscar_emails_usuario(
                    email_usuario=email,
                    filtro_dias=filtro_dias,
                    limite=limite
                )
                todos_emails[nome] = emails
                print(f"✅ {len(emails)} emails encontrados para {nome}")
            except Exception as e:
                print(f"❌ Erro ao buscar emails de {nome}: {str(e)}")
                todos_emails[nome] = []
        
        return todos_emails
