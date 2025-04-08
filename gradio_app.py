import io
import sys
import base64
from contextlib import redirect_stdout, redirect_stderr
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg for non-interactive mode

import gradio as gr

# Import your existing code
from model import llm
from basic_function_collection import python_repl_tool, wikipedia_tool
from taskgen import Agent, Function
from essential_function import python_generator_tool, python_run_tool, python_debug_tool

# Define the python_generate_and_run_code function
def python_generate_and_run_code(shared_variables, instruction: str) -> str:
    ''' Generates and runs code based on instruction.
    You can only import the following modules: math, numpy, random, datetime, re, matplotlib, pandas, plotly
    You can use all Equipped Functions except use_llm and end_task.
    Returns 1) the result of all print statements in code, or error messages, and 2) the code '''

    # Append context to tool
    if shared_variables and 'agent' in shared_variables:
        instruction = f"Context: {shared_variables['agent'].overall_task}\nPrevious Subtasks: {shared_variables['agent'].subtasks_completed}\nInstruction: {instruction}"
    
    # Generate Code
    python_code = python_generator_tool(shared_variables, instruction)['Generated Code']

    # Run and Debug Code
    for _ in range(3):
        output = python_run_tool(shared_variables, python_code)

        if output[:5] == "Error":
            debugged_code = python_debug_tool(instruction, python_code, output)
            python_code = debugged_code['Corrected Code']
        else:
            break

    return output, python_code

# Create Function object
python_generate_and_run_code_tool = Function(
    external_fn=python_generate_and_run_code,
    fn_name='python_generate_and_run_code_tool',
    is_compulsory=True
)

# Create the agent
def create_agent():
    return Agent('Generalist Agent',
                '''Helps user with tasks. When deterministic output or plots are needed, generate and run code. Do not use LLM for calculations.''',
                summarise_subtasks_count=10,
                llm=llm).assign_functions(
        [wikipedia_tool, python_generate_and_run_code_tool])

# Function to execute code and capture figures
def execute_code_and_capture_plots(code):
    # Set up figure capture
    import matplotlib.pyplot as plt
    plt.close('all')  # Close any open figures
    
    # Execute the code
    local_vars = {}
    try:
        exec(code, globals(), local_vars)
        
        # Check if any figures were created
        figures = []
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            img_data = io.BytesIO()
            fig.savefig(img_data, format='png')
            img_data.seek(0)
            encoded = base64.b64encode(img_data.read()).decode('utf-8')
            figures.append(encoded)
        
        return figures
    except Exception as e:
        print(f"Error capturing plots: {str(e)}")
        return []

# Function to run the agent and capture all outputs
def run_agent(input_text):
    # Create a fresh agent instance for each run
    agent = create_agent()
    
    # Capture all standard output and errors
    captured_output = io.StringIO()
    captured_error = io.StringIO()
    
    # Store generated code for later execution
    generated_code = None
    
    with redirect_stdout(captured_output), redirect_stderr(captured_error):
        try:
            agent_result = agent.run(input_text)
            
            # Try to extract the generated code from the output
            output_text = captured_output.getvalue()
            if "Generated code: ```" in output_text:
                code_start = output_text.find("Generated code: ```") + len("Generated code: ```")
                code_end = output_text.find("```", code_start)
                if code_end > code_start:
                    generated_code = output_text[code_start:code_end].strip()
            
            # Add the final result to the captured output
            if agent_result and str(agent_result) not in captured_output.getvalue():
                print("\nFinal Result:")
                print(agent_result)
        except Exception as e:
            print(f"Error occurred: {str(e)}")
    
    # Combine standard output and error streams
    full_output = captured_output.getvalue()
    if captured_error.getvalue():
        full_output += "\nERRORS:\n" + captured_error.getvalue()
    
    # Return the code if it was found
    if generated_code:
        full_output += "\n\nEXTRACTED CODE:\n```python\n" + generated_code + "\n```"
    
    # Extract plots if code was generated
    plots = []
    if generated_code:
        plots = execute_code_and_capture_plots(generated_code)
    
    return full_output, plots

# Create Gradio interface
def process_input(user_input):
    text_output, plots = run_agent(user_input)
    
    # Convert base64 images to gradio images
    image_outputs = []
    for plot_data in plots:
        image_outputs.append(f"data:image/png;base64,{plot_data}")
    
    return text_output, image_outputs if image_outputs else None

# Define the Gradio interface
def create_interface():
    with gr.Blocks(title="Agent Task Runner") as interface:
        gr.Markdown("# Agent Task Runner")
        gr.Markdown("Enter a task and the agent will process it. All console outputs will be displayed.")
        
        with gr.Row():
            input_text = gr.Textbox(
                lines=3, 
                placeholder="Enter your task here...", 
                label="Input"
            )
        
        with gr.Row():
            submit_btn = gr.Button("Run Agent")
        
        with gr.Row():
            output_text = gr.Textbox(
                lines=15,
                label="Console Output",
                show_copy_button=True
            )
        
        with gr.Row():
            output_gallery = gr.Gallery(
                label="Generated Plots",
                show_label=True,
                elem_id="gallery",
                columns=2,
                height=400
            )
        
        # Example tasks
        examples = gr.Examples(
            examples=[
                ["Plot me a graph of y = 2x^2"],
                ["Plot a sine wave with amplitude 2 and frequency 0.5"],
                ["Create a bar chart showing sales data for Q1: 120, Q2: 150, Q3: 180, Q4: 210"],
                ["John has 5 apples. John received another 21 more from Mary, and gave 10 to Tim. How many apples does John have at the end?"],
                ["Build me a gradio application for calculating bmi"]
            ],
            inputs=input_text
        )
        
        # Set up the submit button click event
        submit_btn.click(
            fn=process_input,
            inputs=input_text,
            outputs=[output_text, output_gallery]
        )
    
    return interface

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch()