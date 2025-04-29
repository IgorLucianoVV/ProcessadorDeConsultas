import re
from models.db.patterns import SELECT_PATTERN, FROM_PATTERN, WHERE_PATTERN, INNER_JOIN_PATTERN
class QueryParser:
    """
    Parser SQL simples: SELECT, FROM, zero ou mais INNER JOINs e WHERE.
    """

    @staticmethod
    def parse_sql(sql: str) -> dict:
        # 1) Limpeza: remove ';' final se existir, normaliza múltiplos espaços
        sql = re.sub(r';\s*$', '', sql.strip())
        sql = re.sub(r'\s+', ' ', sql)

        # 2) SELECT …
        select_match = re.search(SELECT_PATTERN, sql)

        # 3) FROM …
        from_match = re.search(FROM_PATTERN, sql)
        
        # 4) ZERO OU MAIS INNER JOINs
        join_match = re.finditer(INNER_JOIN_PATTERN, sql)

        # 5) WHERE …
        where_match = re.search(WHERE_PATTERN, sql)

        return {
            'select': [
                c.strip() for c in select_match.group('cols').split(',')
            ] if select_match else [],
            'from': from_match.group('table') if from_match else '',
            'joins': [
                {'table': m.group('table'), 'condition': m.group('cond')}
                for m in join_match
            ],
            'where': where_match.group('cond').strip() if where_match else ''

        }
