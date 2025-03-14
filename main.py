# Alexandre Bueno
# Gabriel Coradin
# Gustavo Coradin
# Matheus Del Zotto


import requests
import json
from datetime import datetime

def converter_data_pdf(data_pdf):
    if data_pdf.startswith("D:"):
        data_pdf = data_pdf[2:]
    data_formatada = datetime.strptime(data_pdf[:14], "%Y%m%d%H%M%S")
    return data_formatada.strftime("%Y-%m-%d %H:%M:%S")

def limpar_texto_pdf(texto):
    text = ''
    for key in texto.keys():
        text += texto[key]
    comandos = ["BT", "ET", "Tf", "Td", "Tj"]
    linhas = text.split("\n")

    texto_limpo = []
    for linha in linhas:
        partes = linha.split()
        if any(parte in comandos for parte in partes):
            trecho = " ".join(partes)
            inicio = trecho.find("(")
            fim = trecho.rfind(")")
            if inicio != -1 and fim != -1:
                texto_limpo.append(trecho[inicio + 1:fim])
    resultado = " ".join(texto_limpo)[:199]
    return resultado
def parseContent(texto):
    comandos = ["BT", "ET", "Tf", "Td", "Tj"]
    linhas = texto.split("\n")

    texto_limpo = []
    for linha in linhas:
        partes = linha.split()
        if any(parte in comandos for parte in partes):
            trecho = " ".join(partes)
            inicio = trecho.find("(")
            fim = trecho.rfind(")")
            if inicio != -1 and fim != -1:
                texto_limpo.append(trecho[inicio + 1:fim])
    resultado = " ".join(texto_limpo)[:199]
    return resultado
def downloadFile(file_url):
    response = requests.get(file_url)

    if response.status_code == 200:
        return response.text
    else:
        print(f"Erro ao baixar o arquivo. Status code: {response.status_code}")



def generate_pdf_object_tree(file_content):
    """
    Gera uma representação em árvore da estrutura de objetos de um arquivo PDF.

    Args:
        file_content (str): Conteúdo do arquivo PDF como string

    Returns:
        dict: Informações da árvore e representação textual
    """
    objects = file_content.split("endobj")

    object_ids = {}
    object_types = {}
    reference_graph = {}
    reverse_references = {}

    for obj in objects:
        obj = obj.strip()
        if not obj:
            continue
        parts = obj.split(" obj", 1)
        if len(parts) > 1:
            header = parts[0].strip().split()
            if len(header) >= 2 and header[-2].isdigit() and header[-1] == "0":
                try:
                    obj_id = int(header[-2])
                    object_ids[obj_id] = obj

                    obj_type = "Desconhecido"
                    if "/Type /" in obj:
                        type_start = obj.find("/Type /") + 7
                        remaining = obj[type_start:]

                        if " " in remaining:
                            obj_type = remaining.split(" ")[0]
                        elif "/" in remaining:
                            obj_type = remaining.split("/")[0]
                        elif ">>" in remaining:
                            obj_type = remaining.split(">>")[0]
                        elif "\n" in remaining:
                            obj_type = remaining.split("\n")[0]
                        else:
                            obj_type = remaining

                        obj_type = obj_type.strip()
                    elif "stream" in obj and "endstream" in obj:
                        obj_type = "Stream"

                    object_types[obj_id] = obj_type

                    reference_graph[obj_id] = []
                    reverse_references[obj_id] = []

                except ValueError:
                    continue

    def find_referencesTree(text):
        result = []
        text = text.replace("[", " [ ").replace("]", " ] ")
        parts = text.split()

        for i in range(len(parts) - 2):
            if parts[i].isdigit() and parts[i+1] == "0" and parts[i+2] == "R":
                try:
                    ref_id = int(parts[i])
                    if ref_id in object_ids:
                        result.append(ref_id)
                except ValueError:
                    continue
        return result

    for obj_id, obj_content in object_ids.items():
        refs = find_referencesTree(obj_content)
        reference_graph[obj_id] = refs

        for ref_id in refs:
            if ref_id in reverse_references:
                reverse_references[ref_id].append(obj_id)

    root_id = 1


    orphans = [obj_id for obj_id in object_ids if not reverse_references[obj_id] and obj_id != root_id]

    def build_tree(node_id, depth=0, visited=None):
        if visited is None:
            visited = set()

        if node_id in visited:
            return f"{'  ' * depth}[Referência cíclica para {node_id}: {object_types.get(node_id, 'Desconhecido')}]\n"

        visited.add(node_id)

        node_type = object_types.get(node_id, "Desconhecido")

        is_stream = False
        if node_id in object_ids:
            content = object_ids[node_id]
            if "stream" in content and "endstream" in content:
                is_stream = True
                if node_type == "Desconhecido":
                    node_type = "Stream"

        node_repr = f"{node_id}: {node_type}"
        if is_stream:
            node_repr += " (stream)"

        result = f"{'  ' * depth}{node_repr}\n"

        children = reference_graph.get(node_id, [])
        for i, child_id in enumerate(children):
            if i < len(children) - 1:
                prefix = "├─ "
            else:
                prefix = "└─ "

            result += f"{'  ' * depth}{prefix}"
            result += build_tree(child_id, depth + 1, visited.copy())[depth+1:]

        return result

    tree_text = ''
    tree_text += build_tree(root_id)

    if orphans:
        tree_text += "\nOBJETOS NÃO REFERENCIADOS:\n"
        for orphan_id in orphans:
            tree_text += build_tree(orphan_id)

    result = {
        "total_objetos": len(object_ids),
        "objeto_raiz": root_id,
        "objetos_orfaos": orphans,
        "arvore_texto": tree_text
    }

    return result

