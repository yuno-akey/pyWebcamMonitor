# pyWebcamMonitor

<table>
  <!--header-->
  <tr>
    <td>License</td>
    <td>OS</td>
    <td>IDE</td>
    <td>Lang</td>
    <td>Library</td>
    <td>Thank you!</td>
  </tr>
  <!--body-->
  <tr>
    <td>
      <a href="./LICENSE">
        <img src="http://img.shields.io/badge/license-MIT-blue.svg?style=flat">
      </a>
    </td>
    <td>
      <img src="https://img.shields.io/badge/Windows_11-0078d4?style=for-the-badge&logo=windows-11&logoColor=white">
    </td>
    <td>
      <img src="https://img.shields.io/badge/VSCode-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white">
    </td>
    <td>
      <img src="https://img.shields.io/badge/python-3.13+-blue.svg">
    </td>
    <td>
      <img src="https://img.shields.io/badge/opencv-4.10+-green.svg">
      <br>
      <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white">
    </td>
    <td>
      <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">
    </td>
  </tr>
</table>

動体検知機能付きの監視カメラプログラムです。カメラからの映像を常時録画しながら、動体を検知した場合は別ファイルとして保存します。

![motion-detection-sample](https://github.com/user-attachments/assets/2399fc5a-d5eb-47ce-9d37-fb096161f430)

## 機能

- カメラ映像のリアルタイム表示と録画(初期状態では10分もしくは100MBごとにファイルを分割)
- 動体検知時の自動録画（初期状態では検知時から10分間）
- 動体検知範囲の可視化（赤枠ボックス表示）
- config.iniファイルによる設定の変更(初回実行時自動生成)
- リアルタイム録画の最大サイズ・録画時間による分割
- LINEもしくはGmailを用いた動体検知時の通知機能

## 動作環境

- Python 3.13.0
- OpenCV 4.10.0
- NumPy 2.1.3

## インストール方法

1. 最新のPythonを<a href="https://www.python.org/downloads/">公式サイト上</a>からインストール。
2. このリポジトリをクローンまたはダウンロード。
3. `install.bat`を実行（必要なパッケージが自動インストールされます）
4. `run.bat`を実行（初回実行時は設定ファイルを生成し終了します）

## 使用方法

1. `config.ini`で設定を変更（必要であれば）
   - `source`: カメラソースの指定（0=内蔵カメラもしくは内蔵カメラがない端末のUSBカメラ、1=内蔵カメラがある端末の外部カメラ。テスト用のmp4動画ファイルを同ディレクトリに配置し拡張子付きファイル名を指定することで動作確認可能）
   - `motion_path`: 動体検知時の録画保存先。
   - `max_duration`: 録画ファイルの最大長さ（分単位）。デフォルトは30分。
   - `max_size`: 録画ファイルの最大サイズ（MB単位）。デフォルトは100MB。
   - `max_record_length`: 動体検知時の録画時間。デフォルトは10分
   - `method`: 通知方法の指定。現在は`Line`と`Email`に対応。デフォルトはLine
   - `token`: LINEによる通知時に必要なLINE Notifyトークンを設定。
   - `notifier_gmail`: Gmailによる通知時に使用する通知側Gmailアドレスを設定。
   - `notifier_password`: 通知側Gmailアドレスのパスワードを設定。
   - `admin_email`: 通知を受け取るEmailアドレスを設定。Gmailアドレス以外も可能。
   - `smtp_server`: 通知側EmailにGmailを使用する場合のSMTPサーバー。Gmail以外を使用する場合は適宜編集。
   - `smtp_port`: SMTPサーバーへ接続する際に使用するポート番号。デフォルトで動作しない場合は2525番、もしくは465番を設定。

2. `run.bat`を実行してプログラムを起動。

3. 終了する場合は映像表示ウィンドウ上で'q'キーを押す。

## 録画ファイルについて

- 通常の録画：実行時の日時をファイル名として保存（YYYY-mm-dd_HH-MM-SS_n.mp4）
- 動体検知時の録画：'motion_'プレフィックス付きで保存（motion_YYYY-mm-dd_HH-MM-SS.mp4）

## 実装予定機能

- [x] 常時録画時の容量や長さによるファイル分割（録画ファイルが100MBに達したら分割, 30分毎に分割など）
- [ ] アーカイブされた録画ファイルが蓄積された際の自動削除機能。
- [ ] UNIX系への移植。将来的にRaspberry Pi OS上での動作を想定。
- [x] 動体検知時のgmailやLINE、もしくはDiscordなどによる通知機能 -> 通知方法の拡張を予定

## ライセンス

[MIT License](LICENSE)に基づいて公開されています。
