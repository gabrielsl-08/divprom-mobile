# print_utils.py
"""
Funcao compartilhada para gerar texto de impressao do CRR.
Usada pelo formulario (pos-criacao) e pela listagem (reimpressao).
"""


def gerar_linhas_impressao(dados):
    """Gera lista de linhas para impressao de um CRR."""
    linhas = []
    SEP = "=" * 26
    DIV = "-" * 26
    linhas.append(SEP)
    linhas.append("COMPROVANTE DE RECOLHIMENTO E REMOCAO")
    linhas.append(SEP)
    linhas.append(f"NUMERO: {dados.get('numeroCrr', '').upper()}")
    linhas.append(f"DATA: {dados.get('dataFiscalizacao', '').upper()}")
    linhas.append(f"HORA: {dados.get('horaFiscalizacao', '').upper()}")
    linhas.append(DIV)
    linhas.append("VEICULO:")
    linhas.append(f"  PLACA: {dados.get('placa', '-').upper()}")
    linhas.append(f"  CHASSI: {dados.get('chassi', '-').upper()}")
    linhas.append(f"  MARCA: {dados.get('marca', '-').upper()}")
    linhas.append(f"  MODELO: {dados.get('modelo', '-').upper()}")
    linhas.append(f"  COR: {dados.get('cor', '-').upper()}")
    linhas.append(DIV)
    linhas.append("FISCALIZACAO:")
    linhas.append(f"  LOCAL: {dados.get('localFiscalizacao', '-').upper()}")
    linhas.append(f"  MEDIDA: {dados.get('medidaAdministrativa', '-').upper()}")
    linhas.append(DIV)
    aits_v = dados.get('aits', [])
    if aits_v:
        aits_str = ', '.join(a.upper() for a in aits_v)
        linhas.append(f"  AITs: {aits_str}")
    enquadr = dados.get('enquadramentos', [])
    if enquadr:
        linhas.append(f"  ENQUADR.: {', '.join(enquadr)}")
    if dados.get('veiculoAbandonado', False):
        linhas.append("  ART.279 - ABANDONADO")
    linhas.append(DIV)
    linhas.append("OUTROS DADOS:")
    linhas.append(f"  PATIO: {dados.get('localPatio', '').upper()}")
    linhas.append(f"  GUINCHO: {dados.get('placaGuincho', '-').upper()}")
    linhas.append(f"  ENCARREGADO: {dados.get('encarregado', '-').upper()}")
    linhas.append(f"  AGENTE: {dados.get('matriculaAgente', '-').upper()}")
    linhas.append("__AGENTE_SIG__")
    linhas.append(DIV)
    linhas.append("CONDUTOR:")
    if dados.get('nomeCondutor'):
        linhas.append(f"  NOME: {dados.get('nomeCondutor', '-').upper()}")
        linhas.append(f"  CPF: {dados.get('cpfCondutor', '-').upper()}")
    else:
        linhas.append("  AUSENTE")
    if dados.get('observacao'):
        linhas.append(DIV)
        linhas.append(f"OBS: {dados.get('observacao', '').upper()}")
    linhas.append(DIV)
    linhas.append("Assinatura do Condutor")
    linhas.append("__SPACER__")
    linhas.append("__________________________")
    situacao = dados.get('situacaoEntrega', '')
    if situacao:
        linhas.append(situacao)
    linhas.append(DIV)
    linhas.append("Para liberacao do veiculo")
    linhas.append("removido, acesse:")
    linhas.append("__QR_CODE__")
    linhas.append(SEP)
    return linhas


def gerar_texto_impressao(dados):
    """Gera texto formatado para impressao de um CRR."""
    return "\n".join(gerar_linhas_impressao(dados))
