"""Editable bid schedule with SQLite persistence and a daily timeline."""
import io
import json
import os
import sqlite3
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

COLUMNS = ['件名', '配置技術者名', '申請日', '入札日', '開札日', '工期開始', '工期終了', '備考']
DATES = COLUMNS[2:7]
DB = Path(os.environ.get('BID_SCHEDULE_DB', str(Path(__file__).resolve().parents[2] / 'kyoto-projects-data' / 'bids.sqlite3')))


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, revision INTEGER NOT NULL)')
    return con


def load():
    with connect() as con:
        row = con.execute('SELECT payload, revision FROM schedule WHERE id=1').fetchone()
    records, revision = (json.loads(row[0]), row[1]) if row else ([], 0)
    frame = pd.DataFrame(records, columns=COLUMNS)
    for column in DATES:
        frame[column] = pd.to_datetime(frame[column]).dt.date
    return frame, revision


def normalize(frame):
    records = []
    for number, (_, row) in enumerate(frame.iterrows(), 1):
        record = {c: None if pd.isna(row[c]) else row[c] for c in COLUMNS}
        for c in ['件名', '配置技術者名', '備考']:
            record[c] = str(record[c] or '').strip()
        if not any(record.values()):
            continue
        if not record['件名']:
            raise ValueError(f'{number}行目：件名を入力してください。')
        for c in DATES:
            if record[c] is not None:
                record[c] = pd.Timestamp(record[c]).date().isoformat()
        if record['工期開始'] and record['工期終了'] and record['工期開始'] > record['工期終了']:
            raise ValueError(f'{number}行目：工期終了は工期開始以降の日付にしてください。')
        records.append(record)
    return records


def save(records, revision):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT revision FROM schedule WHERE id=1').fetchone()
        if (row[0] if row else 0) != revision:
            raise ValueError('別の画面で更新されています。入力内容をExcelで控えてから「保存済みデータを再読込」を押してください。')
        con.execute('INSERT INTO schedule VALUES(1, ?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, revision=excluded.revision', (json.dumps(records, ensure_ascii=False), revision + 1))
    return revision + 1


def overlaps(records):
    result = []
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            if a['配置技術者名'] and a['配置技術者名'] == b['配置技術者名'] and all(x[k] for x in [a, b] for k in ['工期開始', '工期終了']):
                start, end = max(a['工期開始'], b['工期開始']), min(a['工期終了'], b['工期終了'])
                if start <= end:
                    result.append({'配置技術者名': a['配置技術者名'], '案件1': a['件名'], '案件2': b['件名'], '重複開始': start, '重複終了': end})
    return result


def events(records):
    rows = []
    for i, r in enumerate(records, 1):
        label = f"{i}. {r['件名']} ／ {r['配置技術者名'] or '技術者未定'}"
        if r['工期開始'] and r['工期終了']:
            rows.append({'案件': label, '種別': '工期', '日付': r['工期開始'], '終了': r['工期終了']})
        for c in ['申請日', '入札日', '開札日']:
            if r[c]:
                rows.append({'案件': label, '種別': c, '日付': r[c], '終了': r[c]})
    return rows


st.set_page_config(page_title='入札工程表', layout='wide')
st.title('入札案件の工程表')
st.caption('案件と配置技術者、申請・入札・開札日、工期を一画面で確認できます。')
if 'bid_frame' not in st.session_state:
    st.session_state.bid_frame, st.session_state.bid_revision = load()
    st.session_state.bid_editor_version = 0
st.subheader('案件の編集')
st.caption('セルをクリックして編集。最下行で案件を追加し、行を選択して削除できます。変更後は「変更を保存」を押してください。')
config = {c: st.column_config.DateColumn(c, format='YYYY/MM/DD') for c in DATES}
config['件名'] = st.column_config.TextColumn('件名', required=True, width='large')
edited = st.data_editor(st.session_state.bid_frame, column_config=config, num_rows='dynamic', hide_index=True, width='stretch', key=f'bid_editor_{st.session_state.bid_editor_version}')
left, right = st.columns([1, 3])
with left:
    if st.button('変更を保存', type='primary'):
        try:
            records = normalize(edited)
            st.session_state.bid_revision = save(records, st.session_state.bid_revision)
            st.success('保存しました。定期的にExcelもダウンロードして控えてください。')
        except (ValueError, sqlite3.Error, OSError) as e:
            st.error(str(e))
