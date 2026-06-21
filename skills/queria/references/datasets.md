# Queria データセット一覧（スナップショット）

公開カタログ（data.queria.io）の内容を要約したもの。テーブルは増減するため、
正確な一覧は `python3 scripts/queria_query.py --list / --schema <ds> / --columns <ds>`
で取得すること。テーブル接頭辞は `mart_`（整形済み・推奨）/ `stg_`（中間）/ `raw_`（生データ）。

参照は `データセット名.スキーマ.テーブル名` の形（例: `zipcode.main.mart_zipcode`）。
結合キーが合えば複数データセットを跨いで JOIN できる（自動アタッチ）。

## zipcode — 全国郵便番号
- `zipcode.main.mart_zipcode` — 郵便番号、都道府県、市区町村、町域、`lg_code`（自治体コード）
- 結合: `lg_code` で lg_code / address_br / e_stat(ssds) と接続

## lg_code — 全国地方公共団体コード
- `lg_code.main.mart_lg_code` — `lg_code`（6桁）、`lg_code_5`、`pref_code`、都道府県、市区町村、`code_type`
- 自治体コードの基準マスタ。多くのデータセットの結合ハブ

## address_br — アドレス・ベース・レジストリ（市区町村マスタ）
- `address_br.main.mart_pref` — 都道府県マスタ（代表点 geometry あり）
- `address_br.main.mart_city` — 市区町村マスタ（政令市は市・区の両レベル）
- `address_br.main.mart_town` — 町字マスタ

## houjin_bangou — 国税庁法人番号
- `houjin_bangou.main.mart_houjin_bangou` — 現存法人 約500万件（商号・所在地・法人種別）
- 結合: `corporate_number`(=法人番号) で gbizinfo と接続

## gbizinfo — gBizINFO 法人活動情報
- `gbizinfo.main.mart_gbizinfo_company` — 法人1行に集約（資本金・従業員・設立年・業種＋補助金/調達集計＋財務）
- `gbizinfo.main.mart_gbizinfo_subsidy` — 補助金交付実績（1件1行）
- `gbizinfo.main.mart_gbizinfo_procurement` — 国の調達実績（1件1行）
- 結合: `corporate_number` で houjin_bangou と接続

## e_stat — e-Stat 政府統計（テーブルが豊富）
カタログ・検索:
- `e_stat.main.stats_catalog` — 統計表カタログ（政府統計名・分野・分類軸で横断検索）
- `e_stat.main.raw_meta_info` — 分類項目の詳細メタ

社会・人口統計体系 SSDS（都道府県/市区町村、分野 A〜K）:
- `e_stat.ssds.a_pref_population` / `e_stat.ssds.a_municipal_population` — 人口・世帯
- 以降 `b_*`自然環境 / `c_*`経済基盤 / `d_*`行政基盤 / `e_*`教育 / `f_*`労働 /
  `g_*`文化スポーツ / `h_*`居住 / `i_*`健康医療 / `j_*`福祉 / `k_*`安全
  （いずれも `_pref_` と `_municipal_` の2粒度）
- `e_stat.ssds.item_catalog` — SSDS の指標項目一覧

国勢調査 小地域境界:
- `e_stat.boundary.small_area` — 町丁・字等別の境界ポリゴン＋人口・世帯（`key_code` で結合）

## reinfolib — 不動産情報ライブラリ
- `reinfolib.main.mart_trade_prices` — 不動産取引価格・成約価格（全国）
- `reinfolib.main.mart_land_prices` — 地価公示・地価調査ポイント（全国）

## nlftp — 国土数値情報（GIS）
- `nlftp.boundary.prefecture` / `nlftp.boundary.municipality` — 行政区域境界ポリゴン（令和7年）
- `nlftp.boundary.designated_city` — 政令市の区を市レベルに統合した境界
- geometry を持つ。空間結合・地図用

## calendar — 日本の暦
- `calendar.main.mart_calendar` — 1955〜2027年の日付スパイン（祝日・曜日・和暦・会計年度）

## tsukuba — つくば市オープンデータ
- `tsukuba.main.mart_tsukuba_population` — 人口データ
- `tsukuba.main.mart_tsukuba_emergency_shelter` — 指定緊急避難場所（ODF形式）

## articles — Queria ショーケース
- `articles.main.mart_articles` — 記事メタデータ（タイトル・概要・タグ・データソース）
