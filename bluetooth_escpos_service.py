# bluetooth_escpos_service.py
"""
Servico experimental de impressao ESC/POS via Bluetooth usando PyJNIus.

PyJNIus permite chamar classes Java/Android diretamente do Python via JNI.
Esta abordagem eh alternativa ao AndroidPrintService (dialogo nativo do Android).

REQUER:
  - PyJNIus compilado para Android ARM64 (incluido no build do Flet)
  - Impressora termica Bluetooth pareada no Android
  - Permissoes: BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN

USO:
    from bluetooth_escpos_service import BluetoothEscposService
    svc = BluetoothEscposService()
    ok = svc.imprimir(linhas, mac_address="AA:BB:CC:DD:EE:FF")
"""

import sys
import platform

# Detecta se esta rodando em Android
_ANDROID = hasattr(sys, 'getandroidapilevel') or platform.system() == 'Linux' and 'ANDROID_ROOT' in __import__('os').environ


def _get_pyjnius():
    """Tenta importar jnius. Retorna None se nao disponivel."""
    try:
        import jnius
        return jnius
    except ImportError:
        return None
    except Exception:
        return None


class BluetoothEscposService:
    """
    Impressao ESC/POS direta via Bluetooth Classic usando PyJNIus.

    Fluxo:
      1. Obtem BluetoothAdapter do Android
      2. Abre socket RFCOMM para o MAC da impressora
      3. Envia bytes ESC/POS
      4. Fecha socket
    """

    # UUID padrao para Serial Port Profile (SPP) - usado por impressoras termicas
    SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"

    def __init__(self):
        self._disponivel = None  # None = nao testado ainda

    def disponivel(self) -> bool:
        """Verifica se PyJNIus esta disponivel neste ambiente."""
        if self._disponivel is None:
            self._disponivel = _ANDROID and _get_pyjnius() is not None
        return self._disponivel

    def listar_pareados(self) -> list[dict]:
        """
        Retorna lista de dispositivos Bluetooth pareados.
        Cada item: {'nome': str, 'mac': str}
        Retorna [] se PyJNIus nao disponivel.
        """
        if not self.disponivel():
            return []
        try:
            jnius = _get_pyjnius()
            BluetoothAdapter = jnius.autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None:
                return []
            dispositivos = adapter.getBondedDevices().toArray()
            return [
                {'nome': d.getName(), 'mac': d.getAddress()}
                for d in dispositivos
            ]
        except Exception as e:
            print(f"[BT] Erro ao listar pareados: {e}")
            return []

    def imprimir(self, linhas: list[str], mac_address: str) -> dict:
        """
        Envia conteudo ESC/POS para impressora via Bluetooth.

        Args:
            linhas: Lista de strings (cada uma vira uma linha impressa)
            mac_address: MAC da impressora (ex: "AA:BB:CC:DD:EE:FF")

        Returns:
            {'sucesso': True} ou {'sucesso': False, 'erro': str}
        """
        if not self.disponivel():
            return {
                'sucesso': False,
                'erro': 'PyJNIus nao disponivel neste ambiente (apenas Android)',
            }

        socket = None
        stream = None
        try:
            jnius = _get_pyjnius()

            # Obtem adaptador Bluetooth
            BluetoothAdapter = jnius.autoclass('android.bluetooth.BluetoothAdapter')
            UUID = jnius.autoclass('java.util.UUID')

            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None:
                return {'sucesso': False, 'erro': 'Bluetooth nao disponivel no dispositivo'}
            if not adapter.isEnabled():
                return {'sucesso': False, 'erro': 'Bluetooth desligado'}

            # Obtem dispositivo pelo MAC
            device = adapter.getRemoteDevice(mac_address.upper())

            # Abre socket RFCOMM (Serial Port Profile)
            uuid = UUID.fromString(self.SPP_UUID)
            socket = device.createRfcommSocketToServiceRecord(uuid)
            socket.connect()
            stream = socket.getOutputStream()

            # Monta bytes ESC/POS
            dados = self._gerar_escpos(linhas)
            stream.write(dados)
            stream.flush()

            return {'sucesso': True}

        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

        finally:
            try:
                if stream:
                    stream.close()
            except Exception:
                pass
            try:
                if socket:
                    socket.close()
            except Exception:
                pass

    def _gerar_escpos(self, linhas: list[str]) -> bytes:
        """
        Converte lista de linhas em bytes ESC/POS para impressora termica.

        Comandos usados:
          ESC @ = inicializa impressora
          ESC a 1 = centraliza texto
          ESC a 0 = alinha esquerda
          GS V 66 = corta papel (alimenta 3mm antes de cortar)
        """
        ESC = b'\x1b'
        GS  = b'\x1d'

        INIT       = ESC + b'@'          # inicializa
        ALIGN_CTR  = ESC + b'a\x01'     # centraliza
        ALIGN_LEFT = ESC + b'a\x00'     # esquerda
        BOLD_ON    = ESC + b'E\x01'
        BOLD_OFF   = ESC + b'E\x00'
        FEED       = b'\n'
        CUT        = GS  + b'V\x42\x03' # corte parcial com alimentacao

        buf = bytearray()
        buf += INIT
        buf += ALIGN_LEFT

        separadores = {'=' * 26, '-' * 26}

        for linha in linhas:
            # Tokens especiais usados em print_utils.py
            if linha in ('__AGENTE_SIG__', '__SPACER__', '__QR_CODE__'):
                buf += FEED * 3  # espaco em branco para assinatura/qr manual
                continue

            if linha in separadores:
                buf += BOLD_ON
                buf += linha.encode('ascii', errors='replace') + FEED
                buf += BOLD_OFF
            else:
                buf += linha.encode('latin-1', errors='replace') + FEED

        buf += FEED * 4  # alimenta papel antes de cortar
        buf += CUT
        return bytes(buf)
