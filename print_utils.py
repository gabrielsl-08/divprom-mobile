# print_utils.py
"""
Layout de impressao do CRR para papel termico 56mm (~32 colunas).

Formato:
  - Titulo principal: centralizado
  - Subtitulos de secao: entre linhas DIV, centralizados, caixa alta
  - Labels dos campos: minusculas, alinhados a esquerda
  - Valores: caixa alta
"""

LARGURA = 32
_BASE_URL = "https://divprom.herokuapp.com"

_ACCENT = str.maketrans(
    'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑáàâãäéèêëíìîïóòôõöúùûüçñ',
    'AAAAEEEEEIIIIOOOOOUUUUCNaaaaeeeeeiiiiooooouuuucn'
)


def _T(texto):
    """Remove acentos para compatibilidade com codepage da impressora."""
    return str(texto).translate(_ACCENT)


def _wrap_valor(label, valor, largura=LARGURA):
    """
    Formata 'label: VALOR' quebrando o valor em multiplas linhas se necessario.
    label em minusculas, valor em caixa alta.
    """
    prefixo = f"{label}: "
    valor = _T(str(valor).upper())
    disp = largura - len(prefixo)
    if disp <= 4:
        return [prefixo + valor]
    if len(valor) <= disp:
        return [prefixo + valor]
    linhas = []
    cont = " " * len(prefixo)
    disp_cont = largura - len(cont)
    linhas.append(prefixo + valor[:disp])
    resto = valor[disp:]
    while resto:
        linhas.append(cont + resto[:disp_cont])
        resto = resto[disp_cont:]
    return linhas


def _secao(linhas, titulo, div):
    """Insere um subtitulo de secao entre linhas divisorias, centralizado."""
    linhas.append(div)
    linhas.append(f"__CENTRO__{_T(titulo.upper())}")
    linhas.append(div)


def gerar_linhas_impressao(dados):
    """Gera lista de linhas para impressao de um CRR (papel 56mm)."""
    linhas = []
    DIV = "-" * LARGURA

    crr_num = dados.get('numeroCrr', '').upper()
    qr_url = (
        f"{_BASE_URL}/api/v1/mobile/consulta-publica/"
        f"?numeroCrr={crr_num}"
    )

    # === Titulo principal ===
    linhas.append("__CENTRO__COMP. RECOLH. E REMOCAO")

    # === CRR / DATA / HORA ===
    _secao(linhas, "IDENTIFICACAO DO CRR", DIV)
    linhas += _wrap_valor("numero",  crr_num)
    linhas += _wrap_valor("data",    dados.get('dataFiscalizacao', '-'))
    linhas += _wrap_valor("hora",    dados.get('horaFiscalizacao', '-'))

    # === Veiculo ===
    _secao(linhas, "VEICULO", DIV)
    linhas += _wrap_valor("placa",   dados.get('placa', '-'))
    linhas += _wrap_valor("chassi",  dados.get('chassi', '-'))
    linhas += _wrap_valor("marca",   dados.get('marca', '-'))
    linhas += _wrap_valor("modelo",  dados.get('modelo', '-'))
    linhas += _wrap_valor("cor",     dados.get('cor', '-'))

    # === Fiscalizacao ===
    _secao(linhas, "FISCALIZACAO", DIV)
    linhas += _wrap_valor("local",   dados.get('localFiscalizacao', '-'))
    linhas += _wrap_valor("medida",  dados.get('medidaAdministrativa', '-'))

    aits_v = dados.get('aits', [])
    if aits_v:
        linhas += _wrap_valor("AITs", ', '.join(a.upper() for a in aits_v))

    enquadr = dados.get('enquadramentos', [])
    if enquadr:
        linhas += _wrap_valor("enquadr.", ', '.join(enquadr))

    if dados.get('veiculoAbandonado', False):
        linhas.append("  ART.279 - ABANDONADO")

    # === Outros dados ===
    _secao(linhas, "OUTROS DADOS", DIV)
    linhas += _wrap_valor("patio",    dados.get('localPatio', '-'))
    linhas += _wrap_valor("guincho",  dados.get('placaGuincho', '-'))
    linhas += _wrap_valor("encarr.",  dados.get('encarregado', '-'))
    linhas += _wrap_valor("agente",   dados.get('matriculaAgente', '-'))
    linhas.append("__AGENTE_SIG__")

    # === Condutor ===
    _secao(linhas, "CONDUTOR", DIV)
    if dados.get('nomeCondutor'):
        linhas += _wrap_valor("nome", dados.get('nomeCondutor', '-'))
        linhas += _wrap_valor("cpf",  dados.get('cpfCondutor', '-'))
    else:
        linhas.append("ausente")

    if dados.get('observacao'):
        _secao(linhas, "OBSERVACAO", DIV)
        linhas += _wrap_valor("obs.", dados.get('observacao', ''))

    # === Assinatura do condutor ===
    linhas.append(DIV)
    linhas.append("assinatura do condutor:")
    linhas.append("__SPACER__")
    linhas.append("_" * LARGURA)

    situacao = dados.get('situacaoEntrega', '')
    if situacao:
        linhas.append(_T(situacao.upper()))

    # === QR Code ===
    linhas.append(DIV)
    linhas.append("para liberacao do veiculo,")
    linhas.append("acesse o QR code abaixo:")
    linhas.append("__QR_STATIC__")
    linhas.append(DIV)
    return linhas


def gerar_texto_impressao(dados):
    """Gera texto formatado para impressao de um CRR."""
    return "\n".join(gerar_linhas_impressao(dados))
