# android_print_service.py
"""
Servico de impressao via Android Print Framework.

Abre o dialogo nativo de impressao do Android com um PDF gerado do cupom.
Compativel com 'Datecs Print Service' (e qualquer outra impressora registrada).

Requer no celular:
  - App 'Datecs Print Service' instalado (Google Play)
  - Impressora DDP-250 pareada via Bluetooth ou USB
"""
from flet.controls.base_control import control
from flet.controls.services.service import Service


@control("flet_android_print")
class AndroidPrintService(Service):
    """Servico para impressao via dialogo nativo do Android."""

    async def print_receipt(
        self,
        lines: list,
        signature_base64: str = '',
        condutor_signature_base64: str = '',
    ) -> dict:
        """
        Gera um PDF do cupom e abre o dialogo de impressao do Android.

        O Datecs Print Service intercepta a solicitacao e envia para a
        impressora DDP-250 via Bluetooth ou USB automaticamente.

        Args:
            lines: Lista de strings com o conteudo do cupom.
            signature_base64: Assinatura do agente em base64 (opcional).
            condutor_signature_base64: Assinatura do condutor em base64 (opcional).

        Returns:
            {'sucesso': True} se o usuario confirmou a impressao,
            {'sucesso': False} se cancelou ou ocorreu erro.
        """
        result = await self._invoke_method(
            "print_receipt",
            {
                "lines": lines,
                "signature_base64": signature_base64,
                "condutor_signature_base64": condutor_signature_base64,
            },
            timeout=120,  # usuario precisa interagir com o dialogo
        )
        return result or {'sucesso': False, 'erro': 'Sem resposta'}
