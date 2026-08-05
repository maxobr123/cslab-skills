# cslab-skills

面向 AI 的 CSLab 算法模块开发 skills 套件:让 AI 按平台契约(自有变量、自有
继承方法、模板注入规则)编写/修改 `domain/` 下的算法模块。

## 四层架构

```
L0 方法论(流水线,不是 skill 文件)
    契约侦察 → 提炼成 skill → 盲测验收(复写参考实现)→ 偏差归因 → 迭代
    对每个模块族重复执行;溯源材料存 provenance/

L1 工作流入口(族无关)
    cslab-module-develop      厘清需求 → 定位模板 → 推导契约 → 路由族包 → 验证 → 登记

L2 平台通用契约(所有族共享,由模板系统+调度框架决定)
    cslab-modulet-api         模板系统接口:分类/列表/属性/pyTemp/CRUD、算法槽位
    cslab-module-contract     运行契约:同名注入、startFun、输出三通道、feedback
    cslab-module-verify       取数接口、环境约束、验证检查单

L3 模块族包(每族一组,按 L0 流水线增量生产)
    cslab-operation-unit-skeleton 通用稳态单元骨架:契约取证、Run、端口与失败回滚
    cslab-operation-flashtank FlashTank 专用骨架:MRO、变量词汇、*_BaseOn、暖启动
    cslab-operation-flash     闪蒸计算契约(Flash 家族方法签名)
    cslab-operation-phy-prop  统一物性入口契约(phy_prop 标量/矩阵与属性总表)
    (动态/控制/设计/化原等族包待建)
```

## 目录

- `skills/` — 各 SKILL.md,按上表分层
- `provenance/` — 溯源材料:skill 事实断言的证据来源与已知边界,见其 README
- `examples/` — 本地参考实现与试验代码(gitignored,不入库)

## Codex 项目安装与同步

- 本仓库的 `skills/` 是 Skill 唯一管理源和 Git 提交位置。
- 主项目 `D:/project/cslab_onedrive/.agents/skills/` 是 Codex 自动发现的运行副本。
- 修改 Skill 时先更新本仓库并完成校验，再同步到 `.agents/skills/`；若在运行副本中
  临时修订，必须回写本仓库后再提交，禁止形成两套长期分叉内容。
- 提交前逐个比较同名 `SKILL.md` 的 SHA256，并确认目录集合一致；推送本仓库后才算完成。

## 维护约定(活文档纪律)

1. **测试**:改 skill 或平台升级后,跑盲测验收(只给 skills + 需求规格,复写
   族参考模块,与参考实现对比归因),不达标先修 skill。
2. **触发器**:平台发版改契约 / 新增模块族 / 盲测失败 / 实际使用中 AI 写错
   代码且归因为 skill 缺失或歧义——四类事件触发维护,其余时间不动。
3. **溯源**:新增事实断言必须同步 `provenance/`(来源报告或代码位置);
   无法验证的断言在 skill 内明确标注"未验证"。
4. **瘦身**:skill 正文只放契约(词汇表/签名/规则/模板),不放叙述与出处;
   易变内容(词汇表、签名)归族包,稳定内容(注入机制、输出通道)归 L2。
