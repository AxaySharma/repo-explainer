import sys
import os

# Insert parent directory into sys.path to enable imports of agent packages
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from agent.repo_explainer import run_agent, AgentResult

# Initialize rich Console
console = Console()

def main(
    repo: str = typer.Option(..., "--repo", help="Local path or GitHub URL"),
    question: str = typer.Option(..., "--question", help="Question about the codebase"),
    max_iterations: int = typer.Option(10, "--max-iterations", help="Max agent iterations"),
    verbose: bool = typer.Option(False, "--verbose", help="Show tool call details"),
) -> None:
    """Run the Repo Explainer Agent to explore a repository and answer a question."""
    try:
        # STEP 1 — Header
        header_text = f"[bold cyan]🔍 Repo Explainer Agent[/bold cyan]\n\n[bold]Repo:[/bold] {repo}\n[bold]Question:[/bold] {question}"
        console.print(Panel(header_text, border_style="cyan"))
        
        # STEP 2 — Thinking spinner wrapping core run_agent invocation
        with console.status("[bold green]Exploring codebase..."):
            result = run_agent(
                repo_input=repo,
                question=question,
                max_iterations=max_iterations
            )
            
        # STEP 3 — Handle and display result
        if result.success:
            markdown_answer = Markdown(result.answer)
            console.print(Panel(markdown_answer, title="[bold green]✅ Answer[/bold green]", border_style="green"))
        else:
            console.print(Panel(f"[bold red]Error:[/bold red] {result.error}", title="[bold red]❌ Failure[/bold red]", border_style="red"))
            
        # STEP 4 — Stats table (always shown if result exists)
        table = Table(title="📊 Run Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Value", width=20)
        
        table.add_row("Iterations", f"{result.iterations} / {max_iterations}")
        table.add_row("Tools Used", str(len(result.tools_used)))
        
        success_val = "✅ Yes" if result.success else "❌ No"
        table.add_row("Success", success_val)
        
        console.print(table)
        
        # STEP 5 — Verbose tool details
        if verbose and result.tools_used:
            tools_list = "\n".join([f"• {t}" for t in result.tools_used])
            console.print(Panel(tools_list, title="🔧 Tools Called", border_style="yellow"))
            
        # Exit if run was not successful
        if not result.success:
            raise typer.Exit(code=1)
            
    except ValueError as e:
        console.print(Panel(f"[bold red]ValueError:[/bold red] {e}", title="❌ Error", border_style="red"))
        raise typer.Exit(code=1)
    except typer.Exit:
        # Propagate typer exits directly without wrapping
        raise
    except Exception as e:
        console.print(Panel(f"[bold red]Unexpected error:[/bold red] {e}", title="❌ Error", border_style="red"))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    typer.run(main)
