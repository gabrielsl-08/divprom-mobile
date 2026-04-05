# main.py
"""
DivProm Mobile - Aplicativo de cadastro de CRR (Online Only)
"""
import flet as ft
from api_client import ApiClient
from local_db import LocalDatabase
from login_screen import build_login_screen
from senha_screen import build_senha_screen
from home_screen import build_home_screen
from crr_form_screen import build_crr_form_screen
from crr_list_screen import build_crr_list_screen
from crr_search_screen import build_crr_search_screen
from bluetooth_print_service import BluetoothPrintService
from image_picker_service import ImagePickerService
from print_utils import gerar_linhas_impressao
from print_dialog import mostrar_dialogo_impressao


#API_BASE_URL = "http://localhost:8000/api/v1/mobile"
#API_BASE_URL = "http://192.168.47.2:8000/api/v1/mobile"
API_BASE_URL = "https://systrafcrr-60e7e480b649.herokuapp.com/api/v1/mobile"


async def main(page: ft.Page):
    """Funcao principal do aplicativo"""

    page.title = "SYSTRAF-MOBILE"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # Rastrear página atual para interceptar back button
    page_state = {"atual": "login", "autenticado": False}

    try:
        api_client = ApiClient(API_BASE_URL)
        local_db = LocalDatabase()

        # Impressao ESC/POS direta via Bluetooth (blue_thermal_printer Flutter)
        # MAC padrao: AR-MP2500 pareada. Configuravel via local_db.
        _MAC_PADRAO = "6622302554CA"
        mac = local_db.obter_config('mac_impressora') or _MAC_PADRAO
        print_service = BluetoothPrintService(mac_impressora=mac)
        page.services.append(print_service)

        img_picker = ImagePickerService()
        page.services.append(img_picker)

    except Exception as ex:
        page.add(ft.Text(f"Erro ao inicializar: {ex}", color=ft.Colors.RED))
        page.update()
        return

    # ─────────────────────────────────────────────────────────────────────────
    # Handler para interceptar back button do Android
    # ─────────────────────────────────────────────────────────────────────────
    def mostrar_dialog_confirmacao_saida():
        def confirmar_saida(e):
            import os
            os._exit(0)

        def cancelar_saida(e):
            dlg_saida.open = False
            page.update()

        dlg_saida = ft.AlertDialog(
            title=ft.Text("Sair do Aplicativo?", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Text("Deseja realmente sair do SYSTRAF-MOBILE?", size=14),
            actions=[
                ft.TextButton("Não", on_click=cancelar_saida),
                ft.ElevatedButton(
                    "Sim",
                    on_click=confirmar_saida,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg_saida)
        dlg_saida.open = True
        page.update()

    async def on_confirm_pop(e):
        atual = page_state["atual"]
        if atual == "home":
            mostrar_dialog_confirmacao_saida()
            await e.control.confirm_pop(False)
        elif atual == "login":
            await e.control.confirm_pop(False)
        else:
            mostrar_home()
            await e.control.confirm_pop(False)

    # Impedir que o back button do Android feche/minimize o app
    page.views[0].can_pop = False
    page.views[0].on_confirm_pop = on_confirm_pop

    def mostrar_login():
        try:
            page_state["atual"] = "login"
            page_state["autenticado"] = False
            page.overlay.clear()
            page.controls.clear()
            page.add(build_login_screen(
                page=page, on_login_success=on_login_success,
                on_senha_change_required=mostrar_alterar_senha,
                api_client=api_client, local_db=local_db,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro login: {ex}", color=ft.Colors.RED))
            page.update()

    def mostrar_alterar_senha(matricula):
        try:
            page_state["atual"] = "alterarsenha"
            page.overlay.clear()
            page.controls.clear()
            page.add(build_senha_screen(
                page=page,
                on_senha_alterada=on_senha_alterada,
                api_client=api_client,
                local_db=local_db,
                matricula=matricula,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro senha: {ex}", color=ft.Colors.RED))
            page.update()

    def on_senha_alterada():
        mostrar_home()

    # Cache em memória para dados auxiliares
    cache = {'enquadramentos': []}

    def on_login_success(dispositivo):
        # Pré-carrega enquadramentos após login (síncrono, 1-2s)
        page_state["autenticado"] = True
        try:
            resp = api_client.listar_enquadramentos()
            if isinstance(resp, dict):
                cache['enquadramentos'] = resp.get('enquadramentos', [])
        except Exception:
            cache['enquadramentos'] = []
        mostrar_home()

    def mostrar_busca_crr():
        try:
            page_state["atual"] = "buscacrr"
            page.overlay.clear()
            page.controls.clear()
            page.add(build_crr_search_screen(
                page=page, on_voltar=lambda e: mostrar_home(),
                api_client=api_client, local_db=local_db,
                print_service=print_service,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro busca: {ex}", color=ft.Colors.RED))
            page.update()

    def mostrar_home():
        try:
            page_state["atual"] = "home"
            page.overlay.clear()
            page.controls.clear()
            page.add(build_home_screen(
                page=page,
                on_novo_crr=lambda e: mostrar_formulario_crr(),
                on_meus_crrs=lambda e: mostrar_meus_crrs(),
                on_logout=lambda e: fazer_logout(),
                on_buscar_crr=lambda e: mostrar_busca_crr(),
                api_client=api_client, local_db=local_db,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro home: {ex}", color=ft.Colors.RED))
            page.update()

    def mostrar_formulario_crr():
        try:
            page_state["atual"] = "formulario"
            page.overlay.clear()
            page.controls.clear()
            page.add(build_crr_form_screen(
                page=page, on_voltar=lambda e: mostrar_home(),
                on_salvar=on_crr_salvo,
                api_client=api_client, local_db=local_db,
                print_service=print_service,
                img_picker=img_picker,
                cache=cache,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro form: {ex}", color=ft.Colors.RED))
            page.update()

    def on_crr_salvo(dados, sincronizado):
        page.overlay.clear()
        mostrar_home()
        numero = dados.get('numeroCrr', '')

        def fechar_dlg(ev):
            dlg.open = False
            page.update()

        def imprimir_dlg(ev):
            dlg.open = False
            page.update()

            lines = gerar_linhas_impressao(dados)
            sig_b64 = local_db.obter_config('assinatura_base64') or ''
            condutor_sig = dados.get('assinaturaCondutor', '')

            async def _imprimir():
                await mostrar_dialogo_impressao(
                    page=page,
                    print_service=print_service,
                    lines=lines,
                    signature_base64=sig_b64,
                    condutor_signature_base64=condutor_sig,
                )

            page.run_task(_imprimir)

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE,
                        color=ft.Colors.GREEN, size=30),
                ft.Text(f"CRR {numero}",
                        size=16, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Column([
                ft.Text("CRR salvo com sucesso!", size=14),
            ], tight=True),
            actions=[
                ft.ElevatedButton(
                    "Imprimir", icon=ft.Icons.PRINT,
                    on_click=imprimir_dlg,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE),
                ),
                ft.TextButton("Fechar", on_click=fechar_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def mostrar_meus_crrs():
        try:
            page_state["atual"] = "meuscrrs"
            page.overlay.clear()
            page.controls.clear()
            page.add(build_crr_list_screen(
                page=page, on_voltar=lambda e: mostrar_home(),
                api_client=api_client, local_db=local_db,
                print_service=print_service,
                img_picker=img_picker,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro lista: {ex}", color=ft.Colors.RED))
            page.update()

    def fazer_logout():
        api_client.set_api_key(None)
        local_db.salvar_config('sessao_inicio', '')
        mostrar_login()

    # Migra de versao antiga - limpa banco
    if not local_db.obter_config('ativado_por_codigo'):
        try:
            import os
            db_path = local_db.db_path
            del local_db
            if os.path.exists(db_path):
                os.remove(db_path)
            local_db = LocalDatabase(db_path)
        except Exception:
            local_db.limpar_credenciais()

    # Sempre exige login ao abrir o app (sessao encerra ao fechar)
    mostrar_login()


if __name__ == "__main__":
    import sys
    if "--web" in sys.argv:
        ft.app(main, view=ft.AppView.WEB_BROWSER, port=8550)
    else:
        ft.app(main)
