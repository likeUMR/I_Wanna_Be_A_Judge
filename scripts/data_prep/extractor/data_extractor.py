import re
from typing import Dict, Any, Optional
from .section_splitter import SectionSplitter
import sys
import os

# 将上级目录添加到路径以便导入 helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from helpers.citation_utils import parse_citations, cn_to_an
except ImportError:
    def parse_citations(text): return []
    def cn_to_an(cn_str):
        if not cn_str: return 0
        if isinstance(cn_str, (int, float)): return int(cn_str)
        return int(cn_str) if str(cn_str).isdigit() else 0

class JudgmentExtractor:
    def __init__(self):
        # 允许中文数字、阿拉伯数字、点号等
        self.num_pattern = r'[0-9.一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟万０-９．]+'
        self.splitter = SectionSplitter()
        
        # 预编译常用正则表达式
        self.re_name = re.compile(r'被告人([^\s，,。；：(（]{2,10})')
        # 增强性别识别 - 更加宽松
        self.re_gender = re.compile(r'[，,。、\s(（](男|女)[，,。、\s)）]?')
        # 新增：直接提取年龄的正则
        self.re_age_direct = re.compile(r'[，,。、\s(（]现年(\d{1,3})岁')
        self.re_birth = [
            # 1980年1月1日
            re.compile(r'((?:一九|二〇|[12][09])[\d零一二三四五六七八九]{2}年\d{1,2}月\d{1,2}日)\s*(?:出生|生)'),
            # 1980.1.1
            re.compile(r'(\d{4}[.．]\d{1,2}[.．]\d{1,2})\s*(?:出生|生)'),
            # 出生于...
            re.compile(r'(?:出生于|生于|出生|生于)\s*((?:一九|二〇|[12][09])[\d零一二三四五六七八九]{2}年\d{1,2}月\d{1,2}日)'),
            # 简化版日期 (支持缺失“日”的情况)
            re.compile(r'([12][09]\d{2}年\d{1,2}月\d{1,2}(?:日)?)\s*(?:出生|生|于|在)'),
            # 1980.1.1 这种格式
            re.compile(r'(\d{4}[.．]\d{1,2}[.．]\d{1,2})')
        ]
        self.re_location = re.compile(r'(?:出生于|户籍所在地|户籍地|籍贯|出生地|系|住)([\u4e00-\u9fa5]{2,30}?(?=[，,。、\s(（]|$))')
        self.re_ethnic = re.compile(r'([\u4e00-\u9fa5]{1,10}族)')
        # 增强文化程度识别
        self.re_edu = re.compile(r'([^\s，,。、；]{2,10}?(?:文化|毕业|在读|程度|文盲|识字|小学|初中|高中|中专|大专|大学|本科|研究生|硕士|博士))')
        self.re_residence = re.compile(r'(?:住所地|住|现住|居住在)([\u4e00-\u9fa5\d]{2,40}?(?=[，,。、；\s(（]|$))')
        self.re_prior_criminal = re.compile(r'(\d{4}年\d{1,2}月.*?被判处.*?(?=[；。]|$))')
        self.re_prior_admin = re.compile(r'(\d{4}年\d{1,2}月.*?被(?:劳动教养|行政拘留|处罚).*?(?=[；。]|$))')
        self.re_recidivist = re.compile(r'(系累犯|构成累犯|是累犯|应从重处罚|应当从重处罚)')
        
        # 增加对“于”的支持
        self.re_detention = re.compile(r'(?:于)?(\d{4}年\d{1,2}月\d{1,2}日).*?被刑事拘留')
        self.re_arrest = re.compile(r'(?:于)?(\d{4}年\d{1,2}月\d{1,2}日).*?被逮捕')
        self.re_jail = re.compile(r'现押于([\u4e00-\u9fa5]+看守所)')
        
        self.re_prosecutor = re.compile(r'([\u4e00-\u9fa5]+人民检察院)')
        self.re_indictment = re.compile(r'以(.*?起诉书)')
        self.re_charge = re.compile(r'(?:指控|起诉指控)被告人.*?犯([\u4e00-\u9fa5]+罪)')
        self.re_prosecution_date = re.compile(r'于(\d{4}年\d{1,2}月\d{1,2}日)向本院提起公诉')
        
        self.re_procedure = re.compile(r'适用(.*?程序)')
        
        self.re_time = re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时许|\d{4}年\d{1,2}月\d{1,2}日)')
        self.re_place = re.compile(r'在([\u4e00-\u9fa5\d]+(?:附近|路|街|巷|号|店|家|处|地))')
        self.re_money = re.compile(r'(?:共计|价值|金额为|人民币)(?:约)?(' + self.num_pattern + r')余?元')
        
        self.re_action = re.compile(r'，(.*?)，其行为已构成')
        self.re_crime_type = re.compile(r'构成([\u4e00-\u9fa5]+罪)')
        self.re_attempt = re.compile(r'(犯罪未遂|未遂|因意志以外原因未得逞)')
        
        self.re_aggravating = re.compile(r'(累犯|前科|主观恶性大|多次|应当从重处罚|地位作用突出|手段残忍|社会影响恶劣|情节严重)')
        self.re_mitigating = re.compile(r'(坦白|如实供述|谅解|初犯|偶犯|赃物已全部追回|可以从轻处罚|退缴全部赃款|减少社会危害|认罪悔罪|自愿认罪)')
        
        self.re_surrender = re.compile(r'(系自首|构成自首|有自首情节|主动投案)')
        self.re_merit = re.compile(r'(立功表现|构成立功|有立功情节)')
        self.re_pardon = re.compile(r'(取得谅解|达成和解|谅解了被告人|达成协议)')
        self.re_truth = re.compile(r'(如实供述|坦白|认罪态度较好|能够认罪)')
        self.re_return_property = re.compile(r'(退赃|退赔|退缴|赔偿|赃物已全部追回|退还)')
        
        self.re_final_crime = re.compile(r'犯([\u4e00-\u9fa5]+罪)')
        self.re_sentence = re.compile(r'判处(有期徒刑|拘役|管制|无期徒刑|死刑|罚金)(?:(' + self.num_pattern + r')年)?(?:零?(' + self.num_pattern + r')个月)?(?:(' + self.num_pattern + r')日)?')
        self.re_fine = re.compile(r'罚金人民币(' + self.num_pattern + r')元')
        self.re_extra_penalty = re.compile(r'并处(罚金人民币' + self.num_pattern + r'元)')
        self.re_duration = re.compile(r'自(\d{4}年\d{1,2}月\d{1,2}日起至\d{4}年\d{1,2}月\d{1,2}日止)')
        self.re_fine_limit = re.compile(r'罚金限(.*?缴纳)')
        
        self.re_judge = re.compile(r'审判员\s*([\u4e00-\u9fa5]{2,3})')
        self.re_clerk = re.compile(r'书记员\s*([\u4e00-\u9fa5]{2,3})')
        self.re_date = re.compile(r'([二〇一二三四五六七八九]{4}年[一二三四五六七八九十]{1,2}月[一二三四五六七八九十]{1,3}日)')
        self.re_assessor = re.compile(r'人民陪审员\s*([\u4e00-\u9fa5]{2,3})')

    def extract_all(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str) or not text: return {}
        
        sec = self.splitter.split(text)
        res = {}
        
        # 1. 尝试从全文获取判决日期，作为年龄计算参考
        judgment_year = 2013 # 默认2013
        date_match = self.re_date.search(sec["11_审判人员及日期"] or text)
        if date_match:
            date_str = date_match.group(1)
            if '二〇一三' in date_str or '2013' in date_str: judgment_year = 2013
            elif '二〇一二' in date_str or '2012' in date_str: judgment_year = 2012
            elif '二〇一一' in date_str or '2011' in date_str: judgment_year = 2011
            elif '二〇一四' in date_str or '2014' in date_str: judgment_year = 2014

        # Section 1: 被告人信息
        s1 = sec["1_被告人基本信息及前科劣迹"]
        res["SECTION_1_被告人基本信息及前科劣迹"] = s1
        
        # 姓名
        name_match = self.re_name.search(s1)
        res['姓名'] = name_match.group(1) if name_match else None
        
        # 特殊身体状况
        res['特殊身体状况'] = "盲人" if "盲" in s1 else ("聋哑人" if "聋哑" in s1 else ("残疾" if "残疾" in s1 else "正常"))
        
        # 精神状态
        res['精神状态'] = "完全刑事责任能力" if "完全刑事责任能力" in s1 else ("限制刑事责任能力" if "限制刑事责任能力" in s1 else "正常")
        if "精神病" in s1 and res['精神状态'] == "正常": res['精神状态'] = "精神病相关"

        # 性别
        gender_match = self.re_gender.search(s1)
        res['性别'] = gender_match.group(1) if gender_match else None
        
        # 出生日期
        birth_match = None
        for r in self.re_birth:
            birth_match = r.search(s1)
            if birth_match: break
        res['出生日期'] = birth_match.group(1) if birth_match else None
        
        # 是否未成年
        res['是否未成年'] = 1 if "未成年" in s1 else 0
        # 年龄计算
        res['年龄'] = None
        if res['出生日期']:
            norm_date = res['出生日期'].replace('二〇', '20').replace('一九', '19').replace('.', '-').replace('．', '-')
            year_match = re.search(r'(\d{4})', norm_date)
            if year_match:
                birth_year = int(year_match.group(1))
                if birth_year < judgment_year:
                    res['年龄'] = judgment_year - birth_year
            
            if res['年龄'] is not None and res['年龄'] < 18: 
                res['是否未成年'] = 1
        
        # 如果通过出生日期没算出来，尝试直接提取
        if res['年龄'] is None:
            age_match = self.re_age_direct.search(s1)
            if age_match:
                res['年龄'] = int(age_match.group(1))
                if res['年龄'] < 18:
                    res['是否未成年'] = 1

        # 民族/籍贯/学历/职业
        loc_match = self.re_location.search(s1)
        res['出生地/户籍地'] = loc_match.group(1) if loc_match else None
        
        ethnic_match = self.re_ethnic.search(s1)
        res['民族'] = ethnic_match.group(1) if ethnic_match else None
        
        edu_match = self.re_edu.search(s1)
        res['文化程度'] = edu_match.group(1) if edu_match else None
        
        # 优化职业识别 - 增加更多关键词
        occ = None
        occ_kws = [
            '农民', '无业', '务工', '工人', '教师', '医生', '干部', '学生', '个体', '职员', 
            '商人', '经商', '司机', '保安', '退休', '无固定职业', '退休人员', '公司职员', 
            '经理', '法务', '律师', '会计', '厨师', '快递员', '外卖员', '程序员', '工程师',
            '负责人', '法定代表人', '经理', '副经理', '总经理', '职员', '员工'
        ]
        for kw in occ_kws:
            if kw in s1: occ = kw; break
        
        # 如果没匹配到常见词，尝试用正则匹配 “...为业” 或 “从事...”
        if not occ:
            occ_match = re.search(r'(?:系|为|从事)([^\s，,。、；]{2,10}?(?:人员|工作|职业|为业|经理|职员|工人|农民))', s1)
            if occ_match:
                occ = occ_match.group(1)
        
        res['职业'] = occ
        
        res_match = self.re_residence.search(s1)
        res['住所地'] = res_match.group(1) if res_match else None
        
        # 前科信息
        res['刑事前科'] = "；".join(self.re_prior_criminal.findall(s1)) or "无"
        res['行政处罚/非刑罚处理'] = "；".join(self.re_prior_admin.findall(s1)) or "无"
        
        res['是否初犯'] = 1 if res['刑事前科'] == "无" else 0
        res['是否累犯'] = 1 if self.re_recidivist.search(s1 + sec["8_量刑情节分析"]) else 0

        # Section 2: 强制措施
        s2 = sec["2_本案强制措施及羁押情况"]
        res["SECTION_2_本案强制措施及羁押情况"] = s2
        det_match = self.re_detention.search(s2)
        res['刑事拘留时间'] = det_match.group(1) if det_match else None
        arr_match = self.re_arrest.search(s2)
        res['逮捕时间'] = arr_match.group(1) if arr_match else None
        jail_match = self.re_jail.search(s2)
        res['当前羁押地点'] = jail_match.group(1) if jail_match else None

        # Section 3: 起诉信息
        s3 = sec["3_公诉机关及起诉信息"]
        res["SECTION_3_公诉机关及起诉信息"] = s3
        pros_match = self.re_prosecutor.search(s3)
        res['公诉机关'] = pros_match.group(1) if pros_match else None
        ind_match = self.re_indictment.search(s3)
        res['起诉书文号'] = ind_match.group(1) if ind_match else None
        charge_match = self.re_charge.search(s3)
        res['指控罪名'] = charge_match.group(1) if charge_match else None
        pdate_match = self.re_prosecution_date.search(s3)
        res['提起公诉日期'] = pdate_match.group(1) if pdate_match else None

        # Section 4: 审理程序
        s4 = sec["4_审理程序与诉讼参与情况"]
        res["SECTION_4_审理程序与诉讼参与情况"] = s4
        proc_match = self.re_procedure.search(s4)
        res['审理程序'] = proc_match.group(1) if proc_match else None
        res['审判组织形式'] = "独任审判" if "独任" in s4 else ("合议庭" if "合议庭" in s4 else None)
        res['是否公开审理'] = "是" if "公开" in s4 else "否"
        res['被告人出庭情况'] = "到庭参加诉讼" if "到庭" in s4 else None
        res['审理状态'] = "已审理终结" if "终结" in s4 or "审理终结" in s4 else None

        # Section 5: 犯罪事实
        s5 = sec["5_经审理查明的犯罪事实"]
        res["SECTION_5_经审理查明的犯罪事实"] = s5
        time_match = self.re_time.search(s5)
        res['作案时间'] = time_match.group(1) if time_match else None
        place_match = self.re_place.search(s5)
        res['作案地点'] = place_match.group(1) if place_match else None
        res['作案情况'] = s5[:200] + "..." if len(s5) > 200 else s5
        money_match = self.re_money.search(s5)
        res['涉案金额'] = cn_to_an(money_match.group(1)) if money_match else 0

        # Section 6: 证据
        res["SECTION_6_证据列举"] = sec["6_证据列举"]

        # Section 7: 罪名认定
        s7 = sec["7_罪名认定理由"]
        res["SECTION_7_罪名认定理由"] = s7
        res['主观方面'] = "以非法占有为目的" if "非法占有" in s7 else None
        act_match = self.re_action.search(s7)
        res['客观行为'] = act_match.group(1) if act_match else (s7[:100] if s7 else None)
        ctype_match = self.re_crime_type.search(s7)
        res['法律定性'] = ctype_match.group(1) if ctype_match else None
        res['是否未遂'] = 1 if self.re_attempt.search(s7 + text) else 0

        # Section 8: 量刑情节
        s8 = sec["8_量刑情节分析"]
        res["SECTION_8_量刑情节分析"] = s8
        res['从重情节'] = "；".join(set(self.re_aggravating.findall(s8)))
        res['从轻情节'] = "；".join(set(self.re_mitigating.findall(s8)))
        res['是否自首'] = 1 if self.re_surrender.search(s8) else 0
        res['是否立功'] = 1 if self.re_merit.search(s8) else 0
        res['是否取得谅解'] = 1 if self.re_pardon.search(s8) else 0
        res['是否如实供述'] = 1 if self.re_truth.search(s8) else 0
        res['是否退赃'] = 1 if self.re_return_property.search(s8) else 0
        if res['是否立功']: res['surrender_type'] = 2
        elif res['是否自首']: res['surrender_type'] = 1
        else: res['surrender_type'] = 0
        res['主从犯身份'] = "从犯" if "从犯" in s8 else ("主犯" if "主犯" in s8 else "不详")

        # Section 9: 法律依据
        res["SECTION_9_判决法律依据"] = sec["9_判决法律依据"]
        res['法律依据'] = "；".join(parse_citations(sec["9_判决法律依据"])) if sec["9_判决法律依据"] else ""

        # Section 10: 判决主文
        s10 = sec["10_判决主文"]
        res["SECTION_10_判决主文"] = s10
        res['案由'] = res['指控罪名']
        final_crime = self.re_final_crime.search(s10)
        if final_crime:
            res['罪名'] = final_crime.group(1)
            res['案由'] = res['罪名']
        else:
            res['罪名'] = None
            
        sent_m = self.re_sentence.search(s10)
        if sent_m:
            res['主刑'] = sent_m.group(1)
            res['刑期_年'] = cn_to_an(sent_m.group(2)) if sent_m.group(2) else 0
            res['刑期_月'] = cn_to_an(sent_m.group(3)) if sent_m.group(3) else 0
        else:
            res['主刑'] = None; res['刑期_年'] = 0; res['刑期_月'] = 0
            
        fine_match = self.re_fine.search(s10)
        res['罚金'] = cn_to_an(fine_match.group(1)) if fine_match else 0
        ex_match = self.re_extra_penalty.search(s10)
        res['附加刑'] = ex_match.group(1) if ex_match else None
        dur_match = self.re_duration.search(s10)
        res['刑期起止'] = dur_match.group(1) if dur_match else None
        fl_match = self.re_fine_limit.search(s10)
        res['罚金缴纳期限'] = fl_match.group(1) if fl_match else None

        # Section 11: 审判人员
        s11 = sec["11_审判人员及日期"]
        res["SECTION_11_审判人员及日期"] = s11
        judge_match = self.re_judge.search(s11)
        res['审判员'] = judge_match.group(1) if judge_match else None
        clerk_match = self.re_clerk.search(s11)
        res['书记员'] = clerk_match.group(1) if clerk_match else None
        date_match = self.re_date.search(s11)
        res['判决日期'] = date_match.group(1) if date_match else None
        res['是否合议庭'] = "是" if "合议庭" in s11 else "否"
        ass_match = self.re_assessor.search(s11)
        res['人民陪审员'] = ass_match.group(1) if ass_match else "无"
            
        return res