def print_pdf_object_tree(pdf_content):
    """
    Imprime a árvore de objetos de um arquivo PDF.

    Args:
        pdf_content (str): Conteúdo do arquivo PDF como string
    """
    result = generate_pdf_object_tree(pdf_content)
    return result["arvore_texto"]
def validar_sintaxe_objetos(conteudo):
    """Valida a sintaxe dos objetos PDF."""
    linhas = conteudo.splitlines()
    i = 0
    objetos_abertos = 0
    streams_abertos = 0
    sintaxe_valida = True
    mensagem_erro = None

    while i < len(linhas) and sintaxe_valida:
        linha = linhas[i].strip()

        if not linha or linha.startswith("%"):
            i += 1
            continue

        if linha.endswith(" obj"):
            objetos_abertos += 1

        elif linha == "endobj":
            objetos_abertos -= 1
            if objetos_abertos < 0:
                sintaxe_valida = False
                mensagem_erro = "Encontrado 'endobj' sem 'obj' correspondente"

        elif linha == "stream":
            streams_abertos += 1

        elif linha == "endstream":
            streams_abertos -= 1
            if streams_abertos < 0:
                sintaxe_valida = False
                mensagem_erro = "Encontrado 'endstream' sem 'stream' correspondente"

        elif linha.startswith("<<"):
            if not linha.endswith(">>"):
                j = i + 1
                dicionario_fechado = False
                while j < len(linhas) and not dicionario_fechado:
                    if ">>" in linhas[j]:
                        dicionario_fechado = True
                    j += 1

                if not dicionario_fechado:
                    sintaxe_valida = False
                    mensagem_erro = "Dicionário '<< ... >>' não fechado corretamente"

        i += 1
    if objetos_abertos > 0:
        sintaxe_valida = False
        mensagem_erro = f"{objetos_abertos} objeto(s) não fechado(s) com 'endobj'"

    if streams_abertos > 0:
        sintaxe_valida = False
        mensagem_erro = f"{streams_abertos} stream(s) não fechado(s) com 'endstream'"

    if(mensagem_erro):
        erro = mensagem_erro
        return False
    return True

def parse_pdf(file_content):
    objects = file_content.split("endobj")

    metadata = {}
    pages = []
    globalContent = {}
    fonts = set()
    globalSize = 0
    object_types = {}
    page_count = 0
    total_objects = len(objects) - 1
    contentIndex = 0

    for obj in objects:
        if "stream" in obj and "endstream" in obj:
            contentIndex += 1
            start = obj.find("stream") + len("stream")
            end = obj.find("endstream")
            content = obj[start:end].strip()
            globalContent[contentIndex] = content
        if "/Title" in obj:
            metadata["Title"] = obj.split("/Title")[1].split("(")[1].split(")")[0]
        if "/Author" in obj:
            metadata["Author"] = obj.split("/Author")[1].split("(")[1].split(")")[0]
        if "/CreationDate" in obj:
            metadata["CreationDate"] = obj.split("/CreationDate")[1].split("(")[1].split(")")[0]
        if "/MediaBox" in obj:
            size_data = obj.split("[")[1].split("]")[0]
            globalSize = [float(n) for n in size_data.split()]
    count = 1
    for obj in objects:
        obj = obj.strip()
        if not obj:
            continue

        lines = obj.split("\n")
        type_name = None
        for line in lines:
            if "/Type" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "/Type" and i + 1 < len(parts):
                        type_name = parts[i + 1].strip("/")
                        break

        if type_name:
            object_types[type_name] = object_types.get(type_name, 0) + 1

        if "/Type /Page" in obj:
            count += 1
            page_count += 1
            page_info = {"Número da página": count - 1, "content": globalContent.get(count - 1, "")}
            pages.append(page_info)

        if "/Font" in obj:
            for line in lines:
                if "/BaseFont" in line:
                    font_name = line.split("/BaseFont")[1].split()[0].strip("/")
                    fonts.add(font_name)

    for obj in objects:
        if "/Pages" in obj and "/Count" in obj:
            count_data = obj.split("/Count")[1].split()[0].strip()
            try:
                page_count = int(count_data)
            except ValueError:
                pass

    tamanho_documento = len(file_content.encode('utf-8'))
    overhead_estrutural = tamanho_documento - sum(len(obj.encode('utf-8')) for obj in objects)
    overhead_percentual = (overhead_estrutural / tamanho_documento) * 100 if tamanho_documento > 0 else 0
    extraData = {
                "estrutura_de_paginas": {
            "total_de_paginas": page_count,
            "tamanho_da_pagina": globalSize
        },

        "metadados_do_documento": metadata,
        "conteudo_textual_de_cada_pagina": pages,
        "fontes_utilizadas":  list(fonts),
        "estatisticas_de_objetos_por_tipo": object_types
    }
    estatisticas_objetos = ", ".join([f"{tipo}={qtd}" for tipo, qtd in object_types.items()])
    output = '\n\n'
    output += f"\nESTATÍSTICAS\nTotal de objetos: {total_objects}\nObjetos por tipo: {estatisticas_objetos}\nTotal de páginas: {page_count}\nTamanho do documento: {tamanho_documento} bytes\nOverhead estrutural: {overhead_estrutural} bytes ({overhead_percentual:.2f}%)".strip()

    output+="\n\n"
    output +=f"""
    \nCONTEÚDO:\nTítulo: {metadata['Title']}\nAutor: {metadata['Author']}\nData de criação: {converter_data_pdf(metadata['CreationDate'])}\nTexto extraído: {limpar_texto_pdf(globalContent)})\nFontes Utilizadas:{extraData["fontes_utilizadas"]}\n
    """.strip()
    output+="\n\n"
    dataParsed = {
        "output":output,
        "extraData": extraData,
        "metaData": {
            "titulo": metadata['Title'],
            "autor": metadata['Author'],
            "data_de_criacao": converter_data_pdf(metadata['CreationDate']),
            "texto_extraido": globalContent
        },
        "estatisticas": {
            "total_de_objetos": total_objects,
            "objeto_por_tipo": estatisticas_objetos,
            "total_de_paginas": page_count,
            "tamanho_do_documento": f"{tamanho_documento} bytes",
            "overhead_estrutural": f"{overhead_estrutural} bytes ({overhead_percentual:.2f}%)"
        }
}
    return dataParsed

