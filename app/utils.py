def soma_vendas(todas_vendas):
    """
    Soma o valor total das vendas (exceto canceladas), lidando com diferentes formatos de valor_real.

    Args:
        todas_vendas (list): Lista de dicionários de vendas.

    Returns:
        float: Soma total dos valores reais das vendas.
    """
    total = 0.00

    for venda in todas_vendas:
        if venda.get('status') == 'Cancelada':
            continue

        valor = venda.get('valor_real', '')

        # Se já for número, apenas soma
        if isinstance(valor, (int, float)):
            total += valor
            continue

        # Se for string, tenta converter
        if isinstance(valor, str):
            valor_str = valor.strip()

            if not valor_str:
                continue

            try:
                # Trata formatos como "1.234,56"
                match [(',' in valor_str), ('.' in valor_str)]:
                    case [False, True]:
                        total += float(valor_str)
                        continue
                    case [True, False]:
                        valor_normalizado = valor_str.replace(',', '.')
                        total += float(valor_normalizado)
                        continue
                    case [True, True]:
                        posicao_virgula = valor_str.find(',')
                        posicao_ponto = valor_str.find('.')
                        if posicao_virgula < posicao_ponto:
                            valor_normalizado = valor_str.replace(',', '')
                        else:
                            valor_normalizado = valor_str.replace('.', '').replace(',', '.')

                        total += float(valor_normalizado)
                        continue
                    case _:
                        total += float(valor_str)
                        continue
            except ValueError:
                # Ignora se não for possível converter
                continue

    return round(total, 2)
