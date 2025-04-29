import regex as re
from models.db.metadados import METADADOS

def sql_to_algebra(parsed_sql):
    """
    Converte parsed_sql (dicionário com keys 'select', 'from', 'joins', 'where')
    em uma expressão de álgebra relacional usando projeção (π), seleção (σ)
    e theta‑join (⋈_{cond}).
    """
    # 1) Projeção
    proj_cols = ', '.join(parsed_sql['select'])
    projection = f"π[{proj_cols}]"

    # 2) Construção da expressão de join com predicados (theta‑join)
    expr = parsed_sql['from']
    for j in parsed_sql.get('joins', []):
        table = j['table']
        cond  = j['condition']
        # Theta‑join com predicado
        expr = f"{expr} ⨝[{cond}] {table}"

    # 3) Seleção (WHERE) — opcional
    if parsed_sql.get('where'):
        selection = f"σ[{parsed_sql['where']}]"
        expr = f"{selection}({expr})"

    # 4) Aplicar projeção sobre todo o resultado
    return f"{projection}({expr})"

def extract_tables(expression: str):
    return re.findall(r'(\w+)\s*\⨝?', expression)

def extract_tables(expression):
    """Extrai todas as tabelas da expressão de álgebra relacional"""
    # Padrão melhorado para capturar tabelas, excluindo operadores e funções da álgebra
    table_pattern = r'(?:^|\s|\()(\w+)(?=\s*[⨝×]|\s*\)|\s*$)'
    tables = re.findall(table_pattern, expression)
    
    # Filtrar operadores da álgebra relacional e outros não-tabelas
    return [t for t in tables if t not in ('π', 'σ', 'and', 'or', 'AND', 'OR')]
    
def extract_conditions(expression: str):
    condition_match = re.search(r'σ\[(.*?)\]', expression)
    if condition_match:
        return [cond.strip() for cond in re.split(r'(?i) and ', condition_match.group(1))]
    return []

def extract_projection(expression: str):
    projection_match = re.search(r'π\[(.*?)\]', expression)
    if projection_match:
        return [cond.strip() for cond in re.split(r'(?i) and ', projection_match.group(1))]
    return []

def optimize_algebra(expression: str) -> str:
    projection = extract_projection(expression)
    conditions = extract_conditions(expression)
    tables = extract_tables(expression)

    # Push-down de seleções
    selection_map = {table: [] for table in tables}
    for cond in conditions:
        for table in tables:
            if cond.startswith(table + "."):
                selection_map[table].append(cond)
                break

    # Construção da árvore otimizada em string
    join_expr = " ⨝ ".join([
        f"σ[{ ' and '.join(selection_map[t]) }]({t})" if selection_map[t] else t
        for t in tables
    ])

    if projection:
        return f"π[{', '.join(projection)}]({join_expr})"
    return join_expr

