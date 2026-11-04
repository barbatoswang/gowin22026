# 手机控制SOUND八参数

日期：2026-11-01。基础为当前competition_9_5，当前App使用FPGA_Control_SoundUI_Fixed.aia（2.5.1-sound-fix）。App启动白屏修复不改变本协议或FPGA源码。

## 参数编号

| 编号 | SOUND | 范围 | 数据含义 |
| --- | --- | --- | --- |
| 0 | VOL | 0～32 | 原总音量档位 |
| 1 | OD | 0～4 | 原过驱档位 |
| 2 | CHO | 0～32 | 合唱深度 |
| 3 | REV | 0～32 | 混响深度 |
| 4 | DLY | 0～32 | 回声深度 |
| 5 | PIT | −12～+12 | 有符号半音，8位补码 |
| 6 | VIB | 0～8 | 原颤音档位 |
| 7 | REL | 0～8 | 原释放档位与release_step_from_level映射 |

## 线上协议

仍为115200/8N1、ASCII命令行，ESP32把每次BLE写入规范为一条LF结尾的UART命令。

- 设置：`SC=i,HH`，例如VOL24为`SC=0,18`，PIT−12为`SC=5,F4`。
- 设置确认：`ACK:Ci=HH`，例如`ACK:C0=18`。App精确匹配参数编号和值，重复旧ACK不推进下一项。
- 读取：`SCQ=TT`，TT为App生成的两位十六进制令牌。
- 读取回复共三行：`CFG:TT:0:XXXXXXXX`、`CFG:TT:1:XXXXXXXX`、`CFG:TT:END`。
- 无效参数命令：`CFG:ERR`，不写寄存器。

两段数据分别为VOL/OD/CHO/REV和DLY/PIT/VIB/REL，按显示顺序每值两位十六进制，例如出厂初始值为`18000000`和`00000000`。FPGA收到查询时冻结全部64位，后续旋钮变化不会把两段拼成不同时间的状态。

请求最长7字符，最长回复正文17字符，加NUL18字节，适配当前MTU23下的20字节BLE有效载荷及ESP32 ResponseLines上限。无需修改ESP32脚本或服务UUID。

App参数接收端支持原始UART分段与完整行通知，可重组1～20字节分段、连续多帧及LF/CRLF/NUL分隔。沿用`try2.py`或`ble_song_bridge.py`时均无需为本协议更新透传脚本。

## FPGA改动

参数模块位于song_title_link的普通命令出口与原legacy/song解码器之间。标题协议保持原路径；VOL、TRANS、SB/SD/SE、PA/PG/PS/SQ等非SC命令按行转发给原模块。为接收上游的100MHz短突发，使用256字节小FIFO；过长legacy行保持过长拒绝标记，不能截断成有效命令。

新回复通过另一层uart_reply_mux与原回复合流，按整行锁定，不在LF之前交错。查询发送/回压期间，普通停止命令仍可在输入侧继续转发。输入FIFO过载标记保留供诊断；App正常停等请求不会形成无界突发。

设置脉冲接入原encoder_*八项寄存器。写入优先级只覆盖被指定的参数；物理旋钮的选项与增减规则保持。PIT同步更新原PCM兼容控制寄存器，REL同步更新原释放步长。远程设置会显示SOUND浮窗并高亮被写的项目，读取不会写参数或改变旋钮选项。

未改32复音、波形/频谱、LED节奏评分、音色算法、引脚、时钟约束、曲谱或SD格式。原VOL/TRANS命令继续兼容。

## 验证

`tools/check_sound_parameters.py`生成一个轻量测试壳，直接嵌入生产top中的原旋钮/参数寄存器always块和release_step_from_level函数，避免DDR3/IP模拟。测试八项真实映射、正负移调、释放步长、SOUND浮窗、物理旋钮和旧VOL/TRANS控制。

`sim/tb_sound_parameter_link.v`验证首次冷查询、八项边界、拒绝无效/越界命令、CRLF与大小写、查询冻结、回复回压、旧曲谱命令及停止兼容。

检查输出：`D:/gowin_projects/tmp/c95_sound_controls_20261101/final_rtl`。全工程HDL语义及原MIDI输入/曲谱播放仿真记录在`tmp/c95_sound_controls_20261101/semantics`。

按用户要求，仅更新源码并运行语法/逻辑仿真，**没有运行Gowin综合或布线，没有生成/烧录新FS**。布局布线资源与时序必须由重新实现确认。

修改前工程文件备份：`tmp/competition_9_5_before_sound_control_20261101.zip`。App原图标版AIA保留。
