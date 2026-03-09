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
from android_print_service import AndroidPrintService


API_BASE_URL = "https://systrafcrr-60e7e480b649.herokuapp.com/api/v1/mobile"


async def main(page: ft.Page):
    """Funcao principal do aplicativo"""

    page.title = "DivProm Mobile"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    try:
        api_client = ApiClient(API_BASE_URL)
        local_db = LocalDatabase()
        print_service = AndroidPrintService()
        page.services.append(print_service)
    except Exception as ex:
        page.add(ft.Text(f"Erro ao inicializar: {ex}", color=ft.Colors.RED))
        page.update()
        return

    def mostrar_login():
        try:
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

    def on_login_success(dispositivo):
        mostrar_home()

    def mostrar_busca_crr():
        try:
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
            page.controls.clear()
            page.add(build_crr_form_screen(
                page=page, on_voltar=lambda e: mostrar_home(),
                on_salvar=on_crr_salvo,
                api_client=api_client, local_db=local_db,
                print_service=print_service,
            ))
            page.update()
        except Exception as ex:
            page.controls.clear()
            page.add(ft.Text(f"Erro form: {ex}", color=ft.Colors.RED))
            page.update()

    def on_crr_salvo(dados, sincronizado):
        mostrar_home()
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"CRR {dados['numeroCrr']} salvo!"),
            bgcolor=ft.Colors.GREEN,
        )
        page.snack_bar.open = True
        page.update()

    def mostrar_meus_crrs():
        try:
            page.controls.clear()
            page.add(build_crr_list_screen(
                page=page, on_voltar=lambda e: mostrar_home(),
                api_client=api_client, local_db=local_db,
                print_service=print_service,
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
