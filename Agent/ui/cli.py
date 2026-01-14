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
        print(Fore.CYAN + Style.BRIGHT + "    CHEAT ENGINE AI AGENT")
        print(Fore.CYAN + Style.BRIGHT + "="*60)
        print(Fore.YELLOW + "Welcome to the Cheat Engine AI Agent!")
        print(Fore.YELLOW + "This tool enables natural language interaction with Cheat Engine for memory analysis and reverse engineering.")
        print(Fore.YELLOW + "Type 'help' for available commands or 'quit' to exit.")
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
        print(Fore.GREEN + Style.BRIGHT + "ANALYSIS COMPLETED")
        print(Fore.GREEN + "="*60)
        
        print(f"{Fore.WHITE}Task ID: {report.task_id}")
        print(f"{Fore.WHITE}Status: {Fore.GREEN + 'SUCCESS' if report.success else Fore.RED + 'FAILED'}")
        print(f"{Fore.WHITE}Execution Time: {report.execution_time:.2f} seconds")
        
        if report.summary:
            print(f"\n{Fore.MAGENTA}Summary:")
            print(f"{Fore.WHITE}{report.summary}")
        
        if report.details:
            print(f"\n{Fore.MAGENTA}Details:")
            for key, value in report.details.items():
                print(f"{Fore.WHITE}  {key}: {value}")
        
        if report.insights:
            print(f"\n{Fore.MAGENTA}Key Insights:")
            for i, insight in enumerate(report.insights, 1):
                print(f"{Fore.WHITE}  {i}. {insight}")
        
        if report.recommendations:
            print(f"\n{Fore.MAGENTA}Recommendations:")
            for i, recommendation in enumerate(report.recommendations, 1):
                print(f"{Fore.WHITE}  {i}. {recommendation}")
        
        if report.error:
            print(f"\n{Fore.RED}Error:")
            print(f"{Fore.RED}{report.error}")
        
        print(Fore.GREEN + "="*60)
        
    def display_error(self, error: str):
        """
        Display error message to the user.
        
        Args:
            error: Error message to display
        """
        print(Fore.RED + Style.BRIGHT + "ERROR:")
        print(Fore.RED + error)
        
    def display_help(self):
        """Display help information for available commands."""
        print(Fore.CYAN + Style.BRIGHT + "\nAVAILABLE COMMANDS:")
        print(Fore.WHITE + "  help          - Show this help message")
        print(Fore.WHITE + "  quit/exit     - Exit the program")
        print(Fore.WHITE + "  clear         - Clear the screen")
        print(Fore.WHITE + "  status        - Show current agent status")
        print(Fore.WHITE + "  [natural lang] - Enter natural language requests for memory analysis")
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
                print(Fore.YELLOW + "Goodbye!")
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
                print(Fore.YELLOW + f"Processing request: '{user_input}'")
                print(Fore.CYAN + "-"*60)
                
                try:
                    # Execute request through agent
                    report = agent.execute(user_input)
                    
                    # Display results
                    self.display_result(report)
                    
                except Exception as e:
                    self.display_error(f"Error processing request: {str(e)}")
                
                print(Fore.CYAN + "-"*60)
    
    def display_status(self, agent: Agent):
        """
        Display current agent status.
        
        Args:
            agent: Agent实例
        """
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "AGENT STATUS")
        print(Fore.CYAN + "="*60)
        print(f"{Fore.WHITE}Status: {Fore.GREEN + agent.status}")
        print(f"{Fore.WHITE}Active Task: {Fore.YELLOW + agent.active_task if agent.active_task else Fore.WHITE + 'None'}")
        print(f"{Fore.WHITE}Queued Tasks: {Fore.YELLOW + agent.task_queue.qsize()}")
        print(f"{Fore.WHITE}Available Tools: {Fore.YELLOW + len(agent.tool_registry.list_all_tools())}")
        print(Fore.CYAN + "="*60)
                
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