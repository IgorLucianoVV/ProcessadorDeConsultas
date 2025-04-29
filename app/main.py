import streamlit as st
import matplotlib.pyplot as plt
from models.query.parser import QueryParser
from models.query.manager import QueryManager
from utils.graphs import Graph
from utils.algebra import sql_to_algebra, optimize_algebra

st.set_page_config('Trabalho Consultas', page_icon='👨‍💻', layout='wide')
st.title('Envio e Otimização de Consultas')

with st.form('Formulário de Envio de consultas'):
    # A string com a consulta SQL é entrada na interface gráfica 
    user_query = st.text_area(
        'Campo de consultas', placeholder='Digite sua consulta aqui.')
    submit = st.form_submit_button('Enviar')

if submit:
    if user_query == '':
        st.warning('Requisição vazia não pode ser realizada', icon='❗')
        st.stop()
    
    # A string é parseada e o comando SQL é validado além de validar se as tabelas existem e se 
    # os campos informados no select existem nas tabelas 
    parsed_query = QueryParser.parse_sql(user_query) 
    manager = QueryManager()
    
    if manager.is_query_valid(parsed_query):
        st.write(parsed_query)
        # O comando SQL é convertido para álgebra relacional 
        relational_query = sql_to_algebra(parsed_query)
        # Mostrar na Interface a conversão do SQL para álgebra relacional 
        st.write('### _Álgebra Relacional_')
        st.write(relational_query)
        
        optimized_query = optimize_algebra(relational_query)
        
        # TODO A álgebra relacional é otimizada conforme as heurísticas solicitadas (ver item 5) 
        st.write('### _Álgebra Relacional - Otimizada_')
        st.write(optimized_query)
        
        # TODO O grafo de operadores é construído em memória 
        graph = Graph().build_operator_graph(parsed_query)
        # TODO O grafo de operadores deve ser mostrado na Interface gráfica 
        st.write('### _Gráfico de Operadores_')    
        st.write(graph)
        # TODO O resultado da consulta mostrando cada operação e a ordem que será executada, é exibido 
        # na interface gráfica (plano de execução) 
        st.write('### _Plano de Execução_')
        