# local_db.py
"""
Banco de dados local - apenas configuracoes e credenciais.
"""
import sqlite3
from typing import Optional, Dict


class LocalDatabase:
    """Gerencia configuracoes locais do dispositivo"""

    def __init__(self, db_path: str = "divprom_mobile.db"):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracao (
                id INTEGER PRIMARY KEY,
                chave TEXT UNIQUE NOT NULL,
                valor TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def salvar_config(self, chave: str, valor: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO configuracao (id, chave, valor)
            VALUES ((SELECT id FROM configuracao WHERE chave = ?), ?, ?)
        ''', (chave, chave, valor))
        conn.commit()
        conn.close()

    def obter_config(self, chave: str) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT valor FROM configuracao WHERE chave = ?', (chave,))
        row = cursor.fetchone()
        conn.close()
        return row['valor'] if row else None

    def salvar_credenciais(self, identificador: str, api_key: str, nome: str):
        self.salvar_config('identificador', identificador)
        self.salvar_config('api_key', api_key)
        self.salvar_config('nome_dispositivo', nome)

    def obter_credenciais(self) -> Optional[Dict[str, str]]:
        identificador = self.obter_config('identificador')
        api_key = self.obter_config('api_key')
        nome = self.obter_config('nome_dispositivo')
        if identificador:
            return {
                'identificador': identificador,
                'api_key': api_key or '',
                'nome': nome or '',
            }
        return None

    def limpar_credenciais(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM configuracao WHERE chave IN "
            "('identificador', 'api_key', 'nome_dispositivo')"
        )
        conn.commit()
        conn.close()
