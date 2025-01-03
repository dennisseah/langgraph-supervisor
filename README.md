# langgraph-supervisor
langgraph multi agent supervisor

## Setup

1. Clone the repository
2. `cd langgraph-supervisor` (root directory of this git repository)
3. `python -m venv .venv`
4. `poetry install` (install the dependencies)
5. code . (open the project in vscode)
6. install the recommended extensions (cmd + shift + p -> `Extensions: Show Recommended Extensions`)
7. `pre-commit install` (install the pre-commit hooks)
8. copy the `.env.sample` file to `.env` and fill in the values

## Samples
```sh
python -m langgraph_supervisor.graph
```



## Unit Test Coverage

```sh
python -m pytest -p no:warnings --cov-report term-missing --cov=langgraph_supervisor tests
```