def generate_summary(pdf_info):
    """
    Generate a summary based on the document structure.
    """
    summary = []
    summary.append("\nSumário do Documento")

    summary.append("--- Informações Gerais ---")
    summary.append(f"Total de páginas: {pdf_info['extraData']['estrutura_de_paginas']['total_de_paginas']}")

    page_size = pdf_info["extraData"]['estrutura_de_paginas']['tamanho_da_pagina']

    if len(page_size) >= 4:
        width = page_size[2] - page_size[0]
        height = page_size[3] - page_size[1]
        summary.append(f"Tamanho de página: {width:.2f} x {height:.2f} pontos")

    index = 0
    if pdf_info["extraData"]['metadados_do_documento']:
        summary.append("\n--- Metadados ---")
        for key, value in pdf_info['metaData'].items():
            index +=1
            if (index < 4):
                summary.append(f"{key}: {value}")

    summary.append("\n--- Estatísticas ---")
    summary.append(f"Fontes utilizadas: {len(pdf_info['extraData']['fontes_utilizadas'])},{pdf_info['extraData']['fontes_utilizadas']}")
    index = 0
    if pdf_info["estatisticas"]:
        for key, value in pdf_info['estatisticas'].items():
            index +=1
            if (index < 4):
                summary.append(f"{key}: {value}")
    summary.append("\n--- Conteúdo por Página ---")
    i = 1
    for page in pdf_info["metaData"]["texto_extraido"]:
        if(not '<?x' in pdf_info['metaData']['texto_extraido'][i] ):
            summary.append(f"Página {i}:")
            i+=1
            summary.append(f"  Conteúdo: {parseContent(pdf_info['metaData']['texto_extraido'][i-1])}")
    return '\n'.join(summary)

def extract_pdf_object_tree(pdf_content):
    """
    Extrai a hierarquia de objetos de um arquivo PDF e suas dependências.

    Args:
        pdf_content (str): Conteúdo do arquivo PDF como string

    Returns:
        dict: Resultado contendo a hierarquia de objetos e estatísticas
    """
    objects = {}
    object_types = {}
    object_dependencies = {}

    lines = pdf_content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.endswith("obj"):
            parts = line.split()
            if len(parts) >= 2:
                obj_id = parts[0]
                obj_gen = parts[1]

                obj_content = []
                i += 1
                while i < len(lines) and not lines[i].strip() == "endobj":
                    obj_content.append(lines[i])
                    i += 1

                objects[obj_id] = {
                    "generation": obj_gen,
                    "content": "\n".join(obj_content),
                    "raw_content": obj_content
                }
        i += 1

    for obj_id, obj_data in objects.items():
        obj_content = obj_data["content"]

        obj_type = "Unknown"
        if "/Type" in obj_content:
            parts = obj_content.split("/Type")[1].split()
            if parts and parts[0].startswith("/"):
                obj_type = parts[0][1:]

        object_types[obj_id] = obj_type

        dependencies = []
        lines = obj_data["raw_content"]
        for line in lines:
            tokens = line.split()
            for j in range(len(tokens) - 2):

                if tokens[j+2] == "R":
                    try:
                        ref_id = tokens[j]
                        if ref_id in objects:
                            dependencies.append(ref_id)
                    except (IndexError, ValueError):
                        continue

        object_dependencies[obj_id] = dependencies

    root_objects = []
    for obj_id, obj_type in object_types.items():
        if obj_type == "Catalog":
            root_objects.append(obj_id)

    if not root_objects:
        all_refs = set()
        for deps in object_dependencies.values():
            all_refs.update(deps)

        for obj_id in objects:
            if obj_id not in all_refs:
                root_objects.append(obj_id)

    def build_hierarchy(obj_id, visited=None):
        if visited is None:
            visited = set()

        if obj_id in visited:
            return {"id": obj_id, "type": object_types.get(obj_id, "Unknown"), "circular": True}

        visited.add(obj_id)

        node = {
            "id": obj_id,
            "type": object_types.get(obj_id, "Unknown"),
            "children": []
        }

        if obj_id in object_dependencies:
            for dep_id in object_dependencies[obj_id]:
                child = build_hierarchy(dep_id, visited.copy())
                node["children"].append(child)

        return node

    hierarchy = []
    for root_id in root_objects:
        hierarchy.append(build_hierarchy(root_id))

    all_refs = set()
    for deps in object_dependencies.values():
        all_refs.update(deps)

    orphaned = [obj_id for obj_id in objects if obj_id not in all_refs and obj_id not in root_objects]

    type_counts = {}
    for obj_type in object_types.values():
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

    def format_tree(node, level=0):
        result = []
        prefix = "  " * level
        result.append(f"{prefix}{'└─' if level > 0 else ''}Objeto {node['id']} (Tipo: {node['type']})")

        if "circular" in node and node["circular"]:
            result.append(f"{prefix}  └─ (Referência circular)")
            return result

        for child in node["children"]:
            result.extend(format_tree(child, level + 1))

        return result
    output = []

    for root in hierarchy:
        output.extend(format_tree(root))


    return {
        "text_output": "\n".join(output),
        "hierarchy": hierarchy,
        "orphaned": orphaned,
        "statistics": {
            "total_objects": len(objects),
            "type_counts": type_counts
        }
    }

