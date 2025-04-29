SELECT_PATTERN = r'(?i)select\s+(?P<cols>.+?)\s+from\s+'

FROM_PATTERN = (
    r'(?i)from\s+'
    r'(?P<table>[\w\.]+(?:\s+\w+)?)'
    r'(?=\s+join|\s+where|$)'
)

WHERE_PATTERN = r'(?i)\swhere\s+(?P<cond>.+)$'

INNER_JOIN_PATTERN =  (
    r'(?i)(?:inner\s+)?join\s+'                  
    r'(?P<table>[\w\.]+(?:\s+\w+)?)\s+'           
    r'on\s+(?P<cond>.+?)'                         
    r'(?=\s+(?:inner\s+)?join|\s+where|$)'        
)