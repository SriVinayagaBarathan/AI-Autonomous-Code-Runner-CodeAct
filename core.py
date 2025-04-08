from model import llm

from basic_function_collection import python_repl_tool,wikipedia_tool

from taskgen import *

from essential_function import python_generator_tool, python_run_tool,python_debug_tool



# print(llm(system_prompt = 'You are a classifier to classify the sentiment of a sentence',
#     user_prompt = 'It is a hot and sunny day'))


# print(python_repl_tool("print(2+3)"))




# from taskgen import Agent
# agent = Agent('Weather Agent', 'Returns the Weather',
#              llm = llm).assign_functions(tool.fn)


# Uses LLM to generate Code
def python_generate_and_run_code(shared_variables, instruction: str) -> str:
    ''' Generates and runs code based on instruction.
You can only import the following modules: math, numpy, random, datetime, re, matplotlib, pandas, plotly
You can use all Equipped Functions except use_llm and end_task.
Returns 1) the result of all print statements in code, or error messages, and 2) the code '''
    # from termcolor import colored

    # Append context to tool
    if shared_variables and 'agent' in shared_variables:
        instruction = f"Context: {shared_variables['agent'].overall_task}\nPrevious Subtasks: {shared_variables['agent'].subtasks_completed}\nInstruction: {instruction}"
    # Generate Code
    python_code = python_generator_tool(shared_variables, instruction)['Generated Code']
    # print(colored(f'Generated code: ```{python_code}```', 'magenta'))

    # Run and Debug Code
    for _ in range(3):
        output = python_run_tool(shared_variables, python_code)

        if output[:5] == "Error":
            debugged_code = python_debug_tool(instruction, python_code, output)
            python_code = debugged_code['Corrected Code']
            # print(colored(output, 'red'))
            # print(colored(f'Debugged code: ```{python_code}```', 'magenta'))
        else:
            break

    return output, python_code

# Make this function compulsory
python_generate_and_run_code_tool = Function(
    external_fn = python_generate_and_run_code,
    fn_name = 'python_generate_and_run_code_tool',
    is_compulsory = True)



agent = Agent('Generalist Agent',
'''Helps user with tasks. When deterministic output or plots are needed, generate and run code. Do not use LLM for calculations.''',
             summarise_subtasks_count = 10,
             llm = llm).assign_functions(
    [wikipedia_tool, python_generate_and_run_code_tool])




# agent.run('John has 5 apples. John received another 21 more from Mary, and gave 10 to Tim. How many apples does John have at the end?')


# agent.run('Plot me a graph of y = 2x^2')



# agent.run('Build me a gradio application for calculating bmi')


def run_it(command):
    agent.run(command)



run_it("Plot me a graph of y = 2x^2")