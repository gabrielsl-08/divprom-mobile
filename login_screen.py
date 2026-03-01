# login_screen.py
"""
Tela de Login - somente online.
Fluxo:
  1. Primeira vez: codigo de ativacao + matricula + senha
  2. Proximas vezes: matricula + senha (valida no servidor)
  3. Se senha nao alterada: redireciona para tela de alteracao
"""
import flet as ft


def build_login_screen(page: ft.Page, on_login_success, on_senha_change_required, api_client, local_db):
    """Constroi a tela de login"""

    credenciais = local_db.obter_credenciais() if local_db else None
    dispositivo_ativado = (
        credenciais
        and credenciais.get('api_key')
        and credenciais['api_key'] != 'offline'
    )

    codigo_field = ft.TextField(
        label="Codigo de Ativacao",
        hint_text="Digite o codigo de 6 digitos",
        prefix_icon=ft.Icons.VPN_KEY,
        border_radius=8, text_size=18,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=6,
        visible=not dispositivo_ativado,
    )

    matricula_field = ft.TextField(
        label="Matricula do Agente",
        hint_text="Digite sua matricula",
        prefix_icon=ft.Icons.BADGE,
        border_radius=8, text_size=14,
    )

    senha_field = ft.TextField(
        label="Senha", hint_text="Digite sua senha",
        prefix_icon=ft.Icons.LOCK,
        border_radius=8, password=True,
        can_reveal_password=True, text_size=14,
    )

    status_text = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)
    loading = ft.ProgressRing(visible=False, width=24, height=24)

    info_ativacao = ft.Container(
        content=ft.Text(
            "Solicite o codigo de ativacao ao administrador",
            size=11, color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        ),
        visible=not dispositivo_ativado,
    )

    info_dispositivo = ft.Container(
        content=ft.Text(
            f"Dispositivo: {credenciais.get('nome', '')}" if credenciais else "",
            size=11, color=ft.Colors.GREEN_700,
            text_align=ft.TextAlign.CENTER,
        ),
        visible=dispositivo_ativado,
    )

    def fazer_login(e):
        matricula = matricula_field.value.strip()
        senha = senha_field.value or ''

        if not dispositivo_ativado:
            codigo = codigo_field.value.strip()
            if not codigo or len(codigo) != 6:
                status_text.value = "Digite o codigo de 6 digitos"
                status_text.color = ft.Colors.RED
                page.update()
                return

        if not matricula:
            status_text.value = "Digite sua matricula"
            status_text.color = ft.Colors.RED
            page.update()
            return

        if not senha:
            status_text.value = "Digite sua senha"
            status_text.color = ft.Colors.RED
            page.update()
            return

        loading.visible = True
        status_text.value = "Conectando..."
        status_text.color = ft.Colors.BLUE
        page.update()

        if not dispositivo_ativado:
            _fazer_ativacao(matricula, senha)
        else:
            _fazer_login_normal(matricula, senha)

    def _fazer_ativacao(matricula, senha):
        codigo = codigo_field.value.strip()
        try:
            resultado = api_client.ativar_dispositivo(codigo, matricula, senha)

            if resultado.get('sucesso'):
                dispositivo = resultado['dispositivo']
                api_key = dispositivo.get('api_key', '')

                local_db.salvar_credenciais(
                    matricula, api_key,
                    dispositivo.get('nome', matricula)
                )
                local_db.salvar_config('ativado_por_codigo', '1')
                api_client.set_api_key(api_key)
                api_client.set_matricula(matricula)

                from datetime import datetime
                local_db.salvar_config(
                    'sessao_inicio', datetime.now().isoformat()
                )

                # Baixa e salva assinatura do agente
                assinatura_url = resultado.get('assinatura_url')
                if assinatura_url:
                    try:
                        b64 = api_client.baixar_imagem_base64(assinatura_url)
                        local_db.salvar_config('assinatura_base64', b64)
                    except Exception:
                        pass

                status_text.value = "Dispositivo ativado!"
                status_text.color = ft.Colors.GREEN
                loading.visible = False
                page.update()

                import time
                time.sleep(1)

                # Verifica se precisa alterar senha
                if not resultado.get('senha_alterada', True):
                    on_senha_change_required(matricula)
                else:
                    on_login_success(dispositivo)
            else:
                erro = resultado.get('erro', 'Codigo invalido')
                status_text.value = erro
                status_text.color = ft.Colors.RED
                loading.visible = False
                page.update()

        except Exception as ex:
            status_text.value = f"Erro: {type(ex).__name__}: {ex}"
            status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()

    def _fazer_login_normal(matricula, senha):
        cred = local_db.obter_credenciais()
        if not cred or not cred.get('api_key'):
            status_text.value = "Dispositivo nao ativado"
            status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()
            return

        matricula_ativacao = cred.get('identificador', '')
        if matricula != matricula_ativacao:
            status_text.value = "Matricula incorreta"
            status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()
            return

        try:
            resultado = api_client.validar_login(
                cred['api_key'], matricula, senha
            )
            if not resultado.get('sucesso'):
                erro = resultado.get('erro', 'Login invalido')
                status_text.value = erro
                status_text.color = ft.Colors.RED
                loading.visible = False
                page.update()
                return
        except Exception as ex:
            status_text.value = f"Erro: {type(ex).__name__}: {ex}"
            status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()
            return

        api_client.set_api_key(cred['api_key'])
        api_client.set_matricula(matricula)

        from datetime import datetime
        local_db.salvar_config('sessao_inicio', datetime.now().isoformat())

        # Baixa e salva assinatura do agente
        assinatura_url = resultado.get('agente', {}).get('assinatura_url')
        if assinatura_url:
            try:
                b64 = api_client.baixar_imagem_base64(assinatura_url)
                local_db.salvar_config('assinatura_base64', b64)
            except Exception:
                pass

        status_text.value = "Login realizado!"
        status_text.color = ft.Colors.GREEN
        loading.visible = False
        page.update()

        import time
        time.sleep(0.5)

        # Verifica se precisa alterar senha
        if not resultado.get('senha_alterada', True):
            on_senha_change_required(matricula)
        else:
            on_login_success({'nome': cred.get('nome', '')})

    subtitulo = (
        "Digite sua matricula para continuar"
        if dispositivo_ativado
        else "Ative o dispositivo para comecar"
    )

    return ft.Container(
        content=ft.Column(controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.DIRECTIONS_CAR, size=50, color=ft.Colors.WHITE),
                    ft.Text("DivProm Mobile", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(subtitulo, size=11, color=ft.Colors.WHITE70),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=ft.Colors.BLUE,
                padding=ft.padding.only(top=40, bottom=25, left=20, right=20),
                border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
                width=float("inf"),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=15),
                    info_dispositivo,
                    codigo_field,
                    info_ativacao,
                    ft.Container(height=8),
                    matricula_field,
                    ft.Container(height=8),
                    senha_field,
                    ft.Container(height=15),
                    ft.Row([loading, status_text], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        "Ativar e Entrar" if not dispositivo_ativado else "Entrar",
                        icon=ft.Icons.VPN_KEY if not dispositivo_ativado else ft.Icons.LOGIN,
                        on_click=fazer_login,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        width=200, height=42,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=ft.padding.symmetric(horizontal=20),
            ),
            ft.Container(expand=True),
            ft.Container(
                content=ft.Text("v1.0 - DivProm 2025", size=10, color=ft.Colors.GREY_500),
                padding=ft.padding.only(bottom=15),
                alignment=ft.Alignment(0, 0),
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO),
        expand=True, bgcolor=ft.Colors.GREY_50,
    )
