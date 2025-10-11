#!/usr/bin/env python3
# General CrewAI Script
# Generated: test_syntax_001

import os
import sys
from datetime import datetime
from pathlib import Path
from crewai import Agent, Task, Crew, Process

# Model configuration
MODELS = {'researcher': 'gemini-flash', 'writer': 'gpt-4', 'planner': 'claude-3'}

# General-purpose agents
researcher = Agent(
    role="Researcher",
    goal="Analyze requirements and collect information",
    backstory="Professional research and analysis expert",
    verbose=True,
    llm=MODELS.get('researcher', 'gemini-flash'),
    allow_delegation=False
)

writer = Agent(
    role="Writer",
    goal="Create clear documentation",
    backstory="Expert in creating well-structured documents",
    verbose=True,
    llm=MODELS.get('writer', 'gpt-4'),
    allow_delegation=False
)

planner = Agent(
    role="Planner",
    goal="Develop execution plans",
    backstory="Expert in systematic planning and project management",
    verbose=True,
    llm=MODELS.get('planner', 'claude-3'),
    allow_delegation=False
)

# Tasks
task1 = Task(
    description=f"Analyze requirements and collect information: """ + requirement + """",
    expected_output="Requirements analysis and collected information",
    agent=researcher
)

task2 = Task(
    description="Create systematic documentation based on analysis",
    expected_output="Well-organized documentation",
    agent=writer
)

task3 = Task(
    description="Develop specific execution plans",
    expected_output="Step-by-step execution plan",
    agent=planner
)

# Create crew
crew = Crew(
    agents=[researcher, writer, planner],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True
)

def main():
    print("General CrewAI - Starting execution")
    print(f"Execution ID: {execution_id}")
    print(f"Project Path: {project_path}")

    try:
        output_dir = Path(""" + f'"{project_path}"' + """) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = crew.kickoff()

        print("Execution completed!")
        print(result)

        result_file = output_dir / f"crew_result_{'{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}'}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(str(result))

        print(f"Result saved to: {'{result_file}'}")

    except Exception as e:
        print(f"Error occurred: {'{e}'}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
