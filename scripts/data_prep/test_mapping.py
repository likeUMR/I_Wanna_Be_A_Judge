# -*- coding: utf-8 -*-
from extractor import LocationMapper
import os
import sys

# Ensure output handles UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

project_root = r"d:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge"
admin_csv = os.path.join(project_root, "public", "processed_admin_divisions.csv")
mapper = LocationMapper(admin_csv)

test_cases = [
    ("北京市", "北京市海淀区人民法院"),
    ("北京市", "北京市朝阳区人民法院"),
    ("北京市", "北京市西城区人民法院"),
    ("天津市", "天津市河西区人民法院")
]

for region, court in test_cases:
    adcode = mapper.map(region, court)
    print(f"Region: {region}, Court: {court} => AdCode: {adcode}")
