import subprocess
import os
import sys
import argparse
import time

# ================= 配置区 =================
# 数据处理流水线步骤列表
# 如果需要跳过某个步骤，直接注释掉即可
STEPS = [
    # "stage1_raw_zip_processor.py",
    "stage2_legal_info_extractor.py",
    "stage3_group_by_adcode.py",
    "stage4_filter_complete_cases.py",
]

# stage4 每个 AdCode 文件保留的最大行数 (设为 None 则不限制)
STAGE4_LIMIT = 100
# stage4 每个 CSV 分片包含的案件数量
STAGE4_BLOCK_SIZE = 20
# ==========================================

def run_script(script_name, is_test=False):
    """
    运行指定的 Python 脚本
    """
    print(f"\n{'='*40}")
    print(f"正在执行步骤: {script_name}")
    if is_test:
        print(f"模式: [测试模式]")
    print(f"{'='*40}\n")
    
    start_time = time.time()
    try:
        # 构造命令
        cmd = [sys.executable, script_name]
        
        if is_test:
            cmd.append("--test")

        if script_name == "stage4_filter_complete_cases.py":
            if STAGE4_LIMIT is not None:
                cmd.extend(["--limit", str(STAGE4_LIMIT)])
            if STAGE4_BLOCK_SIZE is not None:
                cmd.extend(["--block_size", str(STAGE4_BLOCK_SIZE)])

        # 运行脚本
        subprocess.run(cmd, check=True)
        
        duration = time.time() - start_time
        
        # 检查报告或输出是否正常
        success = print_stage_report(script_name)
        
        if success:
            print(f"\n[成功] {script_name} 执行完毕且产出正常。耗时: {duration:.2f}s")
        else:
            print(f"\n[失败] {script_name} 虽然运行结束，但未产生预期数据或报告显示异常。")
        
        return success
    except subprocess.CalledProcessError as e:
        print(f"\n[错误] 执行 {script_name} 时返回非零退出代码: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[错误] 运行脚本 {script_name} 时发生未知错误: {e}")
        return False

def print_stage_report(script_name):
    """
    根据不同步骤打印对应的报告
    返回 True 表示产出正常，False 表示产出异常(为空等)
    """
    print(f"\n--- {script_name} 报告 ---")
    
    if script_name == "stage2_legal_info_extractor.py":
        output_dirs = [
            r'F:\素材\游戏制作\裁判文书\裁判文书全量数据\structured_results',
            os.path.join(os.getcwd(), 'data', 'structured_results')
        ]
        
        for d in output_dirs:
            if os.path.exists(d):
                summaries = [f for f in os.listdir(d) if f.startswith('summary_') and f.endswith('.txt')]
                if summaries:
                    summaries.sort(key=lambda x: os.path.getmtime(os.path.join(d, x)), reverse=True)
                    latest = os.path.join(d, summaries[0])
                    print(f"最新处理总结 ({os.path.basename(latest)}):")
                    try:
                        with open(latest, 'r', encoding='utf-8-sig') as f:
                            summary_content = f.read()
                            print(summary_content)
                            
                            import re
                            total_match = re.search(r"总处理:(\d+)", summary_content)
                            if total_match:
                                total_val = int(total_match.group(1))
                                if total_val == 0:
                                    print("\n[错误] Stage 2 处理了 0 条数据！")
                                    return False
                                return True
                    except Exception as e:
                        print(f"读取报告失败: {e}")
        print("未找到 stage2 报告文件或产出为空。")
        return False

    elif script_name == "stage3_group_by_adcode.py":
        output_dirs = [
            r'F:\素材\游戏制作\裁判文书\裁判文书全量数据\cases_by_adcode',
            os.path.join(os.getcwd(), 'data', 'cases_by_adcode')
        ]
        for d in output_dirs:
            if os.path.exists(d):
                files = [f for f in os.listdir(d) if f.endswith('.csv')]
                print(f"生成的 AdCode 地区文件数量: {len(files)}")
                if len(files) == 0:
                    print("\n[错误] Stage 3 生成了 0 个文件！可能是 AdCode 映射全部失败。")
                    return False
                return True
        print("未找到 stage3 输出目录。")
        return False

    elif script_name == "stage4_filter_complete_cases.py":
        report_path = os.path.join(os.getcwd(), "filtering_report.csv")
        if not os.path.exists(report_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            report_path = os.path.join(project_root, "scripts", "data_prep", "filtering_report.csv")
            
        if os.path.exists(report_path):
            try:
                import pandas as pd
                if os.path.getsize(report_path) == 0:
                    print(f"[错误] 报告文件 {report_path} 为空 (0 字节)。")
                    return False
                    
                df = pd.read_csv(report_path)
                if not df.empty:
                    print(f"总处理行政区: {len(df)}")
                    if 'PerfectRows' in df.columns:
                        print(f"累计完美案例: {int(df['PerfectRows'].sum())}")
                    if 'RetainedRows' in df.columns:
                        total_retained = int(df['RetainedRows'].sum())
                        print(f"累计保留案例: {total_retained}")
                        if total_retained == 0:
                            print("\n[错误] Stage 4 最终保留的案例数为 0！")
                            return False
                        return True
                else:
                    print("[错误] Stage 4 报告文件内容为空。")
                    return False
            except Exception as e:
                print(f"读取报告失败: {e}")
                return False
        else:
            print(f"未找到 stage4 报告文件: {report_path}")
            return False
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="裁判文书数据处理流水线")
    parser.add_argument("--test", action="store_true", help="以测试模式运行 (只处理少量数据)")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)

    print("\n" + ">>> 开始运行数据处理完整流水线 <<<".center(50))
    if args.test:
        print("!!! 注意：当前处于测试模式，将只处理少量样本数据 !!!")
    
    if STAGE4_LIMIT:
        print(f"配置信息: stage4 限制总行数 = {STAGE4_LIMIT}")
    if STAGE4_BLOCK_SIZE:
        print(f"配置信息: stage4 每个分片大小 = {STAGE4_BLOCK_SIZE}")
    print(f"待处理步骤: {', '.join(STEPS)}")
    
    results = []
    for step in STEPS:
        success = run_script(step, is_test=args.test)
        results.append((step, "成功" if success else "失败"))
        if not success:
            print(f"\n[终止] 由于 {step} 执行失败或产出为空，后续步骤已取消。")
            break
        
    print("\n" + "="*40)
    print("流水线执行总结")
    print("-" * 40)
    for step, status in results:
        print(f"{step: <35} | {status}")
    print("="*40)
    
    if any(status == "失败" for _, status in results):
        sys.exit(1)
    
    print("\n>>> 所有配置的步骤均已顺利执行完毕！ <<<")
