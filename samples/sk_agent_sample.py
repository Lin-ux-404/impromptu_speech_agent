import streamlit as st
import asyncio
import os
from typing import Annotated
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.agents.strategies import KernelFunctionSelectionStrategy, KernelFunctionTerminationStrategy, DefaultTerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.functions import kernel_function, KernelArguments, KernelFunctionFromPrompt
from azure.ai.projects.models import BingGroundingTool, CodeInterpreterTool, ToolSet
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# === CONFIG ===
SERVICE_ID = "agent"

# Add constants for agent names
SEARCHER_NAME = "BingSearchAgent"
CODER_NAME = "DataAnalysisAgent"

class BingGroundingPlugin:
    def __init__(self):
        # Get the connection from the project client first
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(exclude_environment_credential=True, exclude_managed_identity_credential=True),
            conn_str=os.getenv("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
        )
        bing_connection = self.project_client.connections.get(
            connection_name=os.getenv("BING_CONNECTION_NAME")
        )
        self._tool = BingGroundingTool(connection_id=bing_connection.id)

    @kernel_function(description="Search Bing for real-time web results")
    async def search(self, query: Annotated[str, "The search query"]) -> Annotated[str, "Search results"]:
        toolset = ToolSet()
        toolset.add(self._tool)
        
        # Create agent with search capabilities
        agent = self.project_client.agents.create_agent(
            model=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
            instructions="Search and summarize information from Bing. Include relevant statistics and data that could be visualized.",
            toolset=toolset
        )
        
        try:
            # Create thread and message
            thread = self.project_client.agents.create_thread()
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            # Process the search
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            if run.status == "completed":
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                response = messages.get_last_text_message_by_role("assistant")
                return response.text.value if response else "No results found"
            else:
                return f"Search failed: {run.last_error}"
                
        finally:
            # Cleanup
            self.project_client.agents.delete_agent(agent.id)


class CodeInterpreterPlugin:
    def __init__(self):
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(exclude_environment_credential=True, exclude_managed_identity_credential=True),
            conn_str=os.getenv("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
        )   
        self.tool = CodeInterpreterTool()

    @kernel_function(description="Execute Python code and visualize results")
    async def execute_code(self, code: Annotated[str, "The code to execute"]) -> Annotated[str, "Execution results"]:
        toolset = ToolSet()
        toolset.add(self.tool)
        
        agent = self.project_client.agents.create_agent(
            model=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
            instructions="""Execute Python code and create visualizations.
            For any visualization:
            1. Use matplotlib with proper styling
            2. Save figures with high DPI for clarity
            3. Include proper titles, labels, and legends
            4. Return both the analysis text and visualization""",
            toolset=toolset
        )
        
        thread = self.project_client.agents.create_thread()
        
        try:
            # Create message with the code
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=code
            )
            
            # Run the code
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            if run.status == "completed":
                # Get messages and handle images
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                response = messages.get_last_text_message_by_role("assistant")
                
                # Handle generated plots
                image_paths = []
                for image_content in messages.image_contents:
                    file_name = f"{image_content.image_file.file_id}_image_file.png"
                    self.project_client.agents.save_file(
                        file_id=image_content.image_file.file_id,
                        file_name=file_name
                    )
                    image_paths.append(file_name)
                
                return {
                    'text': response.text.value if response else "Code executed successfully",
                    'image_path': image_paths[0] if image_paths else None,
                    'status': 'complete'
                }
            else:
                return {
                    'text': f"Code execution failed: {run.last_error}",
                    'image_path': None,
                    'status': 'failed'
                }
            
        finally:
            # Cleanup
            self.project_client.agents.delete_agent(agent.id)


