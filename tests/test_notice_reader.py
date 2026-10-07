import io
import json
import unittest
from unittest.mock import patch

import pymupdf

from notice_reader import extract_rules, parsed_dates, pdf_content, extract_ai

NOTICE = '''入札公告
公告日 令和8年10月1日
工事名: 京都道路舗装工事
参加申請書の提出期間: 令和8年10月2日から令和8年10月9日まで
入札日時: 令和8年10月20日
開札日時: 令和8年10月21日
工期: 令和8年11月1日から令和9年1月31日まで
'''

class NoticeTest(unittest.TestCase):
    def test_rules_extract_deadline_and_reiwa_range(self):
        values, sources, warnings = extract_rules(NOTICE)
        self.assertEqual(values, {'件名':'京都道路舗装工事','申請日':'2026-10-09','入札日':'2026-10-20','開札日':'2026-10-21','工期開始':'2026-11-01','工期終了':'2027-01-31'})
        self.assertIn('令和8年10月9日', sources['申請日'])
        self.assertFalse(warnings)

    def test_relative_start_not_invented(self):
        values, _, warnings = extract_rules('工事名称: 河川工事\n工期: 契約日から令和9年3月31日まで')
        self.assertEqual(values['件名'], '河川工事')
        self.assertIsNone(values['工期開始'])
        self.assertEqual(values['工期終了'], '2027-03-31')
        self.assertTrue(warnings)

    def test_ambiguous_dates_remain_empty(self):
        values, _, warnings = extract_rules('開札日: 2026年10月20日\n開札日: 2026年10月21日')
        self.assertIsNone(values['開札日'])
        self.assertTrue(warnings)

    def test_invalid_dates_and_full_width(self):
        self.assertEqual(parsed_dates('令和8年2月30日'), [])
        values, _, _ = extract_rules('工事名：確認工事\n開札日：２０２６年１０月８日')
        self.assertEqual(values['開札日'], '2026-10-08')

    def test_real_pdf_extraction_and_scan_detection(self):
        doc=pymupdf.open(); page=doc.new_page()
        page.insert_text((50,50), NOTICE, fontname='japan', fontsize=11)
        text, scanned=pdf_content(doc.tobytes()); doc.close()
        self.assertFalse(scanned)
        self.assertIn('京都道路舗装工事',text)
        self.assertEqual(extract_rules(text)[0]['申請日'], '2026-10-09')
        blank=pymupdf.open();blank.new_page()
        self.assertTrue(pdf_content(blank.tobytes())[1]);blank.close()
        with self.assertRaises(ValueError):pdf_content(b'not a PDF')

    def test_ai_output_validation_without_network(self):
        values, _, _=extract_rules(NOTICE)
        body={'choices':[{'message':{'content':json.dumps(values)}}]}
        with patch('notice_reader.urllib.request.urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            self.assertEqual(extract_ai(b'',NOTICE,False,'test-key'),values)
        values['開札日']='2026-02-30'
        body['choices'][0]['message']['content']=json.dumps(values)
        with patch('notice_reader.urllib.request.urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            with self.assertRaises(ValueError):extract_ai(b'',NOTICE,False,'test-key')

if __name__=='__main__':unittest.main()
