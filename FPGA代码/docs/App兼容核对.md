# 手机 App 与 competition_10_5 兼容核对

核对对象为用户提供的 `FPGA_Control_SoundUI_Fixed3 (1).apk.1`，文件内容是有效 APK：FPGA Smart Piano 2.7.0，版本码 15，包名 `appinventor.ai_1491876266.FPGA_Control_SoundUI_Fixed3`。SHA-256：`16cd7aca28621e2b50b84306bda8968c4868842f1a7e926c397d5f8e20af6d1d`。原包未改动、未改签、未安装。本页记录清单、DEX 字节码及反编译控制流程的只读核对；不代表 Android/BLE/实体 SD 已实测。

## 删曲事务

Music 页的“从 FPGA SD 删除所选曲谱”冻结所选歌曲的 ID 和标题，弹出确认后将 `DELETE_SD` 和这份选择快照返回首页。手机本地曲谱保留。首页校验整数 ID 范围并转换为 8 位十六进制。

| App 发出／接收的正文 | FPGA 行协议 | 含义 |
| --- | --- | --- |
| `MX=IIIIIIII` | 正文加 LF | 请求删除此 ID 的上传曲库歌曲 |
| `ACK:X=IIIIIIII` | 正文加 LF，15 字节 | 已接受事务，尚未完成 SD 删除 |
| `MZ=IIIIIIII` | 正文加 LF | 轮询同一 ID 的删除结果 |
| `DX:IIIIIIII:B` | 正文加 LF，14 字节 | 正在操作，继续等待 |
| `DX:IIIIIIII:C` / `:W` | 正文加 LF | 目录初始化／没有对应结果，继续等待 |
| `DX:IIIIIIII:D` | 正文加 LF | 双副本空槽提交成功，删除完成 |
| `DX:IIIIIIII:N` | 正文加 LF | 上传曲库中不存在该 ID |
| `DX:IIIIIIII:E` 或 `ERR:*` | 正文加 LF | 错误，不报告删除成功 |

App 按 ID 匹配 ACK 和结果，只在 DELETE_WAIT 收取结果。它逐字符重组通知，支持分段和连续回复，通过固定正文长度或分隔符分派，缓冲上限 64 字符。ACK 正文 14 字符、结果正文 13 字符，与 RTL 一致，均适合 20 字节 BLE 有效载荷。事务定时器 100 ms；结果轮询间隔 1 秒，应答等待 3 秒、最多重试 3 次，整个结果等待上限 60 秒。超时文本说明设备可能仍在操作，不把超时当作删除完成。

FPGA 保留幂等重试和旧结果保护：当前事务同 ID 的重复 MX 只返回接受应答，不重复发起删除；不同 ID 返回忙。进入新的同 ID 事务后，必须观察到本次忙状态再释放等待，不把上次成功误认成本次成功。删除对空槽写两份合法空记录，防止重启回退到旧副本使歌曲重新出现。失败时保留错误状态。此操作不改 FAT 占位文件布局，不删除预置曲或 RECORDING 录音。

10_5 额外将 Loop 页、录制、播放、命令交接与删曲互锁；删除期间暂停新的歌曲启动、循环操作和上传。删除成功后使已加载的同 ID 手机曲谱失效，不能继续播放已删除的缓存。真实 RTL 仿真覆盖忙拒绝、同沿启动、跨时钟完成间隙、重试、重启可见性和存储错误。

## 连接与断开

App 使用同一个 Nordic UART BLE 服务：`6E400001-B5A3-F393-E0A9-E50E24DCCA9E`；写入特征 `6E400002-…`，通知特征 `6E400003-…`。扫描 `YD-FPGA`，连接中设置 LinkBusy，避免重复连接。连接完成注册字符串通知，失败／超时恢复控件。用户断开时先记录当前是否有未确认事务，再停止本地传输和参数轮询，最后调用 BLE Disconnect；断开回调清理连接状态。未确认的保存／删除有专门提示，不强行中断 FPGA 正在提交的 SD 写事务。

App 的 BLE 写入正文不附 LF。既有工程协议约定由 ESP32 将每次 BLE 写入规范为 LF 结尾 UART 命令，并将 FPGA 回复透传到通知特征。App 断开回调的界面文字称 ESP32 会请求 FPGA 停止，但 APK 自身没有在断开回调中直接发送停止命令。自动停止要求 ESP32 在 BLE 断开事件中向 FPGA 发送 `PS\n`；FPGA 已支持该命令。

用户于 2026-11-04 确认：BLE 程序在另一台电脑，已固化到 ESP32；本次只处理 FPGA 端。因此沿用现有 ESP32 固件，不将取得或修改透传代码作为交付前置条件。APK 静态核对和 FPGA 仿真记录在本版证据中，BLE 实机操作不计为本轮已验证项目。

## 证据

交付包 `verification/apk/apk_contract.json` 绑定原 APK 和两个 DEX 的 SHA，`protocol_bytecode.txt` 保存相关事件及命令构造的字节码。仓库复核入口为 `scripts/audit_competition_10_5_apk.py`（Androguard 4.1.4，独立临时依赖目录）。FPGA 用例包括 `tb_download_delete_link`、`tb_download_delete_storage`、`tb_delete_visibility`、`tb_delete_top_race`、`tb_bluetooth_song_link` 及完整 Loop Station 回归。
