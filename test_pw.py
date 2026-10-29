import sys
try:
    print('test print')
    with open('test_pw.log', 'w') as lf:
        lf.write('print succeeded
')
except Exception as e:
    with open('test_pw.log', 'w') as lf:
        lf.write(f'print failed: {e}
')
