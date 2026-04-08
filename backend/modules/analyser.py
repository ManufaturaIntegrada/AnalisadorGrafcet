# FERRAMENTA EDUCACIONAL ORIENTATIVA PARA ALUNOS DE GRADUAÇÃO
# NA DISCIPLINA DE MANUFATURA INTEGRADA DA UTFPR
#     Copyright (C) 2025
# Alunos: Jhulia Andrade de Souza Nogueira e Henrique Marques Dias Chaves
# Orientador: Prof. Dr. Sidney Carlos Gasoto
# Banca: Prof. Dr. Luiz Carlos de Abreu Rodrigues e Prof. Dr. Márcio Alves Sodré de Souza
# Palavras-chave: manufatura integrada; programação de CLPs; interface de usuário; ferramenta educacional.
# Data da defesa: 27/11/2025

import xml.etree.ElementTree as ET

def extrair_namespace(root):
    if '}' in root.tag:
        return root.tag.split('}')[0][1:]
    return ''

def verificar_etapa_inicial(root, ns):
    path = f".//{tag(ns, 'step')}[@initialStep='true']"
    initial_steps = root.findall(path)
    if len(initial_steps) == 0:
        return {'status': 'error', 'message': 'O modelo não possui nenhuma etapa inicial.'}
    if len(initial_steps) > 1:
        names = [s.get('name', 'SemNome') for s in initial_steps]
        return {'status': 'error', 'message': f'Há {len(initial_steps)} etapas iniciais: {", ".join(names)}.'}
    return {'status': 'success', 'message': 'O modelo possui exatamente uma etapa inicial.'}


def verificar_transicoes_vazias(root, ns):
    path = f".//{{{ns}}}transition"
    transicoes = root.findall(path)
    sem_condicao = []
    for trans in transicoes:
        cond = trans.find(f"./{{{ns}}}condition")
        if cond is None:
            sem_condicao.append(trans.get("localId", "SemID"))
            continue

        inline_body = cond.find(f".//{{{ns}}}body")
        if inline_body is not None and inline_body.text and inline_body.text.strip():
            continue

        connection = cond.find(f".//{{{ns}}}connection")
        if connection is not None and connection.get("refLocalId"):
            continue

        sem_condicao.append(trans.get("localId", "SemID"))

    if sem_condicao:
        return {'status': 'warning', 'message': f'Transições sem condição explícita: {", ".join(sem_condicao)}'}
    return {'status': 'success', 'message': 'Todas as transições possuem condição definida.'}


def verificar_etapas_sem_acao(root):
    acoes_definidas = [a.get("name") for a in root.iter() if a.tag.endswith("action")]

    etapas = [e for e in root.iter() if e.tag.endswith("step")]
    etapas_sem_acao = []

    for etapa in etapas:
        step_id = etapa.get("localId", "?")
        step_name = etapa.get("name", "SemNome")

        atribuicoes = [attr.text for attr in etapa.iter() if attr.tag.endswith("attribute")]
        acao_ref = None
        for attr_text in atribuicoes:
            if attr_text and attr_text.startswith("A_"):
                acao_ref = attr_text.strip()
                break

        if not acao_ref:
            etapas_sem_acao.append(f'{step_id} ({step_name}) - sem referência de ação')
            continue

        if acao_ref not in acoes_definidas:
            etapas_sem_acao.append(f'{step_id} ({step_name}) → ação "{acao_ref}" não encontrada')
            continue

    if etapas_sem_acao:
        return {
            'status': 'warning',
            'message': f'Etapas sem ações definidas ou com referência incorreta: {", ".join(etapas_sem_acao)}'
        }

    return {
        'status': 'success',
        'message': 'Todas as etapas referenciam ações existentes e válidas.'
    }

def verificar_acoes_orfas(root):
    acoes_definidas = [a.get("name") for a in root.iter() if a.tag.endswith("action")]
    atributos = [attr.text for attr in root.iter() if attr.tag.endswith("attribute") and attr.text and attr.text.startswith("A_")]
    acoes_usadas = set(atributos)
    acoes_orfas = [a for a in acoes_definidas if a not in acoes_usadas]

    if acoes_orfas:
        return {
            'status': 'warning',
            'message': f'Ações não utilizadas por nenhuma etapa: {", ".join(acoes_orfas)}'
        }
    return {
        'status': 'success',
        'message': 'Todas as ações estão associadas a alguma etapa.'
    }


def verificar_transicoes_orfas(root, ns):
    transicoes = root.findall(f".//{{{ns}}}transition")
    todas_ids = {el.get("localId") for el in root.findall(f".//*[@localId]")}
    conexoes = root.findall(f".//{{{ns}}}connection")

    origem_por_trans = {}
    destino_por_trans = {}

    for t in transicoes:
        local_id = t.get("localId")
        conexoes_internas = t.findall(f".//{{{ns}}}connection[@refLocalId]")
        if conexoes_internas:
            origem_por_trans[local_id] = [c.get("refLocalId") for c in conexoes_internas]

    for conn in conexoes:
        ref = conn.get("refLocalId")
        if ref in todas_ids:
            destino_por_trans.setdefault(ref, []).append(conn)

    sem_origem = []
    sem_destino = []
    for t in transicoes:
        tid = t.get("localId")
        if tid not in origem_por_trans:
            sem_origem.append(tid)
        if tid not in destino_por_trans:
            sem_destino.append(tid)

    msgs = []
    if sem_origem:
        msgs.append(f'Sem origem: {", ".join(sem_origem)}')
    if sem_destino:
        msgs.append(f'Sem destino: {", ".join(sem_destino)}')

    if msgs:
        return {
            'status': 'warning',
            'message': 'Transições possivelmente incompletas → ' + " | ".join(msgs)
        }

    return {'status': 'success', 'message': 'Todas as transições possuem origem e destino válidos.'}

def verificar_conexoes_orfas(root, ns):
    todas_ids = {el.get("localId") for el in root.findall(f".//*[@localId]")}
    orfas = []
    for conn in root.findall(f".//{{{ns}}}connection"):
        ref = conn.get("refLocalId")
        if ref and ref not in todas_ids:
            orfas.append(ref)
    if orfas:
        return {'status': 'warning', 'message': f'Conexões apontando para elementos inexistentes: {", ".join(orfas)}'}
    return {'status': 'success', 'message': 'Todas as conexões apontam para elementos existentes.'}


def analisar_arquivo_grafcet(caminho_do_arquivo):
    try:
        tree = ET.parse(caminho_do_arquivo)
        root = tree.getroot()
        ns = extrair_namespace(root)

        resultados = [
            verificar_etapa_inicial(root, ns),
            verificar_transicoes_vazias(root, ns),
            verificar_etapas_sem_acao(root),
            verificar_acoes_orfas(root),
            verificar_transicoes_orfas(root, ns),
            verificar_conexoes_orfas(root, ns)
        ]

        return {
            'success': True,
            'resultados': resultados
        }

    except ET.ParseError:
        return {'success': False, 'error': 'O arquivo não é um XML válido ou está corrompido.'}
    except Exception as e:
        return {'success': False, 'error': f'Erro inesperado ao processar: {str(e)}'}
    
def tag(ns, name):
    return f"{{{ns}}}{name}" if ns else name