def extrair_texto(linha):
    """
    Extrai texto entre parênteses de uma linha de comando PDF

    Args:
        linha (str): Linha contendo comando Tj

    Returns:
        str: Texto extraído ou string vazia se não encontrado
    """
    inicio = linha.find("(")
    fim = linha.rfind(")")

    if inicio != -1 and fim != -1 and fim > inicio:
        return linha[inicio+1:fim]
    return ""

def pontos_para_cm(pontos):
    """
    Converte pontos PDF (1/72 polegada) para centímetros

    Args:
        pontos (float): Valor em pontos

    Returns:
        float: Valor em centímetros, arredondado para 2 casas decimais
    """
    cm = (pontos / 72) * 2.54
    return round(cm, 2)

def converter_coordenadas_texto_pdf(content):
    """
    Converte coordenadas de texto PDF para um formato mais legível.
    Processa comandos como BT, ET, Td, Tm e extrai informações de posicionamento.

    Args:
        content (str): Conteúdo de texto do stream PDF

    Returns:
        list: Lista de dicionários com informações de texto e posicionamento
    """
    resultado = []

    linhas = content.strip().split("\n")

    em_bloco_texto = False
    posicao_atual_x = 0
    posicao_atual_y = 0
    fonte_atual = ""
    tamanho_fonte = 0

    for linha in linhas:
        tokens = linha.strip().split()
        if not tokens:
            continue

        if "BT" in tokens:
            em_bloco_texto = True
            posicao_atual_x = 0
            posicao_atual_y = 0
            continue

        if "ET" in tokens:
            em_bloco_texto = False
            continue

        if not em_bloco_texto:
            continue

        for i in range(len(tokens)):
            if i > 0 and tokens[i] == "Tf" and i >= 2:
                fonte_atual = tokens[i-2].replace("/", "")
                try:
                    tamanho_fonte = float(tokens[i-1])
                except ValueError:
                    tamanho_fonte = 0

            if i > 0 and tokens[i] == "Td" and i >= 2:
                try:
                    posicao_atual_x = float(tokens[i-2])
                    posicao_atual_y = float(tokens[i-1])
                except ValueError:
                    continue

            if i > 0 and tokens[i] == "Tm" and i >= 6:
                try:
                    posicao_atual_x = float(tokens[i-2])
                    posicao_atual_y = float(tokens[i-1])
                except ValueError:
                    continue

            if i > 0 and tokens[i] == "Tj":
                texto = extrair_texto(linha)
                if texto:
                    info = {
                        "texto": texto,
                        "posicao": {
                            "pontos": {"x": posicao_atual_x, "y": posicao_atual_y},
                            "cm": {"x": pontos_para_cm(posicao_atual_x), "y": pontos_para_cm(posicao_atual_y)}
                        },
                        "fonte": fonte_atual,
                        "tamanho_fonte": {
                            "pontos": tamanho_fonte,
                            "cm": pontos_para_cm(tamanho_fonte)
                        }
                    }
                    resultado.append(info)

    return resultado


def processar_conteudo_pdf(pdf_content):
    """
    Processa o conteúdo do PDF e extrai informações de posicionamento de texto

    Args:
        pdf_content (str): Conteúdo completo do arquivo PDF

    Returns:
        dict: Dicionário com informações de texto por página
    """
    resultado = {}
    objects = pdf_content.split("endobj")

    for i, obj in enumerate(objects):
        if "stream" in obj and "endstream" in obj:
            start = obj.find("stream") + len("stream")
            end = obj.find("endstream")
            content = obj[start:end].strip()

            if "/Type /Page" in obj or "/Contents" in obj:
                page_num = i + 1
                texto_posicionado = converter_coordenadas_texto_pdf(content)

                if texto_posicionado:
                    resultado[f"Página {page_num}"] = texto_posicionado

    return resultado

def formatar_resultado_simples(resultado):
    """
    Formata o resultado para impressão legível de forma simplificada

    Args:
        resultado (dict): Resultado do processamento

    Returns:
        str: Texto formatado de forma simplificada
    """
    saida = []
    saida.append("=== CONTEÚDO DE TEXTO COM COORDENADAS ===")

    for pagina, textos in resultado.items():
        saida.append(f"\n{pagina}:")

        for info in textos:
            posicao = f"({info['posicao_x_cm']}cm, {info['posicao_y_cm']}cm)"

            fonte_info = ""
            if info['fonte']:
                fonte_info = f" - Fonte: {info['fonte']} {info['tamanho_fonte']}pt"

            saida.append(f"  → \"{info['texto']}\" em {posicao}{fonte_info}")

    return "\n".join(saida)

def formatar_resultado(resultado):
    """
    Formata o resultado para impressão legível

    Args:
        resultado (dict): Resultado do processamento

    Returns:
        str: Texto formatado
    """
    saida = []
    saida.append("=== TEXTO COM COORDENADAS ===")

    for pagina, textos in resultado.items():
        saida.append(f"\n--- {pagina} ---")

        for i, info in enumerate(textos, 1):
            saida.append(f"Item {i}:")
            saida.append(f"  Texto: \"{info['texto']}\"")
            saida.append(f"  Posição: X={info['posicao']['pontos']['x']}pt ({info['posicao']['cm']['x']}cm), "
                        f"Y={info['posicao']['pontos']['y']}pt ({info['posicao']['cm']['y']}cm)")

            if info['fonte']:
                saida.append(f"  Fonte: {info['fonte']}, Tamanho: {info['tamanho_fonte']['pontos']}pt ({info['tamanho_fonte']['cm']}cm)")

    return "\n".join(saida)

def extrair_coordenadas_texto(file_content):
    resultado = processar_conteudo_pdf(file_content)
    return formatar_resultado(resultado)

