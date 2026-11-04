# competition_7 曲谱与工具

PNO1小端格式：4字节PNO1、LE16事件数、LE16保留0；每事件LE32起始毫秒、LE16时长、8bit键号0～48、8bit力度0～127。本地曲谱最多2048事件、16392字节；原手机上传和SAVESLOT仍为1024/8200。事件按起始时间排序，最多4个重叠发声音符；同一开始时刻不能重复音高，持续时间1～65535，结束时间不能溢出32位。力度0表示静默事件。录音槽的空删除负载仅在录音事务内允许，不作为普通SONG播放。

SD目录SONGS.CAT维持最多31曲、16字节固定记录：LE16文件编号与14字节ASCII标题。文件SONGxxx.PNO的xxx对应目录编号。

原4首单音曲目保留；新增SONG005.PNO / CHORD STUDY，192个事件、48组四音和弦，用于验证扩容和手动跟弹。四音自动曲谱使用全部4声部。

- python tools/csv_to_pno.py 输入.csv --output SONG005.PNO：列start_ms,duration_ms,key_index,velocity；保留和弦，超容量/5音重叠/无效事件报错。
- python tools/midi_to_pno.py 输入.mid --list-tracks：列出轨道；--track N --output 文件转换该轨道，保留最多4个重叠音，不再挑一个最响音或静默截成128事件。
- python tools/csv_to_catalog.py src/songs/songs.csv --output SONGS.CAT：生成目录。
- python tools/check_project.py：核对依赖、模块唯一性与所有PNO1。
- python tools/export_app_scores.py --output-dir 新目录：导出原手机App兼容的单音≤128事件JSON；四音扩展示例不进入该旧App目录。不会上传外部服务。

手机保持原协议与界面；在本地FPGA增加2048/4音并不使旧App自动获得编辑/传送新格式的能力。可通过SD直接使用扩展曲谱。录音导入/导出工具与槽格式见[录音与安全存储](录音与安全存储.md)。
