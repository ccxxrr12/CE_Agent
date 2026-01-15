import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import colorama
from colorama import Fore, Back, Style

from ..models.core_models import AnalysisReport
from ..core.agent import Agent


class CLI:
    """
    Cheat Engine AI Agent 的命令行界面。
    处理用户交互、进度显示和结果展示。
    """
    
    def __init__(self, agent: Optional[Agent] = None):
        """
        使用颜色支持初始化 CLI。
        
        Args:
            agent: 可选的Agent实例
        """
        colorama.init(autoreset=True)
        self.agent = agent
        
    def show_welcome(self):
        """显示欢迎消息和程序信息。"""
        print(Fore.CYAN + Style.BRIGHT + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "CHEAT ENGINE AI AGENT")
        print(Fore.CYAN + Style.BRIGHT + "="*60)
        print(Fore.YELLOW + "Welcome to the CE_Agent")
        print(Fore.CYAN + "Copyright © SherryCHEN All Rights Reserved")
        print(Fore.YELLOW + "此工具支持使用自然语言与 Cheat Engine 进行交互，用于内存分析和逆向工程。")
        print(Fore.YELLOW + "输入 'help' 查看可用命令，或输入 'quit' 退出。")
        print(Fore.CYAN + "-"*60)
        
    def get_user_input(self) -> str:
        """
        从用户获取输入。
        
        Returns:
            str: 用户输入字符串
        """
        try:
            user_input = input(Fore.GREEN + ">>> " + Style.RESET_ALL)
            return user_input.strip()
        except KeyboardInterrupt:
            print("\n" + Fore.YELLOW + "Operation interrupted by user.")
            return "quit"
        except EOFError:
            print("\n" + Fore.YELLOW + "End of input reached.")
            return "quit"
            
    def display_progress(self, step: int, total: int, message: str):
        """
        在执行期间显示进度信息。
        
        Args:
            step: 当前步骤号
            total: 总步骤数
            message: 要显示的进度消息
        """
        progress_bar_length = 40
        percent_complete = step / total if total > 0 else 0
        filled_length = int(progress_bar_length * percent_complete)
        
        bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
        percent_text = f"{percent_complete:.1%}"
        
        # Print progress bar with color
        print(f"\r{Fore.CYAN}[{bar}] {percent_text} ({step}/{total}) {message}", end='', flush=True)
        
        # When we reach the final step, move to next line
        if step == total and total > 0:
            print()  # Move to next line when complete
            
    def display_result(self, report: AnalysisReport):
        """
        Display the final analysis report to the user.
        
        Args:
            report: AnalysisReport containing the results
        """
        print(Fore.GREEN + "\n" + "="*60)
        print(Fore.GREEN + Style.BRIGHT + "分析完成")
        print(Fore.GREEN + "="*60)
        
        print(f"{Fore.WHITE}任务 ID: {report.task_id}")
        print(f"{Fore.WHITE}状态: {Fore.GREEN + '成功' if report.success else Fore.RED + '失败'}")
        print(f"{Fore.WHITE}执行时间: {report.execution_time:.2f} 秒")
        
        if report.summary:
            print(f"\n{Fore.MAGENTA}摘要:")
            print(f"{Fore.WHITE}{report.summary}")
        
        if report.details:
            print(f"\n{Fore.MAGENTA}详细信息:")
            for key, value in report.details.items():
                print(f"{Fore.WHITE}  {key}: {value}")
        
        if report.insights:
            print(f"\n{Fore.MAGENTA}关键发现:")
            for i, insight in enumerate(report.insights, 1):
                print(f"{Fore.WHITE}  {i}. {insight}")
        
        if report.recommendations:
            print(f"\n{Fore.MAGENTA}建议:")
            for i, recommendation in enumerate(report.recommendations, 1):
                print(f"{Fore.WHITE}  {i}. {recommendation}")
        
        if report.error:
            print(f"\n{Fore.RED}错误:")
            print(f"{Fore.RED}{report.error}")
        
        print(Fore.GREEN + "="*60)
        
    def display_error(self, error: str):
        """
        Display error message to the user.
        
        Args:
            error: Error message to display
        """
        print(Fore.RED + Style.BRIGHT + "错误:")
        print(Fore.RED + error)
        
    def display_help(self):
        """Display help information for available commands."""
        print(Fore.CYAN + Style.BRIGHT + "\n可用命令:")
        print(Fore.WHITE + "  help          - 显示此帮助信息")
        print(Fore.WHITE + "  quit/exit     - 退出程序")
        print(Fore.WHITE + "  clear         - 清除屏幕")
        print(Fore.WHITE + "  status        - 显示当前代理状态")
        print(Fore.WHITE + "  [自然语言]   - 输入自然语言请求进行内存分析")
        print("")
        
    def clear_screen(self):
        """Clear the terminal screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def run_interactive_mode(self, agent: Agent):
        """
        Run the CLI in interactive mode allowing continuous user input.
        
        Args:
            agent: Agent实例用于处理请求
        """
        self.show_welcome()
        
        while True:
            user_input = self.get_user_input()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(Fore.YELLOW + "再见！")
                break
            elif user_input.lower() == 'help':
                self.display_help()
            elif user_input.lower() == 'clear':
                self.clear_screen()
                self.show_welcome()
            elif user_input.lower() == 'status':
                self.display_status(agent)
            elif user_input.lower() == '':
                continue
            else:
                # Process natural language request
                print(Fore.YELLOW + f"正在处理请求: '{user_input}'")
                print(Fore.CYAN + "-"*60)
                
                try:
                    # Execute request through agent
                    report = agent.execute(user_input)
                    
                    # Display results
                    self.display_result(report)
                    
                except Exception as e:
                    self.display_error(f"处理请求时出错: {str(e)}")
                
                print(Fore.CYAN + "-"*60)
    
    def display_status(self, agent: Agent):
        """
        Display current agent status.
        
        Args:
            agent: Agent实例
        """
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "代理状态")
        print(Fore.CYAN + "="*60)
        print(f"{Fore.WHITE}状态: {Fore.GREEN + agent.status}")
        print(f"{Fore.WHITE}当前任务: {Fore.YELLOW + agent.active_task if agent.active_task else Fore.WHITE + '无'}")
        print(f"{Fore.WHITE}队列任务数: {Fore.YELLOW + agent.task_queue.qsize()}")
        print(f"{Fore.WHITE}可用工具数: {Fore.YELLOW + len(agent.tool_registry.list_all_tools())}")
        print(Fore.CYAN + "="*60)
    
    def display_step_log(self, step_type: str, message: str, step_num: int = None, total_steps: int = None):
        """
        Display real-time step log during execution.
        
        Args:
            step_type: Type of step (planning, execution, reasoning, decision, etc.)
            message: Step message to display
            step_num: Optional current step number
            total_steps: Optional total number of steps
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Choose color based on step type
        type_colors = {
            'planning': Fore.MAGENTA,
            'execution': Fore.CYAN,
            'reasoning': Fore.YELLOW,
            'decision': Fore.GREEN,
            'error': Fore.RED,
            'success': Fore.GREEN,
            'warning': Fore.YELLOW,
            'info': Fore.WHITE
        }
        
        color = type_colors.get(step_type.lower(), Fore.WHITE)
        type_icon = {
            'planning': '📋',
            'execution': '⚙️',
            'reasoning': '🤔',
            'decision': '✓',
            'error': '✗',
            'success': '✓',
            'warning': '⚠',
            'info': 'ℹ'
        }
        
        icon = type_icon.get(step_type.lower(), '•')
        
        # Build step info
        step_info = f"[{timestamp}] "
        if step_num is not None and total_steps is not None:
            step_info += f"步骤 {step_num}/{total_steps} - "
        
        step_info += f"{icon} {step_type.upper()}: {message}"
        
        print(f"{color}{step_info}{Style.RESET_ALL}")
    
    def display_tool_call(self, tool_name: str, params: dict, status: str = "starting"):
        """
        Display tool call information.
        
        Args:
            tool_name: Name of the tool being called
            params: Parameters passed to the tool
            status: Status of the tool call (starting, success, failed)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if status == "starting":
            color = Fore.CYAN
            icon = "🔧"
            status_text = "调用中..."
        elif status == "success":
            color = Fore.GREEN
            icon = "✓"
            status_text = "成功"
        elif status == "failed":
            color = Fore.RED
            icon = "✗"
            status_text = "失败"
        else:
            color = Fore.WHITE
            icon = "•"
            status_text = status
        
        # Format parameters for display
        if params:
            params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            params_display = f" (参数: {params_str})"
        else:
            params_display = ""
        
        print(f"{color}[{timestamp}] {icon} 工具调用: {tool_name}{params_display} - {status_text}{Style.RESET_ALL}")
    
    def display_llm_call(self, purpose: str, status: str = "starting", duration: float = None):
        """
        Display LLM call information.
        
        Args:
            purpose: Purpose of the LLM call (planning, reasoning, decision)
            status: Status of the LLM call (starting, success, failed)
            duration: Optional duration of the LLM call in seconds
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if status == "starting":
            color = Fore.MAGENTA
            icon = "🧠"
            status_text = "思考中..."
        elif status == "success":
            color = Fore.GREEN
            icon = "✓"
            duration_text = f" ({duration:.2f}s)" if duration else ""
            status_text = f"完成{duration_text}"
        elif status == "failed":
            color = Fore.RED
            icon = "✗"
            status_text = "失败"
        else:
            color = Fore.WHITE
            icon = "•"
            status_text = status
        
        print(f"{color}[{timestamp}] {icon} LLM调用 ({purpose}): {status_text}{Style.RESET_ALL}")
    
    def display_analysis_result(self, findings: list, next_steps: list):
        """
        Display analysis results from reasoning engine.
        
        Args:
            findings: List of findings from analysis
            next_steps: List of recommended next steps
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if findings:
            print(f"{Fore.YELLOW}[{timestamp}] 🔍 分析结果:")
            for i, finding in enumerate(findings, 1):
                print(f"{Fore.WHITE}  {i}. {finding}")
        
        if next_steps:
            print(f"{Fore.CYAN}[{timestamp}] ➡️  下一步:")
            for i, step in enumerate(next_steps, 1):
                print(f"{Fore.WHITE}  {i}. {step}")
                
    def run_batch_mode(self, input_file: str, output_file: Optional[str] = None, agent: Optional[Agent] = None):
        """
        Run the CLI in batch mode processing commands from a file.
        
        Args:
            input_file: Path to input file with commands
            output_file: Optional path to output results file
            agent: Optional Agent instance for processing requests
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                commands = f.readlines()
                
            results = []
            total_commands = len(commands)
            
            for i, command in enumerate(commands, 1):
                command = command.strip()
                if not command or command.startswith('#'):
                    continue
                    
                self.display_progress(i, total_commands, f"Processing: {command[:30]}...")
                
                if agent:
                    try:
                        report = agent.execute(command)
                        result = {
                            'command': command,
                            'status': 'completed',
                            'success': report.success,
                            'task_id': report.task_id,
                            'timestamp': datetime.now().isoformat(),
                            'summary': report.summary
                        }
                    except Exception as e:
                        result = {
                            'command': command,
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    result = {
                        'command': command,
                        'status': 'processed',
                        'timestamp': datetime.now().isoformat()
                    }
                
                results.append(result)
                
            self.display_progress(total_commands, total_commands, "Batch processing completed")
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(Fore.GREEN + f"Results saved to {output_file}")
            else:
                print(Fore.GREEN + f"Processed {len(results)} commands successfully")
                
        except FileNotFoundError:
            self.display_error(f"Input file not found: {input_file}")
        except Exception as e:
            self.display_error(f"Error during batch processing: {str(e)}")


def main():
    """
    Main entry point for CLI (for standalone usage).
    Note: When used through main.py, arguments are handled there.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Cheat Engine AI Agent CLI")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--batch", "-b", type=str, help="Run in batch mode with input file")
    parser.add_argument("--output", "-o", type=str, help="Output file for batch mode results")
    
    args = parser.parse_args()
    
    cli = CLI()
    
    if args.batch:
        cli.run_batch_mode(args.batch, args.output)
    elif args.interactive or len(sys.argv) == 1:
        cli.run_interactive_mode(None)


if __name__ == "__main__":
    main()