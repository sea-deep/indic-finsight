with open('/home/dipak/code/kaggle-hackathon/agent_backend/build_notebook.py', 'r') as f:
    code = f.read()

import re
code = re.sub(r"options_match = re.search\(r'\\\[.*", r"options_match = re.search(r'\[([^\]]*?\|[^\]]*?)\]', final_answer_raw, re.IGNORECASE | re.DOTALL)", code)
code = re.sub(r"final_answer = re.sub\(r'\\\[.*", r"final_answer = re.sub(r'\[([^\]]*?\|[^\]]*?)\]', '', final_answer_raw, flags=re.IGNORECASE | re.DOTALL).strip()", code)
code = code.replace("final_answer.replace('\\\\\\\\n', '\\\\n')", "final_answer.replace('\\\\n', '\\n')")

with open('/home/dipak/code/kaggle-hackathon/agent_backend/build_notebook.py', 'w') as f:
    f.write(code)
