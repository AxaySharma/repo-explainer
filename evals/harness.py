import sys
import os

# Insert project root into sys.path to enable imports of agent/eval modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import datetime
import dataclasses
from typing import List, Dict, Tuple, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evals.test_cases import TestCase, TEST_CASES
from evals.metrics import (
    score_topic_coverage,
    score_hallucination_penalty,
    score_answer_length,
    score_groundedness,
    compute_overall_score,
    get_missing_topics
)
from agent.repo_explainer import run_agent, AgentResult

# Initialize rich Console
console = Console()

@dataclasses.dataclass
class EvalResult:
    """Represents the evaluation outcome of a single test case."""
    test_id: str
    question: str
    answer: str
    scores: Dict[str, float]  # Keys: topic, hallucination, length, groundedness, overall
    overall_score: float
    tools_used: List[str]
    iterations: int
    passed: bool
    error: Optional[str] = None

@dataclasses.dataclass
class EvalReport:
    """Summary report across all test cases run in an evaluation session."""
    results: List[EvalResult]
    pass_rate: float
    average_score: float
    metric_averages: Dict[str, float]
    total_tests: int
    passed_tests: int
    timestamp: str  # ISO format

def run_single_eval(
    test_case: TestCase,
    repo_path: str,
    system_prompt: Optional[str] = None
) -> EvalResult:
    """Executes a single test case evaluation against the agent."""
    try:
        result = run_agent(
            repo_input=repo_path,
            question=test_case.question,
            max_iterations=10,
            system_prompt=system_prompt
        )
        
        if not result.success:
            zero_scores = {
                "topic": 0.0,
                "hallucination": 0.0,
                "length": 0.0,
                "groundedness": 0.0,
                "overall": 0.0
            }
            return EvalResult(
                test_id=test_case.id,
                question=test_case.question,
                answer="",
                scores=zero_scores,
                overall_score=0.0,
                tools_used=result.tools_used,
                iterations=result.iterations,
                passed=False,
                error=result.error
            )
            
        # Calculate individual metric scores
        t_score = score_topic_coverage(result.answer, test_case.expected_topics)
        h_score = score_hallucination_penalty(result.answer, test_case.must_not_contain)
        l_score = score_answer_length(result.answer, test_case.min_words, test_case.max_words)
        g_score = score_groundedness(result.answer, result.tools_used)
        o_score = compute_overall_score(t_score, h_score, l_score, g_score)
        
        scores_dict = {
            "topic": t_score,
            "hallucination": h_score,
            "length": l_score,
            "groundedness": g_score,
            "overall": o_score
        }
        
        return EvalResult(
            test_id=test_case.id,
            question=test_case.question,
            answer=result.answer,
            scores=scores_dict,
            overall_score=o_score,
            tools_used=result.tools_used,
            iterations=result.iterations,
            passed=(o_score >= 0.6),
            error=None
        )
        
    except Exception as e:
        zero_scores = {
            "topic": 0.0,
            "hallucination": 0.0,
            "length": 0.0,
            "groundedness": 0.0,
            "overall": 0.0
        }
        return EvalResult(
            test_id=test_case.id,
            question=test_case.question,
            answer="",
            scores=zero_scores,
            overall_score=0.0,
            tools_used=[],
            iterations=0,
            passed=False,
            error=str(e)
        )