def formatar_texto(dados):
    resultado = []

    for chave, valor in dados.items():
        if isinstance(valor, dict):
            resultado.append(f"{chave.capitalize()}:")
            for subchave, subvalor in valor.items():
                if isinstance(subvalor, dict):
                    resultado.append(f"  {subchave.capitalize()}: x={subvalor.get('x', 0)}, y={subvalor.get('y', 0)}")
                else:
                    resultado.append(f"  {subchave.capitalize()}: {subvalor}")
        else:
            resultado.append(f"{chave.capitalize()}: {valor}")

    return "\n".join(resultado)

def extrair_e_imprimir_coordenadas(text):
    output = ""
    for item in text:
        if isinstance(item, dict):
            for key, value in item.items():
                output += formatar_texto({key: value})
    return output

def detect_unreferenced_objects(file_content):
    """
    Detecta objetos não referenciados em um arquivo PDF.

    Args:
        file_content (str): Conteúdo do arquivo PDF como string

    Returns:
        dict: Dicionário contendo objetos não referenciados e estatísticas
    """
    objects = file_content.split("endobj")

    object_ids = {}
    references = set()

    for i, obj in enumerate(objects):
        obj = obj.strip()
        if not obj:
            continue

        parts = obj.split(" obj", 1)
        if len(parts) > 1:
            header = parts[0].strip().split()
            if len(header) >= 2 and header[-2].isdigit() and header[-1] == "0":
                try:
                    obj_id = int(header[-2])
                    object_ids[obj_id] = obj
                except ValueError:
                    continue

    def find_references(text):
        result = set()
        text = text.replace("[", " [ ").replace("]", " ] ")
        parts = text.split()

        for i in range(len(parts) - 2):
            if parts[i].isdigit() and parts[i+1] == "0" and parts[i+2] == "R":
                try:
                    ref_id = int(parts[i])
                    result.add(ref_id)
                except ValueError:
                    continue
        return result

    for obj_id, obj_content in object_ids.items():
        refs = find_references(obj_content)
        references.update(refs)

    unreferenced = {}
    for obj_id in object_ids:
        if obj_id == 1:
            continue

        if obj_id not in references:
            unreferenced[obj_id] = object_ids[obj_id]

    unreferenced_types = {}
    for obj_id, obj_content in unreferenced.items():
        obj_type = "Desconhecido"

        if "/Type /" in obj_content:
            type_start = obj_content.find("/Type /") + 7
            remaining = obj_content[type_start:]

            if " " in remaining:
                obj_type = remaining.split(" ")[0]
            elif "/" in remaining:
                obj_type = remaining.split("/")[0]
            elif ">>" in remaining:
                obj_type = remaining.split(">>")[0]
            elif "\n" in remaining:
                obj_type = remaining.split("\n")[0]
            else:
                obj_type = remaining

            obj_type = obj_type.strip()

        unreferenced_types[obj_id] = obj_type


    result = {
        "total_objetos": len(object_ids),
        "total_referencias": len(references),
        "total_nao_referenciados": len(unreferenced),
        "objetos_nao_referenciados": {},
    }

    for obj_id, obj_type in unreferenced_types.items():
        obj_content = unreferenced[obj_id]

        content_preview = obj_content[:100].replace("\n", " ").strip()

        result["objetos_nao_referenciados"][obj_id] = {
            "tipo": obj_type,
            "preview": content_preview + "..." if len(obj_content) > 100 else content_preview
        }

    return result

def print_unreferenced_objects_report(pdf_content):
    """
    Imprime um relatório sobre objetos não referenciados no PDF.

    Args:
        pdf_content (str): Conteúdo do arquivo PDF como string
    """
    result = detect_unreferenced_objects(pdf_content)

    data = "\nANÁLISE AVANÇADA:\n"
    data += "\nRELATÓRIO DE OBJETOS NÃO REFERENCIADOS:\n" + f"Total de objetos no PDF: {result['total_objetos']}\n" + f"Total de referências encontradas: {result['total_referencias']}\n" + f"Total de objetos não referenciados: {result['total_nao_referenciados']}\n"


    if result['objetos_nao_referenciados']:
        data +="\nDETALHES DOS OBJETOS NÃO REFERENCIADOS:"
        for obj_id, details in sorted(result['objetos_nao_referenciados'].items()):
            data +=f"\nObjeto ID: {obj_id}\n"
            data +=f"Tipo: {details['tipo']}\n"
            data += f"Preview: {details['preview']}\n"

    return data

def detect_reference_cycles(file_content):
    """
    Detecta ciclos de referência em um arquivo PDF.

    Args:
        file_content (str): Conteúdo do arquivo PDF como string

    Returns:
        dict: Dicionário contendo ciclos de referência encontrados e estatísticas
    """
    objects = file_content.split("endobj")


    reference_graph = {}

    object_contents = {}

    for obj in objects:
        obj = obj.strip()
        if not obj:
            continue

        parts = obj.split(" obj", 1)
        if len(parts) > 1:
            header = parts[0].strip().split()
            if len(header) >= 2 and header[-2].isdigit() and header[-1] == "0":
                try:
                    obj_id = int(header[-2])
                    object_contents[obj_id] = obj

                    reference_graph[obj_id] = []
                except ValueError:
                    continue

    def find_references(text):
        result = []
        text = text.replace("[", " [ ").replace("]", " ] ")
        parts = text.split()

        for i in range(len(parts) - 2):
            if parts[i].isdigit() and parts[i+1] == "0" and parts[i+2] == "R":
                try:
                    ref_id = int(parts[i])
                    result.append(ref_id)
                except ValueError:
                    continue
        return result

    for obj_id, obj_content in object_contents.items():
        refs = find_references(obj_content)
        reference_graph[obj_id] = refs


    def find_cycles():
        cycles = []
        visited = set()
        path = []
        path_set = set()

        def dfs(node):
            if node in path_set:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited or node not in reference_graph:
                return

            visited.add(node)
            path.append(node)
            path_set.add(node)

            for neighbor in reference_graph[node]:
                dfs(neighbor)

            path.pop()
            path_set.remove(node)

        for node in reference_graph:
            if node not in visited:
                dfs(node)

        return cycles

    cycles = find_cycles()

    object_types = {}
    for obj_id, obj_content in object_contents.items():
        obj_type = "Desconhecido"

        if "/Type /" in obj_content:
            type_start = obj_content.find("/Type /") + 7
            remaining = obj_content[type_start:]

            if " " in remaining:
                obj_type = remaining.split(" ")[0]
            elif "/" in remaining:
                obj_type = remaining.split("/")[0]
            elif ">>" in remaining:
                obj_type = remaining.split(">>")[0]
            elif "\n" in remaining:
                obj_type = remaining.split("\n")[0]
            else:
                obj_type = remaining

            obj_type = obj_type.strip()

        object_types[obj_id] = obj_type

    cycles_info = []
    for cycle in cycles:
        cycle_info = {
            "objetos": cycle,
            "tipos": [object_types.get(obj_id, "Desconhecido") for obj_id in cycle],
            "comprimento": len(cycle)
        }
        cycles_info.append(cycle_info)

    result = {
        "total_objetos": len(object_contents),
        "total_referencias": sum(len(refs) for refs in reference_graph.values()),
        "total_ciclos": len(cycles),
        "ciclos_encontrados": cycles_info
    }

    return result

