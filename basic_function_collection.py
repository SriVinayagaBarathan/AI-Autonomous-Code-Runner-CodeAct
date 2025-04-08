

def wikipedia_tool(search_query: str) -> str:
    ''' Uses search_query and returns text from wikipedia '''
    from langchain.tools import WikipediaQueryRun
    from langchain.utilities import WikipediaAPIWrapper

    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()).run(search_query)


def python_repl_tool(python_code: str) -> str:
    from langchain_core.tools import Tool
    from langchain_experimental.utilities import PythonREPL
    ''' Runs python_code, returns the final result, or any debugging errors '''
    python_repl = PythonREPL()
    return python_repl.run(python_code)