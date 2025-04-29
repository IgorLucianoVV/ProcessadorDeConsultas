import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st
from utils.algebra import extract_tables, extract_conditions, extract_joins, extract_projection

class Graph:
    def __init__(self):
        self.G = nx.DiGraph()
    
    def build_operator_graph(self, parsed_query):
        """
        Constrói o grafo de operadores com base na consulta parseada.
        Retorna uma figura matplotlib para exibição no Streamlit.
        """
        # Limpar grafo existente
        self.G.clear()
        
        # Extrair informações da consulta
        tables = [parsed_query['from']] + [j['table'] for j in parsed_query['joins']]
        join_conditions = [j['condition'] for j in parsed_query['joins']]
        where_condition = parsed_query.get('where', '')
        projection_cols = parsed_query.get('select', [])
        
        # Adicionar nós para as tabelas (folhas)
        for i, table in enumerate(tables):
            self.G.add_node(f"Table: {table}", type="table", level=0, pos=(i*2, 0))
        
        # Adicionar nós para joins, se houver
        if join_conditions:
            prev_node = f"Table: {tables[0]}"
            for i, (table, condition) in enumerate(zip(tables[1:], join_conditions)):
                join_node = f"Join: {condition}"
                self.G.add_node(join_node, type="join", level=1, pos=(i, 1))
                self.G.add_edge(prev_node, join_node)
                self.G.add_edge(f"Table: {table}", join_node)
                prev_node = join_node
        else:
            # Caso só haja uma tabela sem joins
            prev_node = f"Table: {tables[0]}"
        
        # Adicionar nó para condição WHERE, se houver
        if where_condition:
            where_node = f"Where: {where_condition}"
            self.G.add_node(where_node, type="selection", level=2, pos=(len(tables)/2, 2))
            self.G.add_edge(prev_node, where_node)
            prev_node = where_node
        
        # Adicionar nó para projeção (SELECT)
        proj_cols = ", ".join(projection_cols)
        proj_node = f"Project: {proj_cols}"
        self.G.add_node(proj_node, type="projection", level=3, pos=(len(tables)/2, 3))
        self.G.add_edge(prev_node, proj_node)
        
        # Criar figura para visualização
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Definir posições dos nós para layout em níveis
        pos = {}
        for node in self.G.nodes:
            attrs = self.G.nodes[node]
            level = attrs.get('level', 0)
            x_pos = attrs.get('pos', (0, 0))[0]
            pos[node] = (x_pos, level)
        
        # Definir cores para os diferentes tipos de nós
        colors = []
        for node in self.G.nodes:
            node_type = self.G.nodes[node].get('type', '')
            if node_type == 'table':
                colors.append('lightblue')
            elif node_type == 'join':
                colors.append('lightgreen')
            elif node_type == 'selection':
                colors.append('salmon')
            elif node_type == 'projection':
                colors.append('gold')
            else:
                colors.append('gray')
        
        # Desenhar grafo
        nx.draw(self.G, pos, with_labels=True, node_color=colors, 
                node_size=3000, font_size=8, ax=ax, arrows=True)
        
        plt.title("Grafo de Operadores da Consulta")
        
        return fig
    
    def generate_execution_plan(self):
        """
        Gera o plano de execução com base no grafo de operadores.
        Retorna uma lista de passos de execução.
        """
        # Usar a ordem topológica invertida para determinar a ordem de execução
        steps = []
        for i, node in enumerate(reversed(list(nx.topological_sort(self.G)))):
            node_type = self.G.nodes[node].get('type', '')
            if node_type == 'table':
                steps.append(f"{i+1}. Ler tabela: {node.replace('Table: ', '')}")
            elif node_type == 'join':
                steps.append(f"{i+1}. Executar junção: {node.replace('Join: ', '')}")
            elif node_type == 'selection':
                steps.append(f"{i+1}. Aplicar filtro WHERE: {node.replace('Where: ', '')}")
            elif node_type == 'projection':
                steps.append(f"{i+1}. Projetar colunas: {node.replace('Project: ', '')}")
        
        return steps