# === MAIN AGENT LOGIC ===
def main():
    st.set_page_config(page_title="AI Search & Analysis Assistant")

    @st.cache_resource
    def create_kernel():
        kernel = Kernel()
        kernel.add_service(
            AzureChatCompletion(
                service_id="agent",
                deployment_name=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
            )
        )
        kernel.add_plugin(BingGroundingPlugin(), plugin_name="bing")
        kernel.add_plugin(CodeInterpreterPlugin(), plugin_name="code")
        return kernel

    async def initialize_chat():
        kernel = create_kernel()
        settings = kernel.get_prompt_execution_settings_from_service_id("agent")
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        
        search_agent = ChatCompletionAgent(
            kernel=kernel,
            name=SEARCHER_NAME,
            instructions=f"""You are a web search assistant.
            1. Use Bing to search for current information
                - Present data clearly and consistently
            2. When returning data that should be visualized (numbers, statistics, rankings):
               - Tell the user that you have found the data needed to create the visualization
            """,
            arguments=KernelArguments(settings=settings),
        )

        code_agent = ChatCompletionAgent(
            kernel=kernel,
            name=CODER_NAME,
            instructions=f"""You are a Python visualization expert.
            1. Create clear visualizations using matplotlib and Streamlit for any data provided by {SEARCHER_NAME}.
               - Present data clearly and consistently
            2. Always include:
               ```python
               import matplotlib.pyplot as plt
               plt.style.use('seaborn')
               ```
            3. End all plots with:
               ```python
               plt.tight_layout()
               st.pyplot(plt.gcf())
               plt.close()
               ```
            4. Tell {SEARCHER_NAME} and the user that the data has been visualized
            """,
            arguments=KernelArguments(settings=settings),
        )

        selection_function = KernelFunctionFromPrompt(
            function_name="selection",
            prompt=f"""
            Determine which participant takes the next turn in a conversation based on the the most recent participant.
            State only the name of the participant to take the next turn.
            No participant should take more than one turn in a row.

            Choose only from these participants:
            - {CODER_NAME}
            - {SEARCHER_NAME}

            Always follow these rules when selecting the next participant:
            - After user input, it is {SEARCHER_NAME}'s turn.
            - After {SEARCHER_NAME} replies, it is {CODER_NAME}'s turn.
            - After {CODER_NAME} provides feedback, it is {SEARCHER_NAME}'s turn.
            
            History:
            {{{{$history}}}}
            """,
        )

        
        termination_function = KernelFunctionFromPrompt(
            function_name="termination",
            prompt="""
            Determine if the answer has been approved. 
            
            If so, respond with a single word: yes

            History:
            {{$history}}
            """,
        )


        chat = AgentGroupChat(
            agents=[search_agent, code_agent],
            selection_strategy=KernelFunctionSelectionStrategy(
                function=selection_function,
                kernel=kernel,
                result_parser=lambda result: (
                    str(result.value[0]) if result.value and
                    str(result.value[0]).lower() != "none"
                    else None
                ),
                agent_variable_name="agents",
                history_variable_name="history"
            ),
            # termination_strategy=KernelFunctionTerminationStrategy(
            #     agents=[code_agent, search_agent],
            #     function=termination_function,
            #     kernel=kernel,
            #     result_parser=lambda result: str(result.value[0]).lower() == "yes",  # Never terminate automatically
            #     history_variable_name="history",
            #     maximum_iterations=3
            # )
        )
        return chat
    

    async def run_chat(prompt):
        messages = []
        try:
            if st.session_state["chat"] is None:
                st.session_state["chat"] = await initialize_chat()

            chat = st.session_state["chat"]
            await chat.add_chat_message(message=prompt)

            async for response in chat.invoke():
                if response.role != "tool":
                    response_dict = {
                        "role": response.name.lower(),
                        "content": response.content if isinstance(response.content, str)
                                else response.content.get("text", "")
                    }

                    with st.chat_message(response_dict["role"]):
                        st.write(response_dict["content"])

                    # === Extract and display image directly from thread ===
                    if hasattr(chat, "project_client") and hasattr(chat, "thread_id"):
                        project_client = chat.project_client
                        messages_obj = project_client.agents.list_messages(thread_id=chat.thread_id)
                        print(messages_obj)

                        if hasattr(messages_obj, "image_contents"):
                            for image_content in messages_obj.image_contents:
                                file_name = "top_highest_grossing_movies.png"
                                file_path = os.path.join("images", file_name)
                                os.makedirs("images", exist_ok=True)

                                project_client.agents.save_file(
                                    file_id=image_content.image_file.file_id,
                                    file_name=file_path
                                )

                                abs_path = os.path.abspath(file_path)
                                if os.path.exists(abs_path):
                                    with st.chat_message(response_dict["role"]):
                                        st.image(abs_path, caption="Generated Chart")
                                    response_dict["image_path"] = abs_path
                                    break  # Only show one image

                    # Save message history
                    messages.append(response_dict)
                    st.session_state["messages"].append(response_dict)

        except Exception as e:
            st.error(f"Error: {str(e)}")

        return messages



    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "chat" not in st.session_state:
        st.session_state["chat"] = None

    st.title("AI Search & Analysis Assistant")
    st.caption("Ask questions and get information with data visualization!")

    # Display chat history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "image_path" in message and message["image_path"]:
                st.image(message["image_path"])

    # Chat input
    if prompt := st.chat_input("Ask anything..."):
        user_message = {"role": "user", "content": prompt}
        st.session_state["messages"].append(user_message)
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Processing..."):
            # Create new event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_chat(prompt))
            finally:
                loop.close()

    # Reset button
    if st.button("New Conversation"):
        st.session_state["messages"] = []
        st.session_state["chat"] = None
        st.rerun()

if __name__ == "__main__":
    load_dotenv()
    main()
