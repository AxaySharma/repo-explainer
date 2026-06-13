import sys
import os

# Insert project root into sys.path to enable imports of agent/eval modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import typer
from rich.console import Console
from rich.panel import Panel

# Initialize Console
console = Console()

def main(
    repo: str = typer.Option("evals/fixtures/sample_project", "--repo", help="Path to repo to evaluate against"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save results to optimizer/results/"),
    prompt: str = typer.Option(None, "--prompt", help="Path to a .py file containing OPTIMIZED_SYSTEM_PROMPT"),
) -> None:
    """Run the Repo Explainer Evaluation Harness suite."""
    # Move heavy imports inside main to adhere to fast CLI startup and network rules
    import importlib.util
    from evals.harness import run_evals, print_eval_summary
    from evals.test_cases import TEST_CASES
    from agent.prompts import SYSTEM_PROMPT
    
    try:
        # STEP 1 — Header panel
        header_text = f"[bold blue]🧪 Repo Explainer — Eval Suite[/bold blue]\n\nRunning 8 test cases against: [dim]{repo}[/dim]"
        console.print(Panel(header_text, border_style="blue"))
        
        # STEP 2 — Load prompt
        system_prompt = SYSTEM_PROMPT
        if prompt is not None:
            prompt_path = os.path.abspath(prompt)
            if not os.path.exists(prompt_path):
                console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] Prompt file not found at {prompt}. Falling back to default system prompt.")
            else:
                try:
                    spec = importlib.util.spec_from_file_location("prompts_optimized", prompt_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "OPTIMIZED_SYSTEM_PROMPT"):
                            system_prompt = getattr(module, "OPTIMIZED_SYSTEM_PROMPT")
                            console.print(f"📝 Using optimized prompt from [green]{prompt}[/green]")
                        else:
                            console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] OPTIMIZED_SYSTEM_PROMPT not found in {prompt}. Falling back to default system prompt.")
                    else:
                        console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] Could not load module spec for {prompt}. Falling back to default system prompt.")
                except Exception as e:
                    console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] Failed to dynamically load prompt module: {e}. Falling back to default system prompt.")
        else:
            console.print("📝 Using default system prompt")
            
        # STEP 3 — Run evals
        report = run_evals(
            repo_path=repo,
            test_cases=TEST_CASES,
            system_prompt=system_prompt,
            save_results=save
        )
        
        # STEP 4 — Print summary
        print_eval_summary(report)
        
        # STEP 5 — Exit code
        if report.pass_rate == 1.0:
            sys.exit(0)
        else:
            raise typer.Exit(code=1)
            
    except typer.Exit:
        # Propagate typer exits directly
        raise
    except Exception as e:
        console.print(Panel(f"[bold red]Unexpected error:[/bold red] {e}", title="❌ Error", border_style="red"))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    typer.run(main)