with right:
    if st.button('保存済みデータを再読込'):
        st.session_state.bid_frame, st.session_state.bid_revision = load()
        st.session_state.bid_editor_version += 1
        st.rerun()
try:
    records = normalize(edited)
except ValueError as e:
    st.warning(str(e))
    st.stop()
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    edited.to_excel(writer, index=False, sheet_name='入札案件')
st.download_button('現在の表をExcelでダウンロード', output.getvalue(), '入札案件.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
st.subheader('工程表')
technicians = sorted({r['配置技術者名'] for r in records if r['配置技術者名']})
selected = st.multiselect('配置技術者で絞り込み', technicians)
filtered = [r for r in records if not selected or r['配置技術者名'] in selected]
rows = events(filtered)
if rows:
    all_dates = [date.fromisoformat(r[c]) for r in filtered for c in DATES if r[c]]
    earliest, latest = min(all_dates), max(all_dates)
    start, end = st.columns(2)
    with start:
        view_start = st.date_input('表示開始日', value=earliest, key='view_start')
    with end:
        view_end = st.date_input('表示終了日', value=latest, key='view_end')
    if view_end < view_start:
        st.warning('表示終了日は開始日以降にしてください。')
    elif (view_end - view_start).days > 1095:
        st.warning('表示期間は3年以内にしてください。')
    else:
        days = [view_start + timedelta(days=i) for i in range((view_end-view_start).days+1)]
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        css = '<style>.bid-scroll{overflow:auto;max-height:650px}.bid-calendar{border-collapse:collapse;font-size:13px}.bid-calendar th,.bid-calendar td{border:1px solid #ccd5e0;text-align:center;padding:5px;min-width:48px}.bid-calendar thead{position:sticky;top:0;z-index:3;background:#eef3f9;color:#17365d}.bid-calendar .name{position:sticky;left:0;background:#eef3f9;color:#17365d;min-width:220px;max-width:280px;text-align:left;z-index:2}.bid-calendar .sat{background:#e7efff;color:#1565c0}.bid-calendar .sun{background:#ffe8e8;color:#c62828}.bid-calendar .work{background:#bdd7ee;color:#17365d}.bid-calendar .event{font-weight:bold;color:#8b3300}</style>'
        header = '<tr><th class="name">件名・配置技術者</th>'
        for d in days:
            weekend = 'sun' if d.weekday() == 6 else 'sat' if d.weekday() == 5 else ''
            header += f'<th class="{weekend}">{d.year}<br>{d.month}/{d.day}<br>（{weekdays[d.weekday()]}）</th>'
        body = ''
        for r in filtered:
            body += f'<tr><td class="name">{escape(r["件名"])}<br>{escape(r["配置技術者名"] or "技術者未定")}</td>'
            for d in days:
                iso = d.isoformat()
                work = r['工期開始'] and r['工期終了'] and r['工期開始'] <= iso <= r['工期終了']
                marks = [label for column, label in [('申請日', '申'), ('入札日', '入'), ('開札日', '開')] if r[column] == iso]
                weekend = 'sun' if d.weekday() == 6 else 'sat' if d.weekday() == 5 else ''
                classes = ('work' if work else weekend) + (' event' if marks else '')
                body += f'<td class="{classes}" title="{iso}">{"・".join(marks) or ("━" if work else "")}</td>'
            body += '</tr>'
        st.caption('1日ごとの日付・曜日を表示。青い帯＝工期、申＝申請、入＝入札、開＝開札。横にスクロールできます。')
        st.html(css + '<div class="bid-scroll"><table class="bid-calendar"><thead>' + header + '</tr></thead><tbody>' + body + '</tbody></table></div>')

else:
    st.info('案件と日付を入力すると工程表を表示します。工期は開始・終了の両方を入力してください。')
conflicts = overlaps(filtered)
if conflicts:
    st.warning('同じ配置技術者の工期が重なっています。兼任できるか確認してください。')
    st.dataframe(pd.DataFrame(conflicts), hide_index=True, width='stretch')
st.caption('工程図は編集中の内容を表示します。配置重複は技術者名の完全一致で確認します。データはサーバー内に保存されます。公開サービスで環境が作り直されると失われる場合があります。')
