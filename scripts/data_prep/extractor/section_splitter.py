import re
from typing import Dict

class SectionSplitter:
    def split(self, text: str) -> Dict[str, str]:
        """按照大点切分内容，采用位置锚点和贪婪提取策略"""
        sections = {
            "1_被告人基本信息及前科劣迹": "",
            "2_本案强制措施及羁押情况": "",
            "3_公诉机关及起诉信息": "",
            "4_审理程序与诉讼参与情况": "",
            "5_经审理查明的犯罪事实": "",
            "6_证据列举": "",
            "7_罪名认定理由": "",
            "8_量刑情节分析": "",
            "9_判决法律依据": "",
            "10_判决主文": "",
            "11_审判人员及日期": ""
        }
        
        if not text:
            return sections

        # 1. 核心位置探测
        reasoning_match = re.search(r'本院(?:经审理)?认为|经(?:审理|审理后)?认为|理由如下', text)
        reasoning_pos = reasoning_match.start() if reasoning_match else -1
        
        judgment_match = re.search(r'(?:判决|裁定)如下|如下(?:判决|裁定)', text)
        judgment_pos = judgment_match.start() if judgment_match else -1
        
        fact_markers = [
            r'经(?:开庭)?审理查明', r'(?:指控|起诉指控)[:：]', r'查明(?:如下)?[:：]?', 
            r'事实如下[:：]?', r'本院查明', r'本案事实如下', r'检察院指控[:：]'
        ]
        fact_pos = -1
        for m in fact_markers:
            match = re.search(m, text)
            if match:
                pos = match.start()
                if fact_pos == -1 or pos < fact_pos:
                    fact_pos = pos
        
        evidence_markers = [
            r'上述事实', r'以上事实', r'证据如下', r'有(?:以下)?证据', r'证据有', 
            r'证据在案', r'经当庭质证', r'证明上述事实的证据', r'证据[:：]', r'证据材料', 
            r'有.*?证实', r'本院(确认|认定)的证据'
        ]
        evidence_pos = -1
        for m in evidence_markers:
            match = re.search(m, text)
            if match:
                pos = match.start()
                if (pos > fact_pos or fact_pos == -1) and (reasoning_pos == -1 or pos < reasoning_pos):
                    if evidence_pos == -1 or pos < evidence_pos:
                        evidence_pos = pos

        # 2. 从后往前确定各部分边界
        date_pattern = r'([二〇一二三四五六七八九0-9]{4}年\s*[一二三四五六七八九十0-9]{1,2}月\s*[一二三四五六七八九十0-9]{1,3}日)'
        date_matches = list(re.finditer(date_pattern, text))
        
        personnel_markers = ["审判长", "审判员", "代理审判员", "书记员", "陪审员"]
        s11_start = -1
        search_window_size = min(500, len(text))
        search_window = text[-search_window_size:]
        window_offset = len(text) - search_window_size
        
        for m in personnel_markers:
            p = search_window.find(m)
            if p != -1:
                p_abs = p + window_offset
                if s11_start == -1 or p_abs < s11_start:
                    s11_start = p_abs
        
        if s11_start == -1 and date_matches:
            s11_start = max(0, date_matches[-1].start() - 50)
            
        if s11_start != -1:
            sections["11_审判人员及日期"] = text[s11_start:]
            main_body_end = s11_start
        else:
            main_body_end = len(text)

        if judgment_pos != -1:
            sections["10_判决主文"] = text[judgment_pos:main_body_end]
            reasoning_end = judgment_pos
        else:
            last_law_end = text.rfind("之规定")
            if last_law_end != -1 and last_law_end < main_body_end:
                sections["10_判决主文"] = text[last_law_end+3:main_body_end]
                reasoning_end = last_law_end + 3
            else:
                reasoning_end = main_body_end

        if reasoning_pos != -1:
            reasoning_text = text[reasoning_pos:reasoning_end]
            sentencing_keywords = ["从重", "从轻", "减轻", "累犯", "坦白", "自首", "立功", "认罪", "悔改", "谅解", "退赃", "初犯"]
            split_pos = -1
            for kw in sentencing_keywords:
                pos = reasoning_text.find(kw)
                if pos != -1 and (split_pos == -1 or pos < split_pos):
                    split_pos = pos
            
            if split_pos != -1:
                sentence_end = reasoning_text.rfind("。", 0, split_pos)
                if sentence_end != -1:
                    sections["7_罪名认定理由"] = reasoning_text[:sentence_end+1]
                    sections["8_量刑情节分析"] = reasoning_text[sentence_end+1:]
                else:
                    sections["7_罪名认定理由"] = reasoning_text[:split_pos]
                    sections["8_量刑情节分析"] = reasoning_text[split_pos:]
            else:
                sections["7_罪名认定理由"] = reasoning_text
            head_and_facts_end = reasoning_pos
        else:
            head_and_facts_end = reasoning_end

        law_match = re.search(r'((?:依照|依据|根据|遵照)《.*?》.*?第.*?条.*?之规定)', text)
        if not law_match:
            law_match = re.search(r'((?:依照|依据|根据|遵照).*?第.*?条.*?规定)', text)
        
        if law_match:
            sections["9_判决法律依据"] = law_match.group(1)

        if fact_pos == -1:
            end_trial_match = re.search(r'现已审理终结\s*[。]?', text)
            if end_trial_match:
                fact_pos = end_trial_match.end()

        if fact_pos != -1:
            if evidence_pos != -1 and evidence_pos > fact_pos:
                sections["5_经审理查明的犯罪事实"] = text[fact_pos:evidence_pos]
                sections["6_证据列举"] = text[evidence_pos:head_and_facts_end]
            else:
                sections["5_经审理查明的犯罪事实"] = text[fact_pos:head_and_facts_end]
            head_end = fact_pos
        elif evidence_pos != -1:
            sections["6_证据列举"] = text[evidence_pos:head_and_facts_end]
            head_end = evidence_pos
        else:
            head_end = head_and_facts_end

        # 3. 首部处理 - 更加鲁棒的策略
        head_text = text[:head_end]
        def_match = re.search(r'被告人[：:\s]*', head_text)
        if def_match:
            def_start = def_match.start()
            s_head = head_text[def_start:]
            
            # 不再强制分割 S1 和 S2，而是让它们共享搜索空间，或者采用更软的分割
            # S1 提取：通常包含姓名、性别、出生日期等
            sections["1_被告人基本信息及前科劣迹"] = s_head
            
            # S2 提取：专门针对强制措施
            s2_match = re.search(r'((?:因本案|因涉嫌|因犯|于).*?(?:拘留|逮捕|取保候审|监视居住|看守所|羁押|取保).*?(?:[。，]|$))', s_head)
            if s2_match:
                sections["2_本案强制措施及羁押情况"] = s2_match.group(1)

            # S3/S4 依然通过 head_text 搜索
        else:
            sections["1_被告人基本信息及前科劣迹"] = head_text[:min(300, len(head_text))]

        pro_m = re.search(r'([^。]*?人民检察院[^。]*?(?:起诉书|指控|公诉)[^。]*?。)', head_text)
        if pro_m: sections["3_公诉机关及起诉信息"] = pro_m.group(1)
        proc_m = re.search(r'([^。]*?(?:适用.*?程序|公开开庭|独任审判|现已审理终结|由.*?审理|合议庭|普通程序)[^。]*?。)', head_text)
        if proc_m: sections["4_审理程序与诉讼参与情况"] = proc_m.group(1)

        return sections