def print_reference_cycles_report(pdf_content):
    """
    Imprime um relatório sobre ciclos de referência no PDF.

    Args:
        pdf_content (str): Conteúdo do arquivo PDF como string
    """
    result = detect_reference_cycles(pdf_content)
    output = ""
    output +="\nRELATÓRIO DE CICLOS DE REFERÊNCIA:"
    output +=f"\nTotal de objetos no PDF: {result['total_objetos']}"
    output += f"\nTotal de referências encontradas: {result['total_referencias']}"
    output += f"\nTotal de ciclos detectados: {result['total_ciclos']}"

    if result['ciclos_encontrados']:
        output +="\n"
        output +="\nDetalhes dos ciclos encontrados:"
        for i, cycle_info in enumerate(result['ciclos_encontrados']):
            output += f"\nCiclo #{i+1} (comprimento: {cycle_info['comprimento']}):"

            path = []
            for j, obj_id in enumerate(cycle_info['objetos']):
                path.append(f"{obj_id}({cycle_info['tipos'][j]})")
            output += " → ".join(path)
    else:
        output += "\nNão foram encontrados ciclos de referência."
    return output

def analyze_storage_efficiency(file_content):
    """
    Analisa a eficiência de armazenamento de um arquivo PDF, identificando
    oportunidades de otimização e fornecendo métricas detalhadas.

    Args:
        file_content (str): Conteúdo do arquivo PDF como string

    Returns:
        dict: Dicionário contendo métricas de eficiência e recomendações
    """
    total_size = len(file_content.encode('utf-8'))

    objects = file_content.split("endobj")

    object_data = {}
    object_sizes = {}
    object_types = {}
    stream_sizes = {}

    for obj in objects:
        obj = obj.strip()
        if not obj:
            continue

        parts = obj.split(" obj", 1)
        if len(parts) < 2:
            continue

        header = parts[0].strip().split()
        if len(header) < 2 or not header[-2].isdigit() or header[-1] != "0":
            continue

        try:
            obj_id = int(header[-2])
            obj_size = len(obj.encode('utf-8'))
            object_data[obj_id] = obj
            object_sizes[obj_id] = obj_size
        except ValueError:
            continue

        if "/Type /" in obj:
            type_start = obj.find("/Type /") + 7
            remaining = obj[type_start:]

            if " " in remaining:
                obj_type = remaining.split(" ")[0]
            elif "/" in remaining:
                obj_type = remaining.split("/")[0]
            elif ">>" in remaining:
                obj_type = remaining.split(">>")[0]
            elif "\n" in remaining:
                obj_type = remaining.split("\n")[0]
            else:
                obj_type = remaining

            object_types[obj_id] = obj_type.strip()
        else:
            object_types[obj_id] = "Desconhecido"


        if "stream" in obj and "endstream" in obj:
            try:
                stream_start = obj.find("stream") + len("stream")
                stream_end = obj.find("endstream")
                if stream_end > stream_start:
                    if obj[stream_start:stream_start+2] == "\r\n":
                        stream_start += 2
                    elif obj[stream_start:stream_start+1] == "\n":
                        stream_start += 1

                    stream_content = obj[stream_start:stream_end]
                    stream_sizes[obj_id] = len(stream_content.encode('utf-8'))
            except:
                continue

    total_objects = len(object_sizes)
    total_object_size = sum(object_sizes.values())
    total_stream_size = sum(stream_sizes.values())
    total_overhead = total_size - total_object_size

    overhead_percentage = (total_overhead / total_size) * 100 if total_size > 0 else 0

    content_efficiency = (total_stream_size / total_object_size) * 100 if total_object_size > 0 else 0

    avg_object_size = total_object_size / total_objects if total_objects > 0 else 0

    avg_stream_size = total_stream_size / len(stream_sizes) if stream_sizes else 0

    small_objects = []
    small_threshold = avg_object_size * 0.3
    for obj_id, size in object_sizes.items():
        if size < small_threshold and obj_id not in stream_sizes:
            small_objects.append({
                "id": obj_id,
                "tipo": object_types.get(obj_id, "Desconhecido"),
                "tamanho": size
            })

    uncompressed_streams = []
    for obj_id, obj in object_data.items():
        if obj_id in stream_sizes:
            if "/Filter" not in obj:
                uncompressed_streams.append({
                    "id": obj_id,
                    "tipo": object_types.get(obj_id, "Desconhecido"),
                    "tamanho": stream_sizes[obj_id]
                })

    type_counts = {}
    type_sizes = {}
    for obj_id, obj_type in object_types.items():
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        type_sizes[obj_type] = type_sizes.get(obj_type, 0) + object_sizes[obj_id]

    result = {
        "metricas_gerais": {
            "tamanho_total": total_size,
            "total_objetos": total_objects,
            "tamanho_objetos": total_object_size,
            "tamanho_streams": total_stream_size,
            "overhead_estrutural": total_overhead,
            "porcentagem_overhead": overhead_percentage,
            "eficiencia_conteudo": content_efficiency,
            "tamanho_medio_objeto": avg_object_size,
            "tamanho_medio_stream": avg_stream_size
        },
        "distribuicao_tipos": {
            tipo: {
                "contagem": type_counts[tipo],
                "tamanho_total": type_sizes[tipo],
                "tamanho_medio": type_sizes[tipo] / type_counts[tipo] if type_counts[tipo] > 0 else 0,
                "porcentagem_espaco": (type_sizes[tipo] / total_object_size) * 100 if total_object_size > 0 else 0
            } for tipo in type_counts
        },
        "oportunidades_otimizacao": {
            "objetos_pequenos": small_objects,
            "streams_nao_compactados": uncompressed_streams
        }
    }

    return result

