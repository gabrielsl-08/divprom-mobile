# senha_screen.py
"""
Tela de alteracao de senha obrigatoria.
Exibida quando o agente faz login com a senha padrao 'admin'.
"""
import flet as ft


def build_senha_screen(page, on_senha_alterada, api_client, local_db, matricula):
    """Constroi a tela de alteracao de senha"""

    nova_senha_field = ft.TextField(
        label="Nova Senha", password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_RESET,
        border_radius=8, text_size=14,
    )
    confirmar_senha_field = ft.TextField(
        label="Confirmar Nova Senha", password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK,
        border_radius=8, text_size=14,
    )
    status_text = ft.Text(
        "", size=13, text_align=ft.TextAlign.CENTER,
    )
    loading = ft.ProgressRing(visible=False, width=24, height=24)

    def alterar(e):
        nova = nova_senha_field.value or ''
        confirmar = confirmar_senha_field.value or ''

        if not nova or len(nova) < 4:
            status_text.value = "Senha deve ter no minimo 4 caracteres"
            status_text.color = ft.Colors.RED
            page.update()
            return
        if nova == "admin":
            status_text.value = "A nova senha nao pode ser 'admin'"
            status_text.color = ft.Colors.RED
            page.update()
            return
        if nova != confirmar:
            status_text.value = "As senhas nao coincidem"
            status_text.color = ft.Colors.RED
            page.update()
            return

        loading.visible = True
        status_text.value = "Alterando..."
        status_text.color = ft.Colors.BLUE
        page.update()

        try:
            resultado = api_client.alterar_senha(
                matricula, nova,
            )
            if resultado.get('sucesso'):
                status_text.value = "Senha alterada com sucesso!"
                status_text.color = ft.Colors.GREEN
                loading.visible = False
                page.update()
                import time
                time.sleep(1)
                on_senha_alterada()
            else:
                erro = resultado.get('erro', 'Erro ao alterar')
                status_text.value = erro
                status_text.color = ft.Colors.RED
                loading.visible = False
                page.update()
        except Exception:
            status_text.value = "Sem conexao com o servidor"
            status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()

    return ft.Container(
        content=ft.Column(controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.LOCK_RESET,
                        size=50, color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "Alterar Senha", size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "Altere a senha padrao antes de continuar",
                        size=11, color=ft.Colors.WHITE70,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=ft.Colors.ORANGE,
                padding=ft.padding.only(
                    top=40, bottom=25, left=20, right=20,
                ),
                border_radius=ft.border_radius.only(
                    bottom_left=20, bottom_right=20,
                ),
                width=float("inf"),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    nova_senha_field,
                    ft.Container(height=8),
                    confirmar_senha_field,
                    ft.Container(height=15),
                    ft.Row(
                        [loading, status_text],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        "Alterar Senha",
                        icon=ft.Icons.CHECK,
                        on_click=alterar,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        width=200, height=42,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=ft.padding.symmetric(horizontal=20),
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO),
        expand=True, bgcolor=ft.Colors.GREY_50,
    )