def run_evals(
    repo_path: str,
    test_cases: Optional[List[TestCase]] = None,
    system_prompt: Optional[str] = None,
    save_results: bool = True
) -> EvalReport:
    """Runs the full evaluation test suite and compiles the final report."""
    if test_cases is None:
        test_cases = TEST_CASES
        
    # Print header panel
    console.print(Panel(
        f"[bold green]🧪 Running Eval Harness[/bold green]\n\n[bold]{len(test_cases)}[/bold] test cases against [dim]{repo_path}[/dim]",
        border_style="green"
    ))
    
    results = []
    passed_count = 0
    
    for case in test_cases:
        console.print(f"  Running: [cyan]{case.id}[/cyan]...", end="")
        
        # Call run_single_eval
        res = run_single_eval(case, repo_path, system_prompt)
        results.append(res)
        
        # Print inline result
        if res.passed:
            passed_count += 1
            console.print(f" [bold green]✅ PASS[/bold green] (score: {res.overall_score:.4f})")
        else:
            console.print(f" [bold red]❌ FAIL[/bold red] (score: {res.overall_score:.4f})")
            
    # Compute aggregates
    total_tests = len(test_cases)
    pass_rate = passed_count / total_tests if total_tests > 0 else 0.0
    average_score = sum(r.overall_score for r in results) / total_tests if total_tests > 0 else 0.0
    
    # Calculate metric averages
    metric_averages = {
        "topic": 0.0,
        "hallucination": 0.0,
        "length": 0.0,
        "groundedness": 0.0
    }
    if total_tests > 0:
        metric_averages["topic"] = sum(r.scores["topic"] for r in results) / total_tests
        metric_averages["hallucination"] = sum(r.scores["hallucination"] for r in results) / total_tests
        metric_averages["length"] = sum(r.scores["length"] for r in results) / total_tests
        metric_averages["groundedness"] = sum(r.scores["groundedness"] for r in results) / total_tests
        
    # Render detailed results table
    table = Table(title="📊 Detailed Evaluation Results", show_header=True, header_style="bold magenta")
    table.add_column("Test ID", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Topic", justify="right")
    table.add_column("Halluc", justify="right")
    table.add_column("Length", justify="right")
    table.add_column("Ground", justify="right")
    table.add_column("Pass?", justify="center")
    
    for r in results:
        row_style = "green" if r.passed else "red"
        pass_str = "✅" if r.passed else "❌"
        table.add_row(
            r.test_id,
            f"{r.overall_score:.4f}",
            f"{r.scores['topic']:.4f}",
            f"{r.scores['hallucination']:.4f}",
            f"{r.scores['length']:.4f}",
            f"{r.scores['groundedness']:.4f}",
            pass_str,
            style=row_style
        )
        
    # Add bottom summary row
    table.add_section()
    table.add_row(
        "Averages / Pass Rate",
        f"[bold]{average_score:.4f}[/bold]",
        f"{metric_averages['topic']:.4f}",
        f"{metric_averages['hallucination']:.4f}",
        f"{metric_averages['length']:.4f}",
        f"{metric_averages['groundedness']:.4f}",
        f"[bold]{pass_rate * 100:.1f}%[/bold]"
    )
    
    console.print(table)
    
    # Compile report dataclass
    iso_timestamp = datetime.datetime.utcnow().isoformat()
    report = EvalReport(
        results=results,
        pass_rate=pass_rate,
        average_score=average_score,
        metric_averages=metric_averages,
        total_tests=total_tests,
        passed_tests=passed_count,
        timestamp=iso_timestamp
    )
    
    # Save output report as JSON
    if save_results:
        os.makedirs("optimizer/results", exist_ok=True)
        fn_timestamp = iso_timestamp.replace(":", "-")
        report_path = f"optimizer/results/eval_{fn_timestamp}.json"
        
        # Serialize report object including child dataclasses
        report_dict = dataclasses.asdict(report)
        try:
            with open(report_path, "w") as f:
                json.dump(report_dict, f, indent=2)
            console.print(f"💾 Results saved to [green]{report_path}[/green]")
        except Exception as e:
            console.print(f"[bold red]Failed to save results:[/bold red] {e}")
            
    return report

def print_eval_summary(report: EvalReport) -> None:
    """Print a clean summary panel of the evaluation report details."""
    best_test = None
    worst_test = None
    
    if report.results:
        sorted_res = sorted(report.results, key=lambda r: r.overall_score)
        worst_test = sorted_res[0]
        best_test = sorted_res[-1]
        
    best_str = f"{best_test.test_id} ({best_test.overall_score:.4f})" if best_test else "N/A"
    worst_str = f"{worst_test.test_id} ({worst_test.overall_score:.4f})" if worst_test else "N/A"
    
    summary_text = (
        f"[bold]Total passed:[/bold] {report.passed_tests} / {report.total_tests}\n"
        f"[bold]Average Score:[/bold] {report.average_score:.4f}\n"
        f"[bold]Best test:[/bold] {best_str}\n"
        f"[bold]Worst test:[/bold] {worst_str}"
    )
    
    console.print(Panel(summary_text, title="📊 Evaluation Summary", border_style="cyan"))
