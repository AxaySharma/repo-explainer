import sys
import os

# Insert project root into sys.path to enable imports of agent/eval modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize Console
console = Console()

def main(
    repo: str = typer.Option("evals/fixtures/sample_project", "--repo", help="Path to repo to run evals against"),
    iterations: int = typer.Option(5, "--iterations", help="Number of optimization iterations"),
    dry_run: bool = typer.Option(False, "--dry-run/--no-dry-run", help="If set, only run baseline eval, skip optimization"),
) -> None:
    """Run the Prompt Optimizer loop to improve the system prompt."""
    # Move heavy imports inside main to adhere to fast CLI startup and network rules
    from evals.harness import run_evals, print_eval_summary
    from evals.test_cases import TEST_CASES
    from optimizer.optimizer import PromptOptimizer
    
    try:
        # STEP 1 — Header panel
        mode_str = "Dry Run (baseline only)" if dry_run else "Full Optimization"
        header_text = (
            f"[bold yellow]⚡ Repo Explainer — Prompt Optimizer[/bold yellow]\n\n"
            f"[bold]Repo:[/bold]       [dim]{repo}[/dim]\n"
            f"[bold]Iterations:[/bold] {iterations}\n"
            f"[bold]Mode:[/bold]       {mode_str}"
        )
        console.print(Panel(header_text, border_style="yellow"))
        
        # STEP 2 — Dry run mode
        if dry_run:
            console.print("Running baseline eval only...")
            report = run_evals(
                repo_path=repo,
                test_cases=TEST_CASES,
                system_prompt=None,
                save_results=True
            )
            print_eval_summary(report)
            console.print(Panel("Dry run complete. Run without --dry-run to optimize.", border_style="blue"))
            return
            
        # STEP 3 — Confirmation prompt (only in full mode)
        warning_text = (
            "[bold yellow]⚠️  This will make multiple API calls to Claude.[/bold yellow]\n\n"
            "Estimated cost: very low (Haiku model used throughout)\n"
            "Results will be saved to [cyan]optimizer/results/[/cyan]"
        )
        console.print(Panel(warning_text, border_style="yellow"))
        
        confirmed = typer.confirm("Continue?")
        if not confirmed:
            console.print("Aborted.")
            return
            
        # STEP 4 — Run optimizer
        optimizer = PromptOptimizer(repo_path=repo, n_iterations=iterations)
        report = optimizer.run()
        
        # STEP 5 — Print final comparison table
        table = Table(title="📊 Optimization Results", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Baseline", justify="right", width=15)
        table.add_column("Final", justify="right", width=15)
        table.add_column("Change", justify="right", width=15)
        
        # Format Change values
        delta_score = report.final_score - report.baseline_score
        if delta_score > 0:
            change_score_str = f"[green]+{delta_score:.3f}[/green]"
        elif delta_score < 0:
            change_score_str = f"[red]{delta_score:.3f}[/red]"
        else:
            change_score_str = "0.000"
            
        delta_pass = report.final_pass_rate - report.baseline_pass_rate
        if delta_pass > 0:
            change_pass_str = f"[green]+{delta_pass:.0%}[/green]"
        elif delta_pass < 0:
            change_pass_str = f"[red]{delta_pass:.0%}[/red]"
        else:
            change_pass_str = "0%"
            
        table.add_row(
            "Average Score",
            f"{report.baseline_score:.3f}",
            f"{report.final_score:.3f}",
            change_score_str
        )
        table.add_row(
            "Pass Rate",
            f"{report.baseline_pass_rate:.0%}",
            f"{report.final_pass_rate:.0%}",
            change_pass_str
        )
        table.add_row(
            "Iterations Run",
            "—",
            "—",
            str(report.iterations_run)
        )
        
        console.print(table)
        
        # STEP 6 — Next steps panel
        next_steps_text = (
            "Best prompt saved to: [cyan]agent/prompts_optimized.py[/cyan]\n\n"
            "To use it: [bold green]python scripts/run_agent.py --repo . --question 'How does this work?'[/bold green]\n"
            "          (the agent will automatically use the optimized prompt)"
        )
        console.print(Panel(next_steps_text, title="🚀 Next Steps", border_style="green"))
        
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted by user.[/bold red]")
        sys.exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(Panel(f"[bold red]Unexpected error:[/bold red] {e}", title="❌ Error", border_style="red"))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    typer.run(main)
