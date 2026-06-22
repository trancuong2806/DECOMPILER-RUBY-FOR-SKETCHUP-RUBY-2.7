import os
import sys
import subprocess

RUBY_PATH = r"D:\Ruby27-x64\bin\ruby.exe"
TARGET_DIR = r"zsu_vn_signed\zsu_vn"

TEMPLATE = """
require './dumper.so'

module Sketchup
  def self.require(path)
    puts "Sketchup.require #{{path}}"
    real_path = "{target_dir}/" + path.sub("{target_dir_basename}/", "") + ".rb"
    if File.exist?(real_path)
      begin
        require_relative real_path
      rescue LoadError
      end
    end
  end
end

class UI
  def self.menu(*args)
    puts "UI.menu #{{args}}"
    self
  end
  def self.add_item(*args)
    puts "add_item #{{args}}"
  end
end

puts "[*] Dumper loaded. Executing target file..."
begin
    require_relative '{target_path}'
rescue Exception => e
    puts "Error: #{{e.class}} - #{{e.message}}"
end
"""

def decompile_file(file_path):
    print("=" * 60)
    print(f"[+] Processing file: {file_path}")
    print("=" * 60)
    
    # 1. Clean up old dumped_code.txt
    if os.path.exists("dumped_code.txt"):
        try:
            os.remove("dumped_code.txt")
        except Exception as e:
            print(f"[-] Cannot delete dumped_code.txt: {e}")
            
    # 2. Write temp_runner.rb
    # Convert path to forward slashes for Ruby require_relative compatibility
    rel_path = os.path.relpath(file_path, start=".").replace("\\", "/")
    target_dir_fwd = TARGET_DIR.replace("\\", "/")
    target_dir_basename = os.path.basename(TARGET_DIR.rstrip("\\/"))
    runner_code = TEMPLATE.format(target_path=rel_path, target_dir=target_dir_fwd, target_dir_basename=target_dir_basename)
    with open("temp_runner.rb", "w", encoding="utf-8") as f:
        f.write(runner_code)
        
    # 3. Execute Ruby to dump YARV bytecode
    print(f"[*] Running Ruby VM to dump bytecode...")
    try:
        result = subprocess.run(
            [RUBY_PATH, "temp_runner.rb"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode != 0:
            print(f"[-] Ruby runner failed with exit code {result.returncode}")
            print(result.stderr)
    except Exception as e:
        print(f"[-] Failed to execute Ruby: {e}")
        return
        
    # 4. Clean up temp_runner.rb
    if os.path.exists("temp_runner.rb"):
        os.remove("temp_runner.rb")
        
    # 5. Run decompiler module on the dumped bytecode
    if not os.path.exists("dumped_code.txt") or os.path.getsize("dumped_code.txt") == 0:
        print("[-] Error: YARV Bytecode was not dumped (dumped_code.txt is missing or empty).")
        return
        
    print(f"[*] Running decompiler module on dumped bytecode...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "decompiler"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"[-] Decompiler failed:")
            print(result.stderr)
    except Exception as e:
        print(f"[-] Failed to run decompiler module: {e}")

def main():
    if not os.path.exists(RUBY_PATH):
        print(f"[-] Error: Ruby not found at {RUBY_PATH}. Please check the path.")
        return
        
    # Check if a specific file was passed
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.exists(target):
            decompile_file(target)
        else:
            print(f"[-] File not found: {target}")
    else:
        # Autodetect all encrypted files in TARGET_DIR
        print(f"[*] Scanning for encrypted Ruby files in: {TARGET_DIR}")
        targets = []
        for root, dirs, files in os.walk(TARGET_DIR):
            # Skip loader.rb as it is standard and already plain text
            if "rgloader" in root:
                continue
            for file in files:
                if file.endswith(".rb"):
                    targets.append(os.path.join(root, file))
                    
        print(f"[+] Found {len(targets)} files: {', '.join(os.path.basename(t) for t in targets)}")
        for t in targets:
            decompile_file(t)
            
    # Cleanup final dumped_code.txt
    if os.path.exists("dumped_code.txt"):
        try:
            os.remove("dumped_code.txt")
            print("[*] Cleaned up final dumped_code.txt")
        except Exception as e:
            print(f"[-] Cannot delete dumped_code.txt: {e}")
            
    print("\n[+] All decompilation tasks completed.")

if __name__ == "__main__":
    main()
