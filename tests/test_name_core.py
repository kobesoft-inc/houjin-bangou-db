"""name / name_core の作り方の試験。

CASES は、Formia（このDBを使う側）の CorporationName::normalize / core に同じ入力を通して得た値
（入力, 正規化した名前 name, 名前の芯 name_core）。同じ入力から同じ出力になることを確かめる。
全角スペースは見分けがつかないため \\u3000 と書いている。

    python3 -m unittest discover -s tests -v
"""

import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build_db  # noqa: E402

CASES = [
    (" ﾄﾖﾀ自動車  株式会社 abc-1 ", "トヨタ自動車\u3000株式会社\u3000ａｂｃー１", "トヨタ自動車ＡＢＣー１"),
    ("㈱ﾃｽﾄ･ﾎｰﾙﾃﾞｨﾝｸﾞｽ", "（株）テスト・ホールディングス", "テスト・ホールディングス"),
    ("トヨタ自動車株式会社", "トヨタ自動車株式会社", "トヨタ自動車"),
    ("合同会社ＡＢＣ", "合同会社ＡＢＣ", "ＡＢＣ"),
    ("株式会社トヨタ商事", "株式会社トヨタ商事", "トヨタ商事"),
    ("大トヨタ建設有限会社", "大トヨタ建設有限会社", "大トヨタ建設"),
    ("国税庁", "国税庁", "国税庁"),
    ("ｱｲｳｴｵ ｶﾞｷﾞｸﾞ", "アイウエオ\u3000ガギグ", "アイウエオガギグ"),
    ("ABC‐DEF‑G‒H–I—J―K−L-MｰN", "ＡＢＣーＤＥＦーＧーＨーＩーＪーＫーＬーＭーＮ", "ＡＢＣーＤＥＦーＧーＨーＩーＪーＫーＬーＭーＮ"),
    ("A·B•C･D・E", "Ａ・Ｂ・Ｃ・Ｄ・Ｅ", "Ａ・Ｂ・Ｃ・Ｄ・Ｅ"),
    ("A \t\u3000B", "Ａ\u3000Ｂ", "ＡＢ"),
    ("  \u3000前後の空白\u3000  ", "前後の空白", "前後の空白"),
    ("Hello, World! (test) ~#", "Ｈｅｌｌｏ，\u3000Ｗｏｒｌｄ！\u3000（ｔｅｓｔ）\u3000～＃", "ＨＥＬＬＯ，ＷＯＲＬＤ！（ＴＥＳＴ）～＃"),
    ("ａｂｃ ＡＢＣ abc", "ａｂｃ\u3000ＡＢＣ\u3000ａｂｃ", "ＡＢＣＡＢＣＡＢＣ"),
    ("１２３ 123", "１２３\u3000１２３", "１２３１２３"),
    ("(株)テスト", "（株）テスト", "テスト"),
    ("（株）テスト", "（株）テスト", "テスト"),
    ("(有)ｻﾝﾌﾟﾙ", "（有）サンプル", "サンプル"),
    ("㈲サンプル", "（有）サンプル", "サンプル"),
    ("㈳協会", "（社）協会", "協会"),
    ("㈱", "（株）", "（株）"),
    ("株式会社", "株式会社", "株式会社"),
    ("株式会社\u3000株式会社", "株式会社\u3000株式会社", "株式会社株式会社"),
    ("有限会社ａｂｃ株式会社", "有限会社ａｂｃ株式会社", "ＡＢＣ"),
    ("株式会社ＮＴＴ ドコモ", "株式会社ＮＴＴ\u3000ドコモ", "ＮＴＴドコモ"),
    ("医療法人社団 青空会", "医療法人社団\u3000青空会", "青空会"),
    ("医療法人財団ひまわり", "医療法人財団ひまわり", "ひまわり"),
    ("医療法人 さくら", "医療法人\u3000さくら", "さくら"),
    ("社会福祉法人 みどりの会", "社会福祉法人\u3000みどりの会", "みどりの会"),
    ("一般社団法人日本ＡＢＣ協会", "一般社団法人日本ＡＢＣ協会", "日本ＡＢＣ協会"),
    ("公益財団法人 abc", "公益財団法人\u3000ａｂｃ", "ＡＢＣ"),
    ("特定非営利活動法人ほげ", "特定非営利活動法人ほげ", "ほげ"),
    ("国立大学法人東京大学", "国立大学法人東京大学", "東京大学"),
    ("地方独立行政法人 大阪府立病院機構", "地方独立行政法人\u3000大阪府立病院機構", "大阪府立病院機構"),
    ("独立行政法人 国立印刷局", "独立行政法人\u3000国立印刷局", "国立印刷局"),
    ("税理士法人 ABC", "税理士法人\u3000ＡＢＣ", "ＡＢＣ"),
    ("社会保険労務士法人 山田", "社会保険労務士法人\u3000山田", "山田"),
    ("農事組合法人 田んぼ", "農事組合法人\u3000田んぼ", "田んぼ"),
    ("有限責任事業組合ＬＬＰ", "有限責任事業組合ＬＬＰ", "ＬＬＰ"),
    ("学校法人 ｇａｋｕｅｎ", "学校法人\u3000ｇａｋｕｅｎ", "ＧＡＫＵＥＮ"),
    ("宗教法人 寺", "宗教法人\u3000寺", "寺"),
    ("弁護士法人 テスト", "弁護士法人\u3000テスト", "テスト"),
    ("司法書士法人テスト", "司法書士法人テスト", "テスト"),
    ("行政書士法人 テスト", "行政書士法人\u3000テスト", "テスト"),
    ("監査法人 ｔｅｓｔ", "監査法人\u3000ｔｅｓｔ", "ＴＥＳＴ"),
    ("合名会社 山田商店", "合名会社\u3000山田商店", "山田商店"),
    ("合資会社 田中", "合資会社\u3000田中", "田中"),
    ("(同)テスト", "（同）テスト", "テスト"),
    ("(名)テスト", "（名）テスト", "テスト"),
    ("(資)テスト", "（資）テスト", "テスト"),
    ("(社)テスト", "（社）テスト", "テスト"),
    ("(財)テスト", "（財）テスト", "テスト"),
    ("(医)テスト", "（医）テスト", "テスト"),
    ("(福)テスト", "（福）テスト", "テスト"),
    ("(学)テスト", "（学）テスト", "テスト"),
    ("(宗)テスト", "（宗）テスト", "テスト"),
    ("ストレート ßtraße", "ストレート\u3000ßｔｒａßｅ", "ストレートSSＴＲＡSSＥ"),
    ("ǆabc ǅ", "ｄžａｂｃ\u3000Ｄž", "ＤŽＡＢＣＤŽ"),
    ("ﬁnance ﬀ", "ｆｉｎａｎｃｅ\u3000ｆｆ", "ＦＩＮＡＮＣＥＦＦ"),
    ("İstanbul ı", "İｓｔａｎｂｕｌ\u3000ı", "İＳＴＡＮＢＵＬI"),
    ("ΑΒΓ αβγ ς", "ΑΒΓ\u3000αβγ\u3000ς", "ΑΒΓΑΒΓΣ"),
    ("ﾊﾟﾋﾟﾌﾟ", "パピプ", "パピプ"),
    ("㈱ＡＢＣ㈲", "（株）ＡＢＣ（有）", "ＡＢＣ"),
    ("ＡＢＣ（株）ＤＥＦ", "ＡＢＣ（株）ＤＥＦ", "ＡＢＣＤＥＦ"),
    ("日本\u3000\u3000電気", "日本\u3000電気", "日本電気"),
    ("", "", ""),
    ("\u3000", "", ""),
    ("Ａ\u3000Ｂ", "Ａ\u3000Ｂ", "ＡＢ"),
    ("①②③ ㈠ ㌔ ㍿", "１２３\u3000（一）\u3000キロ\u3000株式会社", "１２３（一）キロ"),
    ("abc\\u{3000}株式会社", "ａｂｃ＼ｕ｛３０００｝株式会社", "ＡＢＣ＼Ｕ｛３０００｝"),
    ("株式会社ABC株式会社", "株式会社ＡＢＣ株式会社", "ＡＢＣ"),
    ("ｶﾌﾞｼｷｶﾞｲｼｬ", "カブシキガイシャ", "カブシキガイシャ"),
    ("㍿テスト", "株式会社テスト", "テスト"),
    ("医療法人社団医療法人財団", "医療法人社団医療法人財団", "医療法人社団医療法人財団"),
    ("社会福祉法人社会福祉法人", "社会福祉法人社会福祉法人", "社会福祉法人社会福祉法人"),
    ("Ｋ＆Ｋ", "Ｋ＆Ｋ", "Ｋ＆Ｋ"),
    ("A&B", "Ａ＆Ｂ", "Ａ＆Ｂ"),
    ("A/B\\C", "Ａ／Ｂ＼Ｃ", "Ａ／Ｂ＼Ｃ"),
    ("tab\tsep", "ｔａｂ\u3000ｓｅｐ", "ＴＡＢＳＥＰ"),
    ("人名\u3000太郎", "人名\u3000太郎", "人名太郎"),
    ("ｖｉｔａ ｖＩｔａ", "ｖｉｔａ\u3000ｖＩｔａ", "ＶＩＴＡＶＩＴＡ"),
    ("\U0001f600株式会社", "\U0001f600株式会社", "\U0001f600"),
    ("ａ！？", "ａ！？", "Ａ！？"),
]


