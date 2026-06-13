import os
import json
import tempfile
import shutil
import subprocess
import dataclasses
from typing import List, Dict, Tuple, Optional, Any
from dotenv import load_dotenv
import anthropic

from agent.tools import (
    read_file,
    list_directory,
    search_code,
    get_file_tree,
    detect_language_and_framework,
    TOOL_DEFINITIONS
)
from agent.prompts import SYSTEM_PROMPT, build_user_prompt

@dataclasses.dataclass
class AgentResult:
    """The result of the agent exploration loop."""
    answer: str
    tools_used: List[str]
    iterations: int
    success: bool
    error: Optional[str] = None

def resolve_repo_path(repo_input: str) -> Tuple[str, bool]:
    """Resolve local path or clone GitHub repository to a temp directory."""
    if repo_input.startswith("https://github.com") or repo_input.startswith("git@github.com"):
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_input, temp_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return temp_dir, True
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise ValueError(f"Failed to clone GitHub repository: {repo_input}. Error: {e}")
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise ValueError(f"An unexpected error occurred while cloning repository: {repo_input}. Error: {e}")
    else:
        resolved_path = os.path.abspath(repo_input)
        if not os.path.exists(resolved_path):
            raise ValueError(f"Local path does not exist: {repo_input}")
        return resolved_path, False

def execute_tool(tool_name: str, tool_input: Dict[str, Any], repo_path: str) -> str:
    """Routes a tool call from Claude to the correct Python function with sandbox enforcement."""
    try:
        if tool_name == "read_file":
            path_val = tool_input.get("path", "")
            if not path_val.startswith(repo_path):
                # Sandbox enforcement: strip leading slashes and join to repo path
                rel_path = path_val.lstrip('/')
                path_val = os.path.join(repo_path, rel_path)
            return read_file(path_val)
            
        elif tool_name == "list_directory":
            path_val = tool_input.get("path", "")
            if not path_val.startswith(repo_path):
                rel_path = path_val.lstrip('/')
                path_val = os.path.join(repo_path, rel_path)
            return list_directory(path_val)
            
        elif tool_name == "search_code":
            pattern = tool_input.get("pattern", "")
            return search_code(repo_path, pattern)
            
        elif tool_name == "get_file_tree":
            return get_file_tree(repo_path)
            
        elif tool_name == "detect_language_and_framework":
            return detect_language_and_framework(repo_path)
            
        else:
            return f"ERROR: Unknown tool: {tool_name}"
            
    except Exception as e:
        return f"ERROR: {e}"

def run_agent(
    repo_input: str,
    question: str,
    max_iterations: int = 10,
    system_prompt: Optional[str] = None
) -> AgentResult:
    """Executes the main agentic loop to explore a codebase and answer a question."""
    load_dotenv()
    repo_path: Optional[str] = None
    should_cleanup: bool = False
    tools_used: List[str] = []
    iterations: int = 0
    
    try:
        # Phase 1: Setup and path resolution
        repo_path, should_cleanup = resolve_repo_path(repo_input)
        client = anthropic.Anthropic()
        
        # Determine prompt and construct the first user message
        sys_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
        user_message = build_user_prompt(repo_path, question)
        messages = [{"role": "user", "content": user_message}]
        
        # Phase 2: Agentic loop
        while iterations < max_iterations:
            iterations += 1
            
            # Make API request to Claude
            response = client.messages.create(
                model="anthropic/claude-3.5-haiku",
                max_tokens=4096,
                system=sys_prompt,
                tools=TOOL_DEFINITIONS,
                messages=messages
            )
            
            # Record Claude's response in history
            messages.append({"role": "assistant", "content": response.content})
            
            # Stop Condition: Claude finished turn and returned text answer
            if response.stop_reason == "end_turn":
                answer_text = ""
                for block in response.content:
                    if getattr(block, 'type', None) == "text":
                        answer_text += block.text
                return AgentResult(
                    answer=answer_text,
                    tools_used=tools_used,
                    iterations=iterations,
                    success=True,
                    error=None
                )
            
            # Tool use request: Execute requested tools and append outcomes
            elif response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if getattr(block, 'type', None) == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id
                        
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
                            
                        result_str = execute_tool(tool_name, tool_input, repo_path)
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result_str
                        })
                
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                continue
                
            else:
                # Handle unexpected stop reasons
                break
        
        # If loop exited without returning an answer
        return AgentResult(
            answer="Max iterations reached without a final answer.",
            tools_used=tools_used,
            iterations=iterations,
            success=False,
            error="max_iterations_exceeded"
        )
        
    except Exception as e:
        return AgentResult(
            answer="",
            tools_used=tools_used,
            iterations=iterations,
            success=False,
            error=str(e)
        )
        
    finally:
        # Guarantee cleanup of temporary directory in all scenarios
        if should_cleanup and repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception:
                pass
