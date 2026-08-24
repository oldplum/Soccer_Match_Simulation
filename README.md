# ⚽ Football Match Simulator (基于随机概率链的足球比赛模拟器)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/GUI-Tkinter-green.svg?style=flat" alt="GUI Framework" />
  <img src="https://img.shields.io/badge/Architecture-Single--File-orange.svg?style=flat" alt="Architecture" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat" alt="License" />
</p>

---

## 📖 项目简介

**Football Match Simulator** 是一个基于离散概率链与事件状态机驱动的桌面足球比赛模拟器。通过概率分配、数字判定序列、VAR 裁判介入、加时赛及点球大战机制，还原真实足球比赛的跌宕起伏与不可预测性。

单文件极简设计，基于 Python 原生 Tkinter 开发，零第三方依赖。

> 💡 **致谢**：核心推演规则与概率判定思路参考自 B站 UP主 **[@篮足实录](https://www.bilibili.com/video/BV1KY4y197AH?spm_id_from=333.788.recommend_more_video.-1&trackid=web_related_0.router-related-2589621-k2x2j.1787542669174.435&vd_source=dbe43d353ddc75d68e92456ce5b6b8c7)**。

---

## 🌟 核心特性

- 🎯 **概率推演机会体系**：基于双方填写的实力参数（好机会、中等机会、送礼次数）动态计算实际进攻机会。
- 🎲 **拟真判定链条**：传球被截、射门偏出、扑救脱手、门前补射、角球二次进攻等多级链式判定。
- ⚡ **突发事件与 VAR 裁判系统**：模拟恶劣犯规、黄牌改判红牌、伤停减员及点球判罚，动态影响剩余半场进攻机会。
- ⏱️ **全周期赛制支持**：
  - 常规时间（上下半场，动态伤停补时）
  - 加时赛（上下半场各 15 分钟）
  - 点球大战（前 5 轮定胜负 + 突然死亡阶段）
- 📊 **全维度赛后技术统计**：控球率、射门、射正、危险进攻、角球、点球、红黄牌等一览无遗。
- 💾 **历史战绩与全量回放**：本地 JSON 存档，支持回顾历史比赛完整文字解说与战报。

---

## 📐 核心推演规则

### 1. 机会计算公式
根据双方填写的「好机会」、「中等机会」与对方的「送礼次数」计算总机会（四舍五入且 $\ge 1$）：

$$\text{最终好机会} = \text{基础好机会} + \text{对手送礼} \times \frac{\text{基础好机会}}{\text{基础好机会} + \text{基础中等机会}}$$

$$\text{最终中等机会} = \text{基础中等机会} + \text{对手送礼} \times \frac{\text{基础中等机会}}{\text{基础好机会} + \text{基础中等机会}}$$

- 常规时间机会均分至上下半场（单数时下半场多分 1 次）。
- 加时赛机会按常规时间机会的 $1/4$ 换算。

### 2. 进攻判定机制（单/双数抽取）

| 阶段 | 主队成功条件 | 客队成功条件 | 失败结果 |
| :--- | :--- | :--- | :--- |
| **中等机会组织** | 抽中单数 (1) | 抽中双数 (2) | 进攻失败，球权转换；成功则升级为好机会 |
| **好机会 - 传球** | 单数 (1) | 双数 (2) | 传球被截断 / 配合失误 |
| **好机会 - 射门** | 单数 (1) | 双数 (2) | 射门打偏 |
| **好机会 - 进球** | 双数 (2) 进球 | 单数 (1) 进球 | 门将扑救（触发二次补射/角球/解围判定） |

### 3. 门将扑救与二次进攻
当门将扑救成功时，进入二次判定：
- **解围**：防守方解围，进攻结束。
- **角球**：获得角球进攻（奖励 1 次好机会推演）。
- **补射**：再次射门，判定破门或再次扑救。

### 4. 突发事件 (Foul & VAR)
- 比赛中若连续出现 **8 次相同数字**，触发严重犯规中断。
- 裁判可能出示黄牌/红牌，VAR 可能介入改判点球或判定伤员离场。
- **红牌**：受害方延后追加 1 次好机会。
- **伤退**：犯规方获得 1 次中等机会战术优势。

---

## 🚀 快速上手

### 选项 A：普通玩家（免安装环境）
如果你没有安装 Python，可以直接前往本仓库右侧的 **[Releases](../../releases)** 页面，下载预编译好的 **`FootballSimulator.exe`**，双击即可直接开始游戏！

### 选项 B：开发者（源码运行）
确保已安装 Python 3.8+（无需 `pip install` 任何额外依赖库）：

```bash
# 启动程序
python game.py
```

### 🎮 操作流程：
1. 在主界面配置主客队名称与各项机会数值；
2. 勾选是否开启「加时赛」与「点球大战」；
3. 点击 **【开始比赛】**，随后点击 **【继续 (Next)】** 进行逐回合文字解说推演；
4. 比赛结束后可查看全场技术统计表与历史对战回放。

---

## 📦 自行打包为 Windows 可执行文件 (.exe)

如需自行编译打包，可使用 `pyinstaller`：

```powershell
# 1. 安装打包工具
pip install pyinstaller

# 2. 一键打包（单文件、无黑框控制台、自定义程序名）
pyinstaller -F -w -n "FootballSimulator" game.py
```

打包完成后，生成的独立可执行文件位于 **`dist/FootballSimulator.exe`**。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源协议。