class NameCoreTest(unittest.TestCase):
    def test_normalize_and_core_match_the_reference_table(self):
        for raw, name, name_core in CASES:
            with self.subTest(raw=raw):
                self.assertEqual(name, build_db.normalize_name(raw))
                self.assertEqual(name_core, build_db.core_name(name))

    def test_core_is_never_empty_for_a_non_empty_name(self):
        for form in build_db.LEGAL_FORMS:
            self.assertNotEqual("", build_db.core_name(form))

    def test_legal_forms_are_listed_longest_first_within_prefixes(self):
        # 先に短い語を除くと、長い語が壊れて残る（「医療法人」が先だと「医療法人社団」の「社団」が残る）
        forms = build_db.LEGAL_FORMS
        for i, shorter in enumerate(forms):
            for longer in forms[i + 1 :]:
                self.assertNotIn(shorter, longer, f"{shorter} が {longer} より先にある")


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(build_db.SCHEMA)
        build_db.ensure_kinds(self.conn)
        self.conn.execute(build_db.NAME_CORE_INDEX)

    def tearDown(self):
        self.conn.close()

    def row(self, number, name, close_cause=""):
        # 全件データのCSVと同じ並び（使う列だけ埋める）
        cells = [""] * 30
        cells[1], cells[2], cells[6], cells[8] = str(number), "01", name, "301"
        cells[9], cells[10], cells[11] = "東京都", "千代田区", "丸の内１－１"
        cells[13], cells[14], cells[19] = "13", "101", close_cause
        return cells

    def test_apply_rows_fills_name_core_and_updates_it_on_change(self):
        build_db.apply_rows(self.conn, [self.row(1, "㈱ﾄﾖﾀ"), self.row(2, "合同会社 abc")])
        got = dict(self.conn.execute("SELECT corporate_number, name_core FROM corporations"))
        self.assertEqual({1: "トヨタ", 2: "ＡＢＣ"}, got)

        build_db.apply_rows(self.conn, [self.row(1, "株式会社ホンダ")])
        self.assertEqual(
            "ホンダ", self.conn.execute("SELECT name_core FROM corporations WHERE corporate_number = 1").fetchone()[0]
        )

    def test_name_core_prefix_range_uses_the_index(self):
        build_db.apply_rows(
            self.conn,
            [self.row(1, "トヨタ自動車株式会社"), self.row(2, "株式会社トヨタ商事"), self.row(3, "ホンダ")],
        )
        sql = "SELECT corporate_number FROM corporations WHERE name_core >= ? AND name_core < ? || char(0x10FFFF)"
        plan = " ".join(r[3] for r in self.conn.execute("EXPLAIN QUERY PLAN " + sql, ("トヨタ", "トヨタ")))
        self.assertIn("idx_corporations_name_core", plan)
        self.assertEqual([1, 2], sorted(r[0] for r in self.conn.execute(sql, ("トヨタ", "トヨタ"))))

    def test_prefecture_prefix_range_uses_the_composite_index(self):
        for statement in build_db.PREFECTURE_INDEXES:
            self.conn.execute(statement)
        build_db.apply_rows(self.conn, [self.row(1, "トヨタ自動車株式会社"), self.row(2, "ホンダ")])
        sql = "SELECT corporate_number FROM corporations WHERE prefecture_code = ? AND name >= ? AND name < ? || char(0x10FFFF)"
        plan = " ".join(r[3] for r in self.conn.execute("EXPLAIN QUERY PLAN " + sql, ("23", "トヨタ", "トヨタ")))
        self.assertIn("idx_corporations_prefecture_name", plan)

    def test_existing_columns_keep_their_order_and_name_core_is_last(self):
        columns = [r[1] for r in self.conn.execute("PRAGMA table_info(corporations)")]
        self.assertEqual(
            ["corporate_number", "name", "prefecture_code", "city_code", "address", "kind", "close_cause", "name_core"],
            columns,
        )
        indexes = {r[1] for r in self.conn.execute("PRAGMA index_list(corporations)")}
        for name in ("idx_corporations_name", "idx_corporations_name_core", "idx_corporations_city_code", "idx_corporations_close_cause"):
            self.assertIn(name, indexes)


if __name__ == "__main__":
    unittest.main()