def print_storage_efficiency_report(pdf_content,responseConfigJson):
    """
    Imprime um relatório sobre a eficiência de armazenamento de um PDF.

    Args:
        pdf_content (str): Conteúdo do arquivo PDF como string
    """
    result = analyze_storage_efficiency(pdf_content)
    metrics = result["metricas_gerais"]
    output = ""
    output+="\n"
    output +="\nRELATÓRIO DE EFICIÊNCIA DE ARMAZENAMENTO PDF:"
    output += "\n\n"
    output += "1. MÉTRICAS GERAIS:"
    output += f"\nTamanho total do arquivo: {metrics['tamanho_total']:,} bytes"
    output += f"\nTotal de objetos: {metrics['total_objetos']}"
    output+="\n"
    output +=f"Tamanho total dos objetos: {metrics['tamanho_objetos']:,} bytes ({metrics['tamanho_objetos']/metrics['tamanho_total']*100:.1f}% do arquivo)"
    output += f"Tamanho total dos streams: {metrics['tamanho_streams']:,} bytes ({metrics['tamanho_streams']/metrics['tamanho_total']*100:.1f}% do arquivo)"
    output+="\n"
    output +=f"Overhead estrutural: {metrics['overhead_estrutural']:,} bytes ({metrics['porcentagem_overhead']:.1f}% do arquivo)"
    output+="\n"
    output += f"Eficiência de conteúdo: {metrics['eficiencia_conteudo']:.1f}% (proporção de streams vs. objetos)"
    output+="\n"
    output +="\n2. DISTRIBUIÇÃO POR TIPO DE OBJETO:"
    output+="\n"
    output +=f"{'Tipo':<15} {'Contagem':<10} {'Tamanho Total':<15} {'Tamanho Médio':<15} {'% do Espaço':<10}"

    sorted_types = sorted(
        result["distribuicao_tipos"].items(),
        key=lambda x: x[1]["tamanho_total"],
        reverse=True
    )

    for tipo, info in sorted_types:
        output += f"{tipo:<15} {info['contagem']:<10} {info['tamanho_total']:,} bytes  {info['tamanho_medio']:.1f} bytes    {info['porcentagem_espaco']:.1f}%"
    if(responseConfigJson["analise_avancada"]["sugerir_otimizacoes"]):
        output+="\n"
        output+= "\n3. OPORTUNIDADES DE OTIMIZAÇÃO:"
        uncompressed = result["oportunidades_otimizacao"]["streams_nao_compactados"]
        if uncompressed:
            output +=f"\n3.1. Streams não compactados: {len(uncompressed)} encontrados"
            output+="\n"

            output += "Compactação destes streams pode reduzir significativamente o tamanho do arquivo."
            output +=f"{'ID':<5} {'Tipo':<15} {'Tamanho':<15}"
            for stream in sorted(uncompressed, key=lambda x: x["tamanho"], reverse=True):
                output += f"{stream['id']:<5} {stream['tipo']:<15} {stream['tamanho']:,} bytes"
        else:
            output += "\n3.1. Streams não compactados: Nenhum encontrado (Bom!)"
            output+="\n"
        small_objs = result["oportunidades_otimizacao"]["objetos_pequenos"]
        if small_objs:

            output +=f"\n3.2. Objetos pequenos: {len(small_objs)} encontrados"

            output +="Fusão destes objetos pode reduzir o overhead estrutural."
            output += f"{'ID':<5} {'Tipo':<15} {'Tamanho':<15}"
            for obj in sorted(small_objs, key=lambda x: x["tamanho"]):
                output += f"{obj['id']:<5} {obj['tipo']:<15} {obj['tamanho']:,} bytes"
        else:
            output += "\n3.2. Objetos pequenos: Nenhum encontrado (Bom!)"

        output+="\n"
        output +="\n4. RECOMENDAÇÕES:"
        if metrics["porcentagem_overhead"] > 15:
            output+="\n"
            output +="- O overhead estrutural é alto. Considere otimizar a estrutura do PDF."
        if metrics["eficiencia_conteudo"] < 60:
            output+="\n"
            output += "- Baixa eficiência de conteúdo. Verifique se há metadados excessivos."
        if uncompressed:
            output+="\n"
            output +="- Implemente compressão nos streams identificados para reduzir o tamanho do arquivo."
        if small_objs:
            output+="\n"
            output +="- Considere fundir objetos pequenos para reduzir overhead estrutural."
        if not (metrics["porcentagem_overhead"] > 15 or metrics["eficiencia_conteudo"] < 60 or uncompressed or small_objs):
            output+="\n"
            output+= "- Este PDF parece ser relativamente eficiente em termos de armazenamento."
    return output

