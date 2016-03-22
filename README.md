# 統計データベースブラウザ

本ソフトウェアは
「[政府統計の総合窓口(e-stat) API 機能](http://www.e-stat.go.jp/api/)」
を利用して，オンライン提供されている各種統計データの検索・閲覧機能を提供
するものです．

# インストール


## 稼動環境の想定

以下の環境での動作を確認しています．

* OS - CentOS 7
* HTTP server - apache HTTPd Server
* Application Framework - Flask
* Application Container - mod_wsgi

## インストールの実行

Makefile.sample を Makefile にコピーして，下記パラメータを編集してください．

* DSTDIR - 本ソフトウェアを展開するディレクトリ
* URLPREFIX - アプリケーションアクセス用 URL
* APPID - [政府統計の総合窓口(e-stat) API 機能]から利用登録して取得

以下の手順で作業を行います．

    $ cp Makefile.sample Makefile
    $ editor Makefile
    $ sudo make install

## 動作確認

ウェブブラウザで下記 URL にアクセスします．

    http://インストールサーバー/api/sample2/tokeidb

# 機能紹介

本ソフトウェアは，下記 API 機能に対応した機能構成となっています．

* 統計表情報取得
* メタ情報取得
* 統計データ取得

## 統計表情報取得

トップページには，収録された各種政府統計調査と，調査年度，公開年度の一覧
表が表示されます．

閲覧したい(政府統計，年度)に対応した緑色のボタンをクリックします．

統計表一覧の取得 API (getStatsList) の実行結果が表示されます．

## メタ情報取得

統計 ID(統計表) の一覧表が表示されます．

閲覧したい統計 ID に対応した緑色のボタンをクリックします．

メタデータ情報取得 API (getMetaInfo) の実行結果が表示されます．

## 統計データ取得

選択した統計表のメタデータが表示されます．

パラメータを設定して「getStatsData 実行」をクリックします．

設定したパラメータを適用した結果として統計データが表示されます．

データ転送量を鑑みて，データの表示上限を 200 件としています．

# License

The MIT License (MIT)
Copyright (c) 2016 National Statistics Center

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

        
        
