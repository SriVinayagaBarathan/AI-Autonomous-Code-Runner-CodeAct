from taskgen import *
from model import llm
from basic_function_collection import wikipedia_tool



shared_variables = {'agent': Agent('Generalist Agent', 'Does Everything', llm = llm).assign_functions([wikipedia_tool])}

def python_generator_tool(shared_variables, instruction: str):
    '''Generate code only based on instruction without any additional context.
Ensure that you define all variables and list out all imports.
You can only import the following modules: math, numpy, random, datetime, re, matplotlib, pandas, plotly
Do not define any new functions
You are able to use all Equipped Functions except use_llm and end_task
The output of Equipped Function will be in a dictionary format
Ensure all required output are in print()'''

    agent = shared_variables['agent']

    return strict_json(f'''Generate code based only on ```{instruction}``` without additional context.
Ensure that you define all variables and list out all imports.
You can only import the following modules: math, numpy, random, datetime, re, matplotlib, pandas, plotly
Do not define any new functions
You are able to use the following Equipped Functions:
```{agent.list_functions(
fn_list = [agent.function_map[function_name] for function_name in agent.function_map if function_name not in ['use_llm', 'end_task']])}
```
The output of Equipped Function will be in a dictionary format
You must use Equipped Functions whenever possible
Ensure all required output are in print()''',
                       '',
                                     output_format = {'Generated Code': 'type: code'},
                      llm = agent.llm)




def python_run_tool(shared_variables, code_snippet: str) -> str:
    '''Runs code_snippet and outputs the result of all print statements'''
    import sys
    import io
    import math
    import numpy
    import random
    import datetime
    import re
    import matplotlib
    import pandas
    import plotly

    agent = shared_variables['agent']

    # wrap external functions to pass in shared_variables as well
    def external_function_wrapper(function_name, shared_variables):
        def external_function(**function_params):
            return agent.function_map[function_name](shared_variables=shared_variables, **function_params)
        return external_function

    # Capture the output
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # Safe environment to execute the user code
        allowed_globals = {
            '__builtins__': {
                'print': print,
                'range': range,
                'len': len,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'any': any,
                'all': all,
                'sorted': sorted,
                'zip': zip,
                'map': map,
                'filter': filter,
                '__import__': __import__,
                'math': math,  # Allow access to the math module
                'datetime': datetime, # Allow access to datetime module
                'random': random, # Allow access to random module
                'numpy': numpy, # Allow access to numpy module
                're': re,
                'matplotlib': matplotlib,
                'pandas': pandas,
                'plotly': plotly
            }
        }

        # add in equipped functions one by one
        for function_name in agent.function_map:
            if function_name not in ['use_llm', 'end_task', 'python_generate_and_run_code_tool']:
                allowed_globals['__builtins__'][function_name] = external_function_wrapper(function_name, shared_variables)

        safe_locals = {}

        exec(code_snippet, allowed_globals, safe_locals)
        output = sys.stdout.getvalue()
    except Exception as e:
        output = f"Error: {e}"
    finally:
        # Restore the original stdout
        sys.stdout = old_stdout

    return output



python_debug_tool = Function('''Debugs Python Code and returns corrected code.
Instruction: <instruction: str>
Current Code: <python_code: str>
Error Message: <error_msg: str>''',
                                 output_format = {'Thoughts': 'How to correct code', 'Corrected Code': 'type: code'},
                             fn_name = 'python_debug_tool',
                             llm = llm)