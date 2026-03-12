# api_client.py
"""
Cliente HTTP para comunicacao com a API do DivProm.
Modo online apenas - sincrono (sem dependencias async).
"""
import httpx
from typing import Optional, Dict, Any


class ApiClient:
    """Cliente para comunicacao com a API Mobile do DivProm"""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1/mobile"):
        self.base_url = base_url.rstrip('/')
        self.api_key: Optional[str] = None
        self.matricula: Optional[str] = None
        self.timeout = 10.0

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.matricula:
            headers["X-Matricula"] = self.matricula
        return headers

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def set_matricula(self, matricula: str):
        self.matricula = matricula

    def ativar_dispositivo(self, codigo: str, matricula: str = "", senha: str = "") -> Dict[str, Any]:
        """Ativa o dispositivo usando o codigo de ativacao do admin."""
        with httpx.Client(timeout=self.timeout, verify=False) as client:
            response = client.post(
                f"{self.base_url}/ativar/",
                json={"codigo": codigo, "matricula": matricula, "senha": senha},
                headers={"Content-Type": "application/json"}
            )
            return response.json()

    def validar_login(self, api_key: str, matricula: str, senha: str) -> Dict[str, Any]:
        """Valida login no servidor: verifica api_key + matricula + senha."""
        try:
            with httpx.Client(timeout=self.timeout, verify=False) as client:
                response = client.post(
                    f"{self.base_url}/validar-login/",
                    json={"api_key": api_key, "matricula": matricula, "senha": senha},
                    headers={"Content-Type": "application/json"}
                )
                return response.json()
        except Exception as ex:
            return {'sucesso': False, 'erro': f'Sem conexao: {type(ex).__name__}: {ex}'}

    def alterar_senha(self, matricula: str, nova_senha: str) -> Dict[str, Any]:
        """Altera a senha do agente no servidor."""
        try:
            with httpx.Client(timeout=self.timeout, verify=False) as client:
                response = client.post(
                    f"{self.base_url}/alterar-senha/",
                    json={"matricula": matricula, "nova_senha": nova_senha},
                    headers=self._get_headers()
                )
                return response.json()
        except Exception as ex:
            return {'sucesso': False, 'erro': f'Sem conexao: {type(ex).__name__}: {ex}'}

    def listar_crrs(self) -> Dict[str, Any]:
        """Lista os CRRs criados pelo dispositivo/agente."""
        with httpx.Client(timeout=self.timeout, verify=False) as client:
            response = client.get(
                f"{self.base_url}/crr/",
                headers=self._get_headers()
            )
            return response.json()

    def criar_crr(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo CRR no servidor."""
        with httpx.Client(timeout=30.0, verify=False) as client:
            response = client.post(
                f"{self.base_url}/crr/criar/",
                json=dados,
                headers=self._get_headers()
            )
            if response.status_code in [401, 403]:
                return {
                    'sucesso': False,
                    'erro': 'Sem autorizacao. Faca login novamente.'
                }
            try:
                return response.json()
            except Exception:
                return {
                    'sucesso': False,
                    'erro': f'Erro HTTP {response.status_code}'
                }

    def buscar_crrs(self, placa='', marca='', modelo='', data='') -> Dict[str, Any]:
        """Busca CRRs por filtros: placa, marca, modelo, data."""
        params = {}
        if placa:
            params['placa'] = placa
        if marca:
            params['marca'] = marca
        if modelo:
            params['modelo'] = modelo
        if data:
            params['data'] = data
        with httpx.Client(timeout=self.timeout, verify=False) as client:
            response = client.get(
                f"{self.base_url}/crr/buscar/",
                params=params,
                headers=self._get_headers()
            )
            return response.json()

    def atualizar_condutor_crr(self, crr_id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza situacaoEntrega e assinaturaCondutor de um CRR existente."""
        try:
            with httpx.Client(timeout=30.0, verify=False) as client:
                response = client.patch(
                    f"{self.base_url}/crr/{crr_id}/atualizar-condutor/",
                    json=dados,
                    headers=self._get_headers()
                )
                try:
                    return response.json()
                except Exception:
                    return {'sucesso': False, 'erro': f'Erro HTTP {response.status_code}'}
        except Exception as ex:
            return {'sucesso': False, 'erro': f'Sem conexao: {type(ex).__name__}: {ex}'}

    def listar_enquadramentos(self) -> Dict[str, Any]:
        """Lista todos os enquadramentos disponiveis."""
        with httpx.Client(timeout=self.timeout, verify=False) as client:
            response = client.get(
                f"{self.base_url}/enquadramentos/",
                headers=self._get_headers()
            )
            return response.json()

    def baixar_imagem_base64(self, url: str) -> str:
        """Baixa uma imagem da URL e retorna como string base64."""
        import base64
        with httpx.Client(timeout=30.0, verify=False) as client:
            r = client.get(url)
            return base64.b64encode(r.content).decode('utf-8')
