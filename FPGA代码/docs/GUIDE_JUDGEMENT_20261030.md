# 2026-10-30 辅助演奏评分修订

本文件记录当天较早的按键过滤修订。后续已加入提前240ms蓝灯，并将Excellent/Good扩大为±150ms/±300ms；当前功能以`BLUE_REACTION_GUIDE_20261030.md`及`TIMED_GUIDE_20261029.md`为准。下文±100ms/±220ms是当时版本的历史参数。

工程基础：competition_9_5。旧的原始MIDI接入可在仿真中复现：C4在拍点第一次Note On得到Excellent；未松键时重复发送C4 Note On，会再增加Wrong；密集同键曲谱还可能被误领下一拍的分数。实物键盘是否实际重发了该消息，仍需MIDI记录确认；本次先修复代码中可复现的重复输入漏洞。

## 一次物理按键只评分一次

新增`guide_midi_input_filter.v`，只用于评分输入，持续维护C2～C6的49键按下状态。第一次Note On作为有效起音；未收到该键Note Off时的重复Note On被忽略，不改变Excellent、Good、Wrong、连击或下一音。Note On力度0等同松键。收到真实松键后再次按下，就重新接受；没有设置阻挡全键盘或快速连音的固定冷却时间。

每个音高独立维护状态，因此和弦、不同键接续、100ms间隔的同键重弹均正常。CC64踏板不改变物理按住状态；通道0的CC120/CC123清除按住状态。停止/开始评分不清空真实按键状态，避免一直按住时重播被误判为新起音。键盘断电丢失Note Off的问题不在本次修改范围。

## 更适合实际演奏的时间窗口

| 判定 | 当前范围 | 原范围 |
| --- | --- | --- |
| Excellent | 正确音，误差−100ms～+100ms，含边界 | ±80ms |
| Good | 正确音，误差±220ms内，超出Excellent范围 | ±180ms |
| Miss | 目标超过+220ms仍未命中 | +180ms后 |
| Wrong | 有效的新起音无法匹配窗口内的待弹同音事件 | 规则保持 |

这些窗口围绕曲谱真实拍点，黄灯仍按500ms真实剩余时间渐灭，到拍熄灭。同一音的重叠窗口仍选择最近的未评分事件，等距优先较早者；一次起音最多命中一个事件。提前250ms按目标音仍会Wrong；按错其他音也会Wrong。被忽略的重复MIDI消息不算新起音，真正松开再按错仍正常扣分。

计分继续为Excellent100分、Good70分、Wrong额外扣5分，按全曲有效音符数归一化；SSS/SS/S/A/B/C分档保持原规则。未改变音频、AUTO、500ms渐灭、LED引脚或GRB协议、App、ESP32与SD文件格式。

## 上板检查

1. 重新综合、布线、检查时序并生成新码流；2026-10-29的FS不包含本次改动。
2. 小星星GUIDE中，每次完整按下/松开应只给一个判定；一直按住不能得下一音的分。
3. 连续同键必须松开再按，稍早/稍晚可以Good；不同键组成的和弦逐键判定。
4. 故意按错一个键，Wrong增加一次；按住不继续增加，松开再按错才增加下一次。
5. 踏板踩住时松键重弹，仍应接受新起音；AUTO和自由演奏照常验证。

## 验证入口

`python -B tools/check_timed_guide.py --output ../../tmp/c95_guide_judgement_20261030/after --only input,timed,player,light,led_fade --timeout 180`

`sim/tb_guide_input_realism.v`以真实MIDI字节解析器接入评分，覆盖重复消息、密集同键、力度0松键、错音重按、踏板、和弦及通道/音域过滤。参数`USE_FILTER=0`可复现旧接入导致的Excellent后Wrong。其余测试覆盖计分、判定边界、PNO加载、AUTO以及实体灯序列输出。

本次源码备份：`D:/gowin_projects/tmp/competition_9_5_before_guide_judgement_20261030.zip`。仿真输出：`D:/gowin_projects/tmp/c95_guide_judgement_20261030/after`。旧impl/FS保留为此前版本，本次仿真不生成新码流、不代表布局布线时序结果。
