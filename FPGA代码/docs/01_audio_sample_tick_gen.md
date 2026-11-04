> 历史单模块调试记录，不代表competition_5当前按键/音源/验收状态。当前操作见[使用说明](使用说明.md)。

# 01 - 音频采样节拍发生器

## 功能

`audio_sample_tick_gen` 在系统的 50 MHz 时钟域中产生单周期的 48 kHz
`sample_tick`。它是时钟使能信号，不是一个新的时钟。

下游音频模块的推荐写法：

```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位
    end
    else if (sample_tick) begin
        // 只在新采样点到来时更新音频状态
    end
end
```

## 为什么使用累加器

50 MHz 不能被 48 kHz 整除：

```text
50,000,000 / 48,000 = 1041.666666...
```

因此，相邻两个采样脉冲之间不能始终使用同一个整数周期数。累加器每个系统时钟
增加 `SAMPLE_RATE_HZ`；累加到一次系统时钟频率的总量后产生脉冲并保留余数。

结果是脉冲间隔在 1041 和 1042 个系统时钟之间分配，长期平均每秒正好产生
48,000 个采样脉冲。

## 接口

| 信号 | 方向 | 说明 |
|---|---|---|
| `clk` | 输入 | 50 MHz 系统时钟 |
| `rst_n` | 输入 | 低有效异步复位 |
| `sample_tick` | 输出 | 48 kHz、单系统时钟周期的采样使能脉冲 |

## 参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `CLK_FREQ_HZ` | 50,000,000 | 输入时钟频率 |
| `SAMPLE_RATE_HZ` | 48,000 | 目标音频采样率 |

参数必须满足：

```text
0 < SAMPLE_RATE_HZ < CLK_FREQ_HZ <= 4,294,967,295
```

## 仿真检查项

测试平台将频率同时缩小 1000 倍，以减少仿真时间，但保持相同的分频比例。

测试平台自动检查：

1. 复位期间 `sample_tick` 始终为低。
2. 每个 `sample_tick` 只保持一个系统时钟周期。
3. 相邻脉冲间隔只能为 1041 或 1042 个时钟。
4. 运行 50,000 个测试时钟后必须得到 48 个脉冲。
5. 再次复位后输出立即清零。

使用 Icarus Verilog 时，可在 `sim` 目录执行：

```text
iverilog -g2005 -o tb_tick_sim ../rtl/common/audio_sample_tick_gen.v tb_audio_sample_tick_gen.v
vvp tb_tick_sim
```

正确结果应包含：

```text
PASS: generated 48 ticks with intervals of 1041/1042 clocks.
```

同时会生成 `audio_sample_tick_gen.vcd`，可以用 GTKWave 查看波形。

## 调试思路

如果脉冲总数错误，先检查参数是否写反或单位是否一致；频率参数统一使用 Hz。

如果脉冲连续保持多个周期，检查 `sample_tick` 是否在每个非触发周期明确赋值为
`0`。

如果间隔固定但采样率有偏差，说明实现可能使用了普通整数分频，没有保留除法余数。