def optimize_algebra(expression):
    """
    Otimiza a expressão de álgebra relacional usando as seguintes heurísticas:
    
    1. Aplicar seleções o mais cedo possível (push-down de seleções)
    2. Aplicar projeções o mais cedo possível (push-down de projeções)
    3. Ordenar junções da mais restritiva para menos restritiva
    4. Evitar produtos cartesianos quando possível
    """
    tables = extract_tables(expression)
    conditions = extract_conditions(expression)
    joins = extract_joins(expression)
    projections = extract_projection(expression)
    
    # 1. Mapear condições às tabelas específicas (push-down de seleções)
    table_conditions = {table: [] for table in tables}
    join_conditions = []
    remaining_conditions = []
    
    # Classificar cada condição: tabela específica, junção ou global
    for cond in conditions + joins:
        table_matches = re.findall(r'(\w+)\.(\w+)', cond)
        tables_in_condition = {table for table, _ in table_matches}
        
        if len(tables_in_condition) == 1:
            # Condição afeta apenas uma tabela - aplicar diretamente à tabela
            table = list(tables_in_condition)[0]
            table_conditions[table].append(cond)
        elif len(tables_in_condition) == 2 and any(op in cond for op in ['=', '<', '>', '<=', '>=', '<>']):
            # Condição de junção entre duas tabelas
            join_conditions.append((cond, tables_in_condition))
        else:
            # Condição que não pode ser empurrada para baixo
            remaining_conditions.append(cond)
    
    # 2. Identificar colunas necessárias para cada tabela (push-down de projeções)
    needed_columns = {table: set() for table in tables}
    
    # Colunas no SELECT
    for proj in projections:
        if '.' in proj:
            table, column = proj.split('.')
            if table in needed_columns:
                needed_columns[table].add(column)
    
    # Colunas em condições (WHERE, JOIN)
    all_conditions = conditions + joins
    for cond in all_conditions:
        matches = re.findall(r'(\w+)\.(\w+)', cond)
        for table, column in matches:
            if table in needed_columns:
                needed_columns[table].add(column)
    
    # 3. Aplicar seleções e projeções antecipadas às tabelas base
    filtered_tables = {}
    for table in tables:
        table_expr = table
        
        # Aplicar seleção se houver condições para esta tabela
        if table_conditions[table]:
            conditions_str = " AND ".join(table_conditions[table])
            table_expr = f"σ[{conditions_str}]({table_expr})"
        
        # Aplicar projeção antecipada se tivermos apenas algumas colunas necessárias
        if needed_columns[table] and len(needed_columns[table]) < len(METADADOS.get(table, [])):
            columns_str = ", ".join([f"{table}.{col}" for col in needed_columns[table]])
            table_expr = f"π[{columns_str}]({table_expr})"
        
        filtered_tables[table] = table_expr
    
    # 4. Ordenar junções por seletividade (mais restritiva primeiro)
    sorted_joins = []
    if join_conditions:
        # Estimar seletividade para cada junção
        join_selectivity = []
        for cond, tbls in join_conditions:
            # Junções de igualdade são mais seletivas que outras
            selectivity = 0.1 if '=' in cond else 0.3
            # Junções em colunas-chave (contendo 'id') são mais seletivas
            if re.search(r'id\w*', cond, re.IGNORECASE):
                selectivity *= 0.5
            join_selectivity.append((cond, tbls, selectivity))
        
        # Ordenar junções da mais seletiva (menor valor) para menos seletiva
        join_selectivity.sort(key=lambda x: x[2])
        sorted_joins = [(cond, tbls) for cond, tbls, _ in join_selectivity]
    
    # 5. Construir a árvore de operadores a partir das junções ordenadas
    # Começar com a tabela mais restritiva ou a primeira se não houver seleções
    table_order = list(filtered_tables.keys())
    
    # Se temos junções, executar primeiro as mais seletivas
    join_tree = None
    processed_tables = set()
    
    if sorted_joins:
        # Identificar a primeira junção e as tabelas envolvidas
        first_join, first_tables = sorted_joins[0]
        first_tables = list(first_tables)
        
        # Iniciar com as duas tabelas da primeira junção
        join_tree = f"({filtered_tables[first_tables[0]]} ⨝[{first_join}] {filtered_tables[first_tables[1]]})"
        processed_tables.update(first_tables)
        
        # Adicionar as junções restantes na ordem de seletividade
        for join_cond, join_tables in sorted_joins[1:]:
            join_tables = list(join_tables)
            # Verificar se podemos conectar esta junção com o que já processamos
            if any(table in processed_tables for table in join_tables):
                # Encontrar a tabela que ainda não foi processada
                new_table = next((t for t in join_tables if t not in processed_tables), None)
                if new_table:
                    join_tree = f"({join_tree} ⨝[{join_cond}] {filtered_tables[new_table]})"
                    processed_tables.add(new_table)
        
        # Para tabelas que não foram incluídas em nenhuma junção, usar produto cartesiano
        for table in table_order:
            if table not in processed_tables:
                if join_tree:
                    join_tree = f"({join_tree} × {filtered_tables[table]})"
                else:
                    join_tree = filtered_tables[table]
                processed_tables.add(table)
    else:
        # Se não há junções, apenas aplicar produto cartesiano entre tabelas filtradas
        join_tree = " × ".join([filtered_tables[t] for t in table_order])
    
    # 6. Aplicar condições restantes que não puderam ser empurradas para baixo
    if remaining_conditions:
        remaining_cond_str = " AND ".join(remaining_conditions)
        join_tree = f"σ[{remaining_cond_str}]({join_tree})"
    
    # 7. Aplicar projeção final
    if projections:
        projection_str = ", ".join(projections)
        join_tree = f"π[{projection_str}]({join_tree})"
    
    return join_tree
