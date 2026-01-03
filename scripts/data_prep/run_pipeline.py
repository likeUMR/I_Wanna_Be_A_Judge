import subprocess
import os
import sys

# ================= 配置区 =================
# 数据处理流水线步骤列表
# 如果需要跳过某个步骤，直接注释掉即可
STEPS = [
    # "stage1_raw_zip_processor.py",
    # "stage2_legal_info_extractor.py",
    "stage3_group_by_adcode.py",
    "stage4_filter_complete_cases.py",
]

# stage4 每个 AdCode 文件保留的最大行数 (设为 None 则不限制)
STAGE4_LIMIT = 100
# ==========================================

def run_script(script_name):
    """
    运行指定的 Python 脚本
    """
    print(f"\n{'='*30}")
    print(f"正在执行步骤: {script_name}")
    print(f"{'='*30}\n")
    
    try:
        # 构造命令
        cmd = [sys.executable, script_name]
        
        # 如果是第4步且设置了限制个数，则增加参数
        if script_name == "stage4_filter_complete_cases.py" and STAGE4_LIMIT is not None:
            cmd.extend(["--limit", str(STAGE4_LIMIT)])
            print(f"检测到 stage4，已添加限制参数: --limit {STAGE4_LIMIT}")

        # 使用 sys.executable 获取当前运行的 Python 解释器路径
        subprocess.run(cmd, check=True)
        print(f"\n[成功] {script_name} 执行完毕。")
    except subprocess.CalledProcessError as e:
        print(f"\n[错误] 执行 {script_name} 时返回非零退出代码: {e.returncode}")
        # 数据处理通常具有依赖性，如果前一步失败，则停止后续步骤
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[错误] 找不到脚本文件: {script_name}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] 运行脚本 {script_name} 时发生未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 切换工作目录到脚本所在文件夹，确保相对路径引用正确
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)

    print(">>> 开始运行数据处理完整流水线 <<<")
    if STAGE4_LIMIT:
        print(f"配置信息: stage4 限制行数 = {STAGE4_LIMIT}")
    print(f"待处理步骤: {', '.join(STEPS)}")
    
    for step in STEPS:
        run_script(step)
        
    print("\n>>> 所有配置的步骤均已顺利执行完毕！ <<<")

# python D:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge\scripts\data_prep\run_pipeline.py