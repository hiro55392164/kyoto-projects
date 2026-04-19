import io
from datetime import date

import pandas as pd
import streamlit as st
from openpyxl import Workbook

st.set_page_config(page_title="施工計画書 自動作成アプリ", layout="wide")

st.title("施工計画書 自動作成アプリ")
st.write("入力フォームに入力した内容をExcelに出力します。")

with st.form("plan_form"):
    st.subheader("基本情報")
    project_name = st.text_input("工事名")
    project_number = st.text_input("工事番号")
    location = st.text_input("工事場所")
    contractor = st.text_input("受注者名")
    site_manager = st.text_input("現場代理人")

    st.subheader("工期")
    start_date = st.date_input("工期（開始）", value=date.today())
    end_date = st.date_input("工期（終了）", value=date.today())

    st.subheader("施工計画")
    overview = st.text_area("工事概要", height=120)
    safety_plan = st.text_area("安全対策", height=120)
    quality_plan = st.text_area("品質管理", height=120)
    schedule_plan = st.text_area("工程計画", height=120)

    submitted = st.form_submit_button("入力内容を確認する")

if submitted:
    data = {
        "工事名": project_name,
        "工事番号": project_number,
        "工事場所": location,
        "受注者名": contractor,
        "現場代理人": site_manager,
        "工期（開始）": str(start_date),
        "工期（終了）": str(end_date),
        "工事概要": overview,
        "安全対策": safety_plan,
        "品質管理": quality_plan,
        "工程計画": schedule_plan,
    }

    st.subheader("入力内容")
    df = pd.DataFrame([data])
    st.dataframe(df, use_container_width=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "施工計画書"

    ws["A1"] = "項目"
    ws["B1"] = "内容"

    row = 2
    for key, value in data.items():
        ws.cell(row=row, column=1, value=key)
        ws.cell(row=row, column=2, value=value)
        row += 1

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    st.download_button(
        label="Excelをダウンロード",
        data=excel_buffer,
        file_name="施工計画書_入力内容.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