def print_hierarchy(pdf_content):
    """
    Extrai e imprime a hierarquia de objetos de um arquivo PDF.

    Args:
        pdf_content (str): Conteúdo do arquivo PDF como string
    """
    result =  extract_pdf_object_tree(pdf_content)
    return "\nLISTAGEM HIERÁRQUICA:\n" + result["text_output"]

def initParser(file,label):
    file_content = ''
    erro = ''
    txt_content = ""
    file_content = file
    configFileUrl = f'https://raw.githubusercontent.com/GustavoGuadagnin/ConstrucaoDeInterpretadores-TDE1/main/{label}Config.json'
    responseConfig = requests.get(configFileUrl)
    if responseConfig.status_code == 200:
        responseConfigJson = responseConfig.json()
    else:
        print(f"Erro ao baixar o arquivo. Status code: {responseConfig.status_code}")
    objects = {}
    xref_entries = []
    trailer_found = False
    lines = file_content.splitlines()
    missing_refs = ''
    extraData = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.endswith("obj"):
            obj_id = line.split(" ")[0]
            obj_content = []

            i += 1
            while i < len(lines) and not lines[i].strip().startswith("endobj"):
                obj_content.append(lines[i].strip())
                i += 1

            if i < len(lines) and lines[i].strip() == "endobj":
                objects[obj_id] = obj_content
            else:
                erro = f"Objeto {obj_id} sem 'endobj'!"

        if (line == 'trailer' and responseConfigJson["validar_trailer"]):
            trailer_found = True
        if (line == 'xref'):
            xref_entries.append(line.strip())

        i += 1
    missing_refs = []
    for obj_id, obj_content in objects.items():
        for item in obj_content:
            tokens = item.split()
            for token in tokens:
                if token.endswith("R") and len(token.split()) == 2:
                    ref_id = token.split()[0]
                    if ref_id not in objects:
                        missing_refs.append(ref_id)
    sintaxe = validar_sintaxe_objetos(file_content)


    if lines[0].strip().startswith('%SPDF-1.0') and trailer_found and not missing_refs and xref_entries and not erro and  sintaxe:
        txt_content+="VALIDAÇÃO:\n[OK] Estrutura Geral"
    else:
        txt_content+="\nVALIDAÇÃO:\n[ERRO] Estrutura Geral"
    if (not sintaxe):
        txt_content+="\n[ERRO] Sintaxe de objetos"
    else:
        txt_content+="\n[OK] Sintaxe de objetos"
    if missing_refs:
        txt_content+="\n[ERRO] Referências"
    else:
        txt_content+="\n[OK] Referências"
    if not xref_entries:
        txt_content+="\n[ERRO] Tabela xref"
    else:
        txt_content+="\n[OK] Tabela xref"
    if(responseConfigJson["validar_cabecalho"]):
        if not lines[0].strip().startswith('%SPDF-1.0'):
            txt_content+="\n[ERRO] Cabeçalho"
        else:
            txt_content+="\n[OK] Cabeçalho"
    if (responseConfigJson["validar_trailer"]):
        if not trailer_found:
            txt_content+="\n[ERRO] Trailer"
        else:
            txt_content+="\n[OK] Trailer"
    if erro:
        txt_content+=f"[{erro}]"
    pdf_info = parse_pdf(file_content)
    txt_content += pdf_info["output"]
    txt_content += "ÁRVORE DE OBJETOS" + "\n" + print_pdf_object_tree(file_content)
    generate_summary(pdf_info)
    if (responseConfigJson["analise_avancada"]["detectar_objetos_nao_referenciados"]):
        print_unreferenced_objects_report(file_content)
        txt_content += print_unreferenced_objects_report(file_content)
    if(responseConfigJson["analise_avancada"]["detectar_ciclos_referencia"]):
        txt_content += print_reference_cycles_report(file_content)
    if(responseConfigJson["analise_avancada"]["analisar_eficiencia_armazenamento"]):
        txt_content += print_storage_efficiency_report(file_content,responseConfigJson)
    if (responseConfigJson["conteudo"]["listar_hierarquia"]):
        txt_content += "\n"
        txt_content +=  print_hierarchy(file_content)
    if (responseConfigJson["conteudo"]["gerar_sumario"]):
        txt_content+= "\n"
        txt_content+=generate_summary(pdf_info)
    if (responseConfigJson["conteudo"]["converter_coordenadas"]):
        extrair_e_imprimir_coordenadas(converter_coordenadas_texto_pdf(file_content))
        txt_content += "\n\nCOORDENADAS DE TEXTO CONVERTIDAS\n"
        txt_content +=extrair_e_imprimir_coordenadas(converter_coordenadas_texto_pdf(file_content))

    with open(label+'.txt', 'w') as f:
        f.write(txt_content)
        print(f'{label}.txt gerado com sucesso!')
    with open(f'{label}configJson.txt', 'w') as f:
        f.write(json.dumps(responseConfigJson))
        print(f'Configuração de {label}.json convertida em .txt para fins de visualização gerado com sucesso!')

initParser(downloadFile('https://raw.githubusercontent.com/GustavoGuadagnin/ConstrucaoDeInterpretadores-TDE1/refs/heads/main/arquivo1.spdf'),'arquivo1')
initParser(downloadFile('https://raw.githubusercontent.com/GustavoGuadagnin/ConstrucaoDeInterpretadores-TDE1/refs/heads/main/arquivo2.spdf'),'arquivo2')
initParser(downloadFile('https://raw.githubusercontent.com/GustavoGuadagnin/ConstrucaoDeInterpretadores-TDE1/refs/heads/main/arquivo3.spdf'),'arquivo3')
