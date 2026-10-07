import io,os,tempfile,sqlite3,json,sys
from unittest.mock import patch
import pymupdf
from pathlib import Path
from streamlit.testing.v1 import AppTest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest

class NoticeUITest(unittest.TestCase):
    def test_upload_review_append_and_save(self):
        os.environ['BID_SCHEDULE_DB']=tempfile.mktemp(suffix='.sqlite3')
        doc=pymupdf.open();page=doc.new_page();page.insert_text((50,50),'工事名: 確認道路工事\n参加申請書の提出期限: 令和8年10月9日\n入札日時: 令和8年10月20日\n開札日時: 令和8年10月21日\n工期: 契約日から令和9年3月31日まで',fontname='japan',fontsize=11)
        upload=io.BytesIO(doc.tobytes());upload.name='確認公告.pdf';doc.close()
        with patch('streamlit.file_uploader',return_value=upload):
         at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
         assert not at.exception,at.exception
         next(b for b in at.button if b.label=='PDFを読み取る').click().run()
         assert not at.exception,at.exception
         assert at.text_input[0].value=='確認道路工事'
         assert at.date_input[0].value.isoformat()=='2026-10-09'
         assert at.date_input[3].value is None
         at.text_input[1].set_value('山田太郎')
         next(b for b in at.button if b.label=='確認した内容を案件表へ追加').click().run()
         assert not at.exception,at.exception
         assert len(at.session_state['bid_frame'])==1
         assert at.session_state['bid_frame'].iloc[0]['配置技術者名']=='山田太郎'
         next(b for b in at.button if b.label=='変更を保存').click().run()
         assert not at.exception,at.exception
         with sqlite3.connect(os.environ['BID_SCHEDULE_DB']) as con:
          data=json.loads(con.execute('SELECT payload FROM schedule').fetchone()[0])
         assert data[0]['件名']=='確認道路工事' and data[0]['工期開始'] is None
        os.unlink(os.environ['BID_SCHEDULE_DB'])

if __name__ == "__main__":
    unittest.main()
