# 保存完成后SAVING/BUSY锁住修复

当前App：FPGA Smart Piano 2.6.2。基础工程仍为competition_9_5。

## 已确认的故障链

用户报告TWINKLE自动播放停在App的SD:SAVING，而FPGA显示SAVED；退出重进后上传得到ERR:BUSY。保存派发代码存在一拍竞态：

1. SD完成边沿时，top把`packed_release`置1，同时把`save_command_sent`清0。
2. packer在下一拍才看到release。在这一拍，top仍看到上一份快照的`packed_ready=1`，又满足`!save_command_sent`，错误地派发第二次保存。
3. 幽灵保存完成时，快照已释放，完成分支不再清`save_command_sent`。下一首快照准备好后不能派发，`packed_busy`持续为1。
4. MQ优先检查busy，因而即使上一次保存结果是SAVED，仍返回SD:SAVING。新MB请求也会收到ERR:BUSY。退出手机App不会复位FPGA的这些寄存器。

在当前生产top原样提取的派发代码、真实song_backup_packer和song_title_link上，使用模拟SD完成事件复现了“重复派发 -> 下一次锁住 -> SD:SAVING -> ERR:BUSY”的完整序列。此前独立SD核心与App模型没有覆盖这个顶层完成握手。

修复在派发条件增加`!packed_release`：释放旧快照的这一拍不能再派发。未改变文件格式、存储核心、音频、MIDI、LED、引脚或约束。当前SD文件不需要因此格式化或重建。

## App修复

- SAVE_WAIT保留可用的“结束等待（设备继续保存）”。点击只结束App等待与自动续播，不发送停止/复位SD写卡命令；明确提示尚未确认保存结果。迟到的SD:SAVED不会意外自动开播。
- 自动播放仍沿用“同步所选曲谱、同ID更新SD、确认保存后PA”的行为。手机不是按歌名直接远程选择SD已有文件；因此已存TWINKLE也会再次同步。
- 当前APK的ConnectMatchingName实现中，名称匹配回调调用ConnectWithAddress，外层扫描回调又调用一次connectGatt。用户手机日志可见同一次连接出现多份GATT客户端。
- App改用普通StartScanning，定时检查DeviceList中确切的YD-FPGA条目，停止扫描后仅调用一次ConnectWithAddress。不硬编码MAC；连接中及已连接时禁止重复连接，异常/超时恢复控件。
- 保持当前居中布局、齿轮、VIB0～32步进4、顶部统一应用、曲谱下载与原单BLE组件。未更换BLE扩展或ESP32程序。

## 更新与验证

先用更新后的competition_9_5.gprj自行综合、布线、检查时序、生成并烧录新码流。只安装App不能修复旧FPGA中已经锁住的状态。本轮没有运行综合、布线、烧录或实体SD写入。

App本地源码包为app/FPGA_Control_SoundUI_Fixed.aia。另提供app/FPGA_Control_SoundUI_Fixed3.aia，包名与用户当前手机APK一致。沿用Fixed3工程名及原App Inventor签名构建，可覆盖安装并保留原包数据；导入时若网页版同名工程存在，可先将旧网页工程重命名备份，再导入新的Fixed3文件，不要卸载手机上的旧App。

1. 关闭旧App，启动2.6.2，单击连接；等待连接完成。
2. 选择TWINKLE自动播放，结束后重复三次。
3. 在两首曲子间切换，再对已保存的同一首执行上传保存与自动播放。
4. 保存等待可点击结束等待，界面应恢复，FPGA继续完成保存；此时App不会宣称已保存或自行开播。
5. 断开重连后重复测试；确认不再持续ERR:BUSY。原卡歌曲无需清空。

## 检查记录与边界

- `tools/check_song_save_dispatch.py --expect-old-bug`：修改前代码复现故障。
- 同工具修复后通过20次连续握手，验证每次只派发一次、快照释放后MQ返回SAVED且下一次MB正常。
- `app/check_song_reliability.py`：7项，包括同一目标重复广播、连接超时/同步错误、SD等待退出不写UART、不提前开播、BUSY后无重试风暴。
- `app/check_sound_ui.py`：16项参数与接口检查、7项原曲谱模型回归。
- 全工程HDL语义、原MIDI输入和曲谱播放集成回归通过。

RTL测试中SD完成事件由仿真驱动，并非20次真实SD写入。新APK尚未编译或实机验证；真实BLE、SD及新版时序仍需更新后确认。

原APK反编译和该App专属手机日志：tmp/song_busy_20261101/apk与phone。旧故障/修复仿真：同目录old_reproduction、fixed_dispatch。修改前源码与AIA：output/song_busy_fix_20261101/before_fix.zip。
