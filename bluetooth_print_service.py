# bluetooth_print_service.py
"""
Servico de impressao ESC/POS direta via Bluetooth Classic.

Usa o plugin Flutter 'blue_thermal_printer' injetado no build para
comunicar diretamente com a impressora via socket RFCOMM - sem diálogo,
sem PrintHand, sem app intermediario.

Interface identica ao AndroidPrintService para substituicao transparente
em todas as telas (crr_form_screen, crr_list_screen, crr_search_screen).
"""
import os
import base64 as _b64
from flet.controls.base_control import control
from flet.controls.services.service import Service

_QR_JPEG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'qrcode.jpeg'
)


def _load_qr_base64() -> str:
    try:
        with open(_QR_JPEG_PATH, 'rb') as f:
            return _b64.b64encode(f.read()).decode('utf-8')
    except Exception:
        return ''


@control("flet_bluetooth_print")
class BluetoothPrintService(Service):
    """
    Servico Flet que delega impressao ao Dart via flet_bluetooth_print.

    O MAC da impressora e configurado em main.py via local_db
    e passado a cada chamada de print_receipt.
    """

    def __init__(self, mac_impressora: str = ''):
        super().__init__()
        self.mac_impressora = mac_impressora

    async def print_receipt(
        self,
        lines: list,
        signature_base64: str = '',
        condutor_signature_base64: str = '',
        mac_address: str = '',
    ) -> dict:
        """
        Envia cupom diretamente para a impressora Bluetooth via ESC/POS.
        Interface identica ao AndroidPrintService.

        Args:
            mac_address: MAC da impressora; se vazio usa self.mac_impressora.

        Returns:
            {'sucesso': True} ou {'sucesso': False, 'erro': str}
        """
        mac = mac_address or self.mac_impressora
        result = await self._invoke_method(
            "print_receipt",
            {
                "lines": lines,
                "mac_address": mac,
                "signature_base64": signature_base64 or '',
                "qr_base64": _load_qr_base64(),
            },
            timeout=30,
        )
        return result or {
            'sucesso': False, 'erro': 'Sem resposta do servico Dart'
        }

    async def listar_pareados(self) -> list:
        """
        Retorna dispositivos Bluetooth pareados no Android.
        Util para tela de configuracao de impressora.

        Returns:
            Lista de {'nome': str, 'mac': str}
        """
        result = await self._invoke_method("listar_pareados", {}, timeout=10)
        return result or []
