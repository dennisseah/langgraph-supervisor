import asyncio
import logging
from typing import Callable, Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import TypedDict

from langgraph_supervisor.hosting import container
from langgraph_supervisor.protocols.i_azure_openai_service import IAzureOpenAIService
from langgraph_supervisor.tools.tools import cd_interest_rate, saving_interest_rate

agents: list[str] = ["saving-agent", "cd-agent"]
options: list[str] = agents + ["FINISH"]

logger = container[logging.Logger]

# instantiate the AzureOpenAIService and get the completion model
llm = container[IAzureOpenAIService].get_model()

# Define the system prompt
system_prompt = (
    "You are my bank agent tasked with managing a conversation between the"
    f" following agent: {agents}. Given the following my request,"
    " respond with the agent to act next. Each agent will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)


# customer agent node. This is the main node that routes to the next agent
# based on the response to the saving or CD interest rate agents, or finishes
def customer_agent_node(
    state: MessagesState,
) -> Command[Literal[*agents, "__end__"]]:  # type: ignore
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]

    for message in messages:
        logger.info(f"Message: {message}")

    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]

    if goto == "FINISH":
        goto = END

    return Command(goto=goto)


class Router(TypedDict):
    """Agent to route to next. If no agents needed, route to FINISH."""

    next: Literal[*options]  # type: ignore


# helper function to create an agent node (saving or CD)
def create_agent_node(
    name: str, agent: CompiledGraph
) -> Callable[[MessagesState], Command[Literal["customer_agent"]]]:
    def node(state: MessagesState) -> Command[Literal["customer_agent"]]:
        result = agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name=name)
                ]
            },
            goto="customer_agent",
        )

    return node


def build_graph() -> CompiledStateGraph:
    saving_agent = create_react_agent(
        llm,
        tools=[saving_interest_rate],
        state_modifier="You are the saving account agent. You are "
        "tasked with providing the saving interest rate.",
    )
    cd_agent = create_react_agent(
        llm,
        tools=[cd_interest_rate],
        state_modifier="You are the CD account agent. You are "
        "tasked with providing the CD interest rate.",
    )

    saving_node = create_agent_node("saving-agent", saving_agent)
    cd_node = create_agent_node("cd-agent", cd_agent)

    builder = StateGraph(MessagesState)
    builder.add_edge(START, "customer_agent")
    builder.add_node("customer_agent", customer_agent_node)
    builder.add_node("saving-agent", saving_node)
    builder.add_node("cd-agent", cd_node)
    return builder.compile()


async def run(graph: CompiledStateGraph):
    # sending in the human message to the graph and routing begins
    async for state in graph.astream(
        {
            "messages": [
                HumanMessage(
                    content="Advise me to keep my money in saving account if the saving interest "
                    "rate higher than the CD interest rate. Otherwise, advise me to "
                    "put my money in CD account.",
                )
            ]
        },
        subgraphs=True,
    ):
        logger.info("graph.astream: " + str(state))

        if "agent" in state[1] and "messages" in state[1]["agent"]:  # type: ignore
            agent_name = state[0][0]  # type: ignore
            for message in state[1]["agent"]["messages"]:  # type: ignore
                if message.content:
                    print(f"Agent {agent_name}: {message.content}")
                elif message.tool_calls:
                    for tool_call in message.tool_calls:
                        print(f"Tool: {tool_call["name"]}")


if __name__ == "__main__":
    graph = build_graph()
    asyncio.run(run(graph))
