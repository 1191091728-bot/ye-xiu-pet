# 叶修宠物 · 养只你桌宠素材 🐱🎮

> 保留原图人物、服装与面部的 **Q 版像素桌宠**，包含移动、工作、等待及鼠标悬停彩蛋动作。
> 这是 [养只你](https://github.com/1191091728-bot/yangzhini) Demo 的宠物素材项目。

[![Demo](https://img.shields.io/badge/在线体验-Live%20Demo-0E5C50?style=for-the-badge)](https://1191091728-bot.github.io/yangzhini/)
[![类型](https://img.shields.io/badge/类型-像素桌宠%20素材-B89254?style=for-the-badge)](https://github.com/1191091728-bot/ye-xiu-pet)
[![作品集](https://img.shields.io/badge/作品集-Online-0E5C50?style=for-the-badge)](https://1191091728-bot.github.io/)

## 🎯 项目简介

"养只你"的宠物形象——**叶修** Q 版像素桌宠。支持多方向移动、工作、等待、跳跃、挥手和鼠标悬停彩蛋动作。

本仓库不仅包含成品素材，还保留了**完整的 Vibe Coding 生成工作流**（`work/`）：从参考图 → 逐帧生成 → 方向一致性 QA → 精灵图合成，全部过程可复现。

### ✨ 素材清单

| 文件 | 说明 |
|------|------|
| `outputs/ye-xiu-pet/spritesheet.webp` | 成品精灵图（v2） |
| `outputs/ye-xiu-pet/pet.json` | 宠物配置（动作/彩蛋定义） |
| `outputs/ye-xiu-running.gif` / `working.gif` | 移动/工作动画预览 |
| `outputs/ye-xiu-*-contact-sheet.png` | 动作总览图 |
| `work/mo-fei/build_from_reference.py` | 精灵图合成脚本 |
| `work/mo-fei/extract_preview.py` | 预览图提取脚本 |
| `work/mo-fei/run/` | 完整工作流（帧/提示词/QA 验证） |

## 🎨 Vibe Coding 工作流（亮点）

这不是一份"用 AI 画图"的记录，而是一次**可审计的 AI 内容生产**：

1. **参考锚定**：`run/references/reference-01.jpg` 保留原图人物特征
2. **逐帧生成**：`run/frames/` 按动作分帧（idle / running / jumping / waving / waiting / failed / review）
3. **方向一致性 QA**：`run/qa/direction-blind-*` 盲测验证 8 方向朝向正确性
4. **提示词迭代**：`run/prompts/` 保留每一轮提示词与 row-retries 修复记录
5. **最终合成**：`build_from_reference.py` 合成 spritesheet 并导出 webp

## 🚀 使用

```bash
# 合成精灵图（从参考图 + 帧目录）
python3 work/mo-fei/build_from_reference.py

# 提取预览
python3 work/mo-fei/extract_preview.py
```

## 📬 联系

📧 1191091728@qq.com · 嘿哈土豆 · 从 PM 到 FDE 的路上
