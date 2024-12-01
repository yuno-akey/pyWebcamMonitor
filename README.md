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
  </tr>
</table>

動体検知機能付きの監視カメラプログラムです。カメラからの映像を常時録画しながら、動体を検知した場合は別ファイルとして保存します。

## 機能

- カメラ映像のリアルタイム表示と録画
- 動体検知時の自動録画（検知から10分間）
- 動体検知範囲の可視化（赤枠ボックス表示）
- config.iniファイルによる設定の変更(初回実行時自動生成)

## 動作環境

- Python 3.13.0
- OpenCV 4.10.0
- NumPy 2.1.3

## インストール方法

1. このリポジトリをクローンまたはダウンロード
2. `install.bat`を実行（必要なパッケージが自動インストールされます.）

## 使用方法

1. `config.ini`で設定を変更（必要であれば）
   - `source`: カメラソースの指定（0=内蔵カメラ, 1=外部カメラ. または動画ファイル名）
   - `motion_path`: 動体検知時の録画保存先

2. `run.bat`を実行してプログラムを起動

3. 終了する場合は映像表示ウィンドウ上で'q'キーを押す

## 録画ファイルについて

- 通常の録画：実行時の日時をファイル名として保存（YYYY-mm-dd-HH-MM-SS.mp4）
- 動体検知時の録画：'motion_'プレフィックス付きで保存（motion_YYYY-mm-dd-HH-MM-SS.mp4）

## 実装予定機能

- 常時録画時の容量や長さによるファイル分割（録画ファイルが100MBに達したら分割, 30分毎に分割など）
- アーカイブされた録画ファイルが蓄積された際の自動削除機能
- 動体検知時のgmailやLINE、もしくはDiscordなどによる通知機能<sub>~~面倒くさい......~~</sub>

## ライセンス

[MIT License](LICENSE)に基づいて公開されています。