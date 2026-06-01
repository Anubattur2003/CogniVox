"""
Cross-platform terminal launcher for services
"""

import os
import platform
import subprocess
import tempfile
from typing import List, Tuple, Optional

# Rich imports for console output
try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback to basic console
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

# Create console instance
console = Console()


class TerminalLauncher:
    """Cross-platform terminal launcher for services"""
    
    @staticmethod
    def detect_platform_and_shell():
        """Detect the current platform and shell"""
        system = platform.system().lower()
        shell_info = {
            "system": system,
            "shell": "unknown",
            "command_template": None
        }
        
        if system == "windows":
            # Check if running in PowerShell or CMD
            parent_process = os.environ.get("PSModulePath")
            if parent_process:
                shell_info["shell"] = "powershell"
                shell_info["command_template"] = "powershell"
            else:
                shell_info["shell"] = "cmd"
                shell_info["command_template"] = "cmd"
        elif system == "linux":
            shell_info["shell"] = "bash"
            shell_info["command_template"] = "gnome-terminal"
        elif system == "darwin":  # macOS
            shell_info["shell"] = "zsh"
            shell_info["command_template"] = "osascript"
            
        return shell_info
    
    @staticmethod
    def launch_service_in_terminal(service_name: str, service_dir: str, run_command: List[str], 
                                 working_dir: str = None) -> Tuple[subprocess.Popen, Optional[str]]:
        """Launch a service in a separate terminal window"""
        shell_info = TerminalLauncher.detect_platform_and_shell()
        system = shell_info["system"]
        
        if working_dir is None:
            working_dir = os.getcwd()
            
        # Prepare the command to run in the new terminal
        if system == "windows":
            return TerminalLauncher._launch_windows_terminal(
                service_name, service_dir, run_command, working_dir, shell_info["shell"]
            )
        elif system == "linux":
            process = TerminalLauncher._launch_linux_terminal(
                service_name, service_dir, run_command, working_dir
            )
            return process, None  # Linux doesn't use temp files
        elif system == "darwin":
            process = TerminalLauncher._launch_macos_terminal(
                service_name, service_dir, run_command, working_dir
            )
            return process, None  # macOS doesn't use temp files
        else:
            raise OSError(f"Unsupported platform: {system}")
    
    @staticmethod
    def _launch_windows_terminal(service_name: str, service_dir: str, run_command: List[str], 
                               working_dir: str, shell_type: str) -> Tuple[subprocess.Popen, Optional[str]]:
        """Launch service in Windows terminal"""
        
        # Change to service directory and run command
        if shell_type == "powershell":
            # PowerShell command with proper quoting and environment activation
            service_path = os.path.join(working_dir, service_dir)
            
            # Create a temporary PowerShell script to avoid complex quoting issues
            script_content = []
            
            # Set console encoding for Unicode support
            script_content.append("$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding")
            script_content.append("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8")
            
            # Set working directory
            script_content.append(f"Set-Location '{service_path}'")
            
            # Set window title
            script_content.append(f"$Host.UI.RawUI.WindowTitle = '{service_name}'")
            
            script_content.append(f"Write-Host 'Starting {service_name}...' -ForegroundColor Cyan")
            script_content.append(f"Write-Host 'Service Directory: {service_path}' -ForegroundColor Gray")
            
            # Check if this is a Node.js service (frontend)
            if run_command[0] in ["npm", "node", "yarn", "pnpm"]:
                # Node.js service handling
                script_content.append("Write-Host 'Node.js service detected' -ForegroundColor Green")
                
                # Check Node.js availability
                script_content.append("if ($null -eq (Get-Command node -ErrorAction SilentlyContinue)) {")
                script_content.append("    Write-Host 'Node.js not found! Please install Node.js' -ForegroundColor Red")
                script_content.append("    Read-Host 'Press Enter to exit'")
                script_content.append("    exit 1")
                script_content.append("}")
                
                # Check npm availability
                script_content.append("if ($null -eq (Get-Command npm -ErrorAction SilentlyContinue)) {")
                script_content.append("    Write-Host 'npm not found! Please install npm' -ForegroundColor Red")
                script_content.append("    Read-Host 'Press Enter to exit'")
                script_content.append("    exit 1")
                script_content.append("}")
                
                # Check if node_modules exists
                script_content.append("if (-not (Test-Path 'node_modules')) {")
                script_content.append("    Write-Host 'node_modules not found! Please run: npm install' -ForegroundColor Red")
                script_content.append("    Read-Host 'Press Enter to exit'")
                script_content.append("    exit 1")
                script_content.append("}")
                
                # Run the npm command
                run_cmd = " ".join(run_command)
                script_content.append(f"Write-Host 'Running command: {run_cmd}' -ForegroundColor Cyan")
                script_content.append(f"{run_cmd}")
                
            else:
                # Python service handling
                venv_path = os.path.join(service_path, ".venv")
                venv_scripts_path = os.path.join(venv_path, "Scripts")
                activate_script = os.path.join(venv_scripts_path, "Activate.ps1")
                python_exe = os.path.join(venv_scripts_path, "python.exe")
                
                if os.path.exists(venv_path):
                    script_content.append(f"Write-Host 'Virtual environment found at: {venv_path}' -ForegroundColor Green")
                    
                    if os.path.exists(activate_script):
                        script_content.append(f"Write-Host 'Activating virtual environment...' -ForegroundColor Yellow")
                        # Use proper PowerShell activation with error handling
                        script_content.append("try {")
                        script_content.append(f"    & '{activate_script}'")
                        script_content.append("    if ($LASTEXITCODE -eq 0) {")
                        script_content.append("        Write-Host 'Virtual environment activated successfully!' -ForegroundColor Green")
                        script_content.append("    } else {")
                        script_content.append("        Write-Host 'Activation script returned non-zero exit code, trying alternative method...' -ForegroundColor Yellow")
                        script_content.append(f"        $env:PATH = '{venv_scripts_path};' + $env:PATH")
                        script_content.append("        Write-Host 'PATH updated to use virtual environment Python' -ForegroundColor Green")
                        script_content.append("    }")
                        script_content.append("} catch {")
                        script_content.append("    Write-Host 'Activation script failed, using direct Python path...' -ForegroundColor Yellow")
                        script_content.append(f"    $env:PATH = '{venv_scripts_path};' + $env:PATH")
                        script_content.append("    Write-Host 'PATH updated to use virtual environment Python' -ForegroundColor Green")
                        script_content.append("}")
                        
                        # Use UV if available, otherwise use python from activated environment  
                        uv_available = "$null -ne (Get-Command uv -ErrorAction SilentlyContinue)"
                        script_content.append(f"if ({uv_available}) {{")
                        script_content.append(f"    Write-Host 'Using UV package manager...' -ForegroundColor Green")
                        uv_cmd = f"uv run {' '.join(run_command)}"
                        script_content.append(f"    Write-Host 'Running command: {uv_cmd}' -ForegroundColor Cyan")
                        script_content.append(f"    & {uv_cmd}")
                        script_content.append("} else {")
                        run_cmd = " ".join(run_command)
                        script_content.append(f"    Write-Host 'Running command: {run_cmd}' -ForegroundColor Cyan")
                        script_content.append(f"    & {run_cmd}")
                        script_content.append("}")
                    elif os.path.exists(python_exe):
                        script_content.append(f"Write-Host 'Using Python from virtual environment: {python_exe}' -ForegroundColor Yellow")
                        # Use UV if available, otherwise use python executable directly from venv
                        uv_available = "$null -ne (Get-Command uv -ErrorAction SilentlyContinue)"
                        script_content.append(f"if ({uv_available}) {{")
                        script_content.append(f"    Write-Host 'Using UV package manager...' -ForegroundColor Green")
                        uv_cmd = f"uv run {' '.join(run_command)}"
                        script_content.append(f"    Write-Host 'Running command: {uv_cmd}' -ForegroundColor Cyan")
                        script_content.append(f"    & {uv_cmd}")
                        script_content.append("} else {")
                        modified_command = [f'"{python_exe}"'] + run_command[1:]
                        run_cmd = " ".join(modified_command)
                        script_content.append(f"    Write-Host 'Running command: {run_cmd}' -ForegroundColor Cyan")
                        script_content.append(f"    & {run_cmd}")
                        script_content.append("}")
                    else:
                        script_content.append("Write-Host 'Virtual environment found but no activation script or python.exe!' -ForegroundColor Red")
                        script_content.append("Write-Host 'Please run: uv sync or python setup.py to configure the environment properly.' -ForegroundColor Yellow")
                        # Try UV first, then fallback to system Python
                        uv_available = "$null -ne (Get-Command uv -ErrorAction SilentlyContinue)"
                        script_content.append(f"if ({uv_available}) {{")
                        script_content.append(f"    Write-Host 'Trying with UV package manager...' -ForegroundColor Yellow")
                        uv_cmd = f"uv run {' '.join(run_command)}"
                        script_content.append(f"    Write-Host 'Running command: {uv_cmd}' -ForegroundColor Cyan")
                        script_content.append(f"    & {uv_cmd}")
                        script_content.append("} else {")
                        run_cmd = " ".join(run_command)
                        script_content.append(f"    Write-Host 'Trying with system Python: {run_cmd}' -ForegroundColor Yellow")
                        script_content.append(f"    & {run_cmd}")
                        script_content.append("}")
                else:
                    script_content.append(f"Write-Host 'No virtual environment found at: {venv_path}' -ForegroundColor Red")
                    script_content.append("Write-Host 'Please run: uv venv or python setup.py to create the virtual environment.' -ForegroundColor Yellow")
                    # Try UV first, then fallback to system Python
                    uv_available = "$null -ne (Get-Command uv -ErrorAction SilentlyContinue)"
                    script_content.append(f"if ({uv_available}) {{")
                    script_content.append(f"    Write-Host 'Trying with UV package manager...' -ForegroundColor Yellow")
                    uv_cmd = f"uv run {' '.join(run_command)}"
                    script_content.append(f"    Write-Host 'Running command: {uv_cmd}' -ForegroundColor Cyan")
                    script_content.append(f"    & {uv_cmd}")
                    script_content.append("} else {")
                    run_cmd = " ".join(run_command)
                    script_content.append(f"    Write-Host 'Trying with system Python: {run_cmd}' -ForegroundColor Yellow")
                    script_content.append(f"    & {run_cmd}")
                    script_content.append("}")
            
            # Keep terminal open on exit
            script_content.append("")
            script_content.append("if ($LASTEXITCODE -ne 0) {")
            script_content.append("    Write-Host 'Service exited with errors. Press any key to close...' -ForegroundColor Red")
            script_content.append("    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')")
            script_content.append("}")
            
            # Create temporary script file
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as script_file:
                    script_file.write('\n'.join(script_content))
                    script_file_path = script_file.name
                
                # Launch PowerShell with the temporary script
                cmd = [
                    "powershell", "-Command",
                    f"Start-Process powershell -ArgumentList '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', '{script_file_path}'"
                ]
                
                console.print(f"[blue]Launching {service_name} in new terminal...[/blue]")
                console.print(f"[dim]Script: {script_file_path}[/dim]")
                
                # For Node.js services, don't print venv path
                if run_command[0] not in ["npm", "node", "yarn", "pnpm"]:
                    venv_path = os.path.join(service_path, ".venv")
                    console.print(f"[dim]Virtual Environment: {venv_path}[/dim]")
                else:
                    console.print(f"[dim]Node.js Service - No Virtual Environment Needed[/dim]")
                
                # Launch the process and return both process and temp file path
                process = subprocess.Popen(cmd, shell=True)
                return process, script_file_path
                
            except Exception as e:
                console.print(f"❌ Failed to create temporary script: {e}", style="red")
                # Fallback to simple command
                if run_command[0] in ["npm", "node", "yarn", "pnpm"]:
                    # Node.js fallback
                    run_cmd_str = " ".join(run_command)
                    cmd = [
                        "powershell", "-Command",
                        f"Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd \"{service_path}\"; {run_cmd_str}'"
                    ]
                else:
                    # Python fallback
                    cmd = [
                        "powershell", "-Command",
                        f"Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd \"{service_path}\"; python {run_command[1]}'"
                    ]
                
                console.print(f"[blue]Launching {service_name} in new terminal (fallback)...[/blue]")
                console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")
                
                process = subprocess.Popen(cmd, shell=True)
                return process, None
        else:
            # CMD command with proper quoting and UV environment activation
            service_path = os.path.join(working_dir, service_dir)
            
            # Check if UV virtual environment exists
            venv_path = os.path.join(service_path, ".venv")
            if os.path.exists(venv_path):
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                if os.path.exists(python_exe):
                    run_command[0] = f'"{python_exe}"'
            
            command_str = ' '.join(run_command)
            
            cmd = [
                "start", f'"{service_name}"',  # Properly quote the title
                "cmd", "/k", 
                f'cd /d "{service_path}" && echo Starting {service_name}... && echo Virtual Environment: {venv_path} && {command_str}'
            ]
            
            console.print(f"[blue]Launching {service_name} in CMD terminal...[/blue]")
            console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")
            
            process = subprocess.Popen(cmd, shell=True)
            return process, None  # CMD doesn't use temp files
    
    @staticmethod
    def _launch_linux_terminal(service_name: str, service_dir: str, run_command: List[str], 
                             working_dir: str) -> subprocess.Popen:
        """Launch service in Linux terminal"""
        
        full_service_dir = os.path.join(working_dir, service_dir)
        
        # Check if UV virtual environment exists
        venv_path = os.path.join(full_service_dir, ".venv")
        if os.path.exists(venv_path):
            # Activate UV environment and run command
            activate_script = os.path.join(venv_path, "bin", "activate")
            if os.path.exists(activate_script):
                command_str = f"source {activate_script} && {' '.join(run_command)}"
            else:
                # Fallback to python from venv
                python_exe = os.path.join(venv_path, "bin", "python")
                if os.path.exists(python_exe):
                    run_command[0] = python_exe
                    command_str = ' '.join(run_command)
                else:
                    command_str = ' '.join(run_command)
        else:
            command_str = ' '.join(run_command)
        
        # Try different terminal emulators
        terminals = [
            ["gnome-terminal", "--title", service_name, "--working-directory", full_service_dir, "--", "bash", "-c", f"{command_str}; exec bash"],
            ["xterm", "-title", service_name, "-e", f"cd {full_service_dir} && {command_str}"],
            ["konsole", "--title", service_name, "--workdir", full_service_dir, "-e", "bash", "-c", f"{command_str}; exec bash"]
        ]
        
        for term_cmd in terminals:
            try:
                console.print(f"[blue]Launching {service_name} in {term_cmd[0]}...[/blue]")
                return subprocess.Popen(term_cmd)
            except FileNotFoundError:
                continue
        
        raise OSError("No suitable terminal emulator found")
    
    @staticmethod
    def _launch_macos_terminal(service_name: str, service_dir: str, run_command: List[str], 
                             working_dir: str) -> subprocess.Popen:
        """Launch service in macOS terminal"""
        
        full_service_dir = os.path.join(working_dir, service_dir)
        
        # Check if UV virtual environment exists
        venv_path = os.path.join(full_service_dir, ".venv")
        if os.path.exists(venv_path):
            # Activate UV environment and run command
            activate_script = os.path.join(venv_path, "bin", "activate")
            if os.path.exists(activate_script):
                command_str = f"source {activate_script} && {' '.join(run_command)}"
            else:
                # Fallback to python from venv
                python_exe = os.path.join(venv_path, "bin", "python")
                if os.path.exists(python_exe):
                    run_command[0] = python_exe
                    command_str = ' '.join(run_command)
                else:
                    command_str = ' '.join(run_command)
        else:
            command_str = ' '.join(run_command)
        
        # AppleScript to open new Terminal window
        applescript = f'''\n        tell application "Terminal"\n            activate\n            set newTab to do script "cd {full_service_dir} && {command_str}"\n            set title of newTab to "{service_name}"\n        end tell\n        '''
        
        cmd = ["osascript", "-e", applescript]
        console.print(f"[blue]Launching {service_name} in new Terminal window...[/blue]")
        
        return subprocess.Popen(cmd) 