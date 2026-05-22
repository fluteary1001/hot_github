const pptxgen = require("pptxgenjs");

// Create presentation
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Claude Code";
pres.title = "claw-code Design";

// Color palette matching HTML dark theme
const colors = {
  bgPrimary: "0D1117",
  bgSecondary: "161B22",
  bgTertiary: "21262D",
  textPrimary: "C9D1D9",
  textSecondary: "8B949E",
  accentPrimary: "58A6FF",
  accentSecondary: "1F6FEB",
  accentSuccess: "3FB950",
  border: "30363D"
};

// Slide 1: Title Slide
let slide1 = pres.addSlide();
slide1.background = { color: colors.bgPrimary };

// Add decorative accent bar at top
slide1.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.08,
  fill: { color: colors.accentSecondary }
});

// Title
slide1.addText("claw-code Design", {
  x: 0.5, y: 2.0, w: 9, h: 1.2,
  fontSize: 48, fontFace: "Arial", bold: true,
  color: colors.textPrimary, align: "center"
});

// Subtitle
slide1.addText("设计说明书", {
  x: 0.5, y: 3.2, w: 9, h: 0.6,
  fontSize: 24, fontFace: "Arial",
  color: colors.textSecondary, align: "center"
});

// Generation time
slide1.addText("生成时间: 2026-05-17 22:58:26", {
  x: 0.5, y: 4.8, w: 9, h: 0.4,
  fontSize: 14, fontFace: "Arial",
  color: colors.textSecondary, align: "center"
});

// Slide 2: Table of Contents
let slide2 = pres.addSlide();
slide2.background = { color: colors.bgPrimary };

slide2.addText("目录", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

const tocItems = [
  "1. 项目概述",
  "2. 系统架构设计",
  "3. 设计模式分析",
  "4. 关键流程图",
  "5. 核心组件详解",
  "6. 数据流分析",
  "7. 技术亮点与创新点"
];

slide2.addText(tocItems.map((item, i) => ({
  text: item,
  options: { bullet: true, breakLine: true, fontSize: 20, color: colors.textSecondary }
})), {
  x: 1, y: 1.2, w: 8, h: 4
});

// Slide 3: Section 1 - Project Overview
let slide3 = pres.addSlide();
slide3.background = { color: colors.bgPrimary };

slide3.addText("1. 项目概述", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

slide3.addText("项目定位", {
  x: 0.5, y: 1.0, w: 9, h: 0.5,
  fontSize: 22, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

slide3.addText([
  { text: "Claw Code 是一个开源的 Rust 实现的 CLI Agent Harness", options: { breakLine: true } },
  { text: "面向自主编码智能体（claw）的程序化协调框架", options: { breakLine: true } },
  { text: "Claude Code 的公开 Rust 移植版本", options: { breakLine: true } },
  { text: "实现从指令下发到代码生成的全自动化闭环", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 16, color: colors.textSecondary } })), {
  x: 0.5, y: 1.6, w: 9, h: 2
});

slide3.addText("核心功能", {
  x: 0.5, y: 3.2, w: 9, h: 0.5,
  fontSize: 22, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

slide3.addText([
  { text: "CLI Agent 会话管理", options: { breakLine: true } },
  { text: "多 Provider 支持（Anthropic/OpenAI/代理）", options: { breakLine: true } },
  { text: "Mock Parity Harness 行为一致性验证", options: { breakLine: true } },
  { text: "插件与 Hook 系统", options: { breakLine: true } },
  { text: "权限与沙箱控制", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 16, color: colors.textSecondary } })), {
  x: 0.5, y: 3.8, w: 9, h: 1.8
});

// Slide 4: Section 2 - System Architecture
let slide4 = pres.addSlide();
slide4.background = { color: colors.bgPrimary };

slide4.addText("2. 系统架构设计", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

slide4.addText("三层系统架构", {
  x: 0.5, y: 1.0, w: 9, h: 0.5,
  fontSize: 22, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

// Architecture layers
const layers = [
  { name: "人类接口层 (Discord)", desc: "人类通过 Discord 频道下达指令", y: 1.6 },
  { name: "工作流编排层 (OmX)", desc: "短指令 → 结构化执行", y: 2.4 },
  { name: "事件路由层 (clawhip)", desc: "监控 git/tmux/GitHub 事件", y: 3.2 },
  { name: "执行层 (Claw Code)", desc: "API / Runtime / Commands / Plugins", y: 4.0 }
];

layers.forEach((layer, i) => {
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: layer.y, w: 9, h: 0.7,
    fill: { color: i % 2 === 0 ? colors.bgSecondary : colors.bgTertiary },
    line: { color: colors.border, width: 1 }
  });
  slide4.addText(layer.name, {
    x: 0.7, y: layer.y + 0.1, w: 4, h: 0.25,
    fontSize: 14, fontFace: "Arial", bold: true,
    color: colors.accentPrimary
  });
  slide4.addText(layer.desc, {
    x: 0.7, y: layer.y + 0.35, w: 8, h: 0.25,
    fontSize: 12, fontFace: "Arial",
    color: colors.textSecondary
  });
});

// Slide 5: Module Structure
let slide5 = pres.addSlide();
slide5.background = { color: colors.bgPrimary };

slide5.addText("模块划分 (9 个 Crate)", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

const modules = [
  ["api", "LLM Provider API 客户端抽象层"],
  ["commands", "CLI 命令定义与分发"],
  ["runtime", "核心运行时：权限、Bash、文件操作"],
  ["plugins", "插件系统与 Hook 执行"],
  ["compat-harness", "兼容性测试框架"],
  ["mock-anthropic-service", "确定性 Mock 服务"]
];

slide5.addTable(modules.map(m => [m[0], m[1]]), {
  x: 0.5, y: 1.0, w: 9, h: 4,
  colW: [2.5, 6.5],
  border: { pt: 1, color: colors.border },
  fill: { color: colors.bgSecondary },
  fontFace: "Arial",
  fontSize: 14,
  color: colors.textSecondary
});

// Slide 6: Section 3 - Design Patterns
let slide6 = pres.addSlide();
slide6.background = { color: colors.bgPrimary };

slide6.addText("3. 设计模式分析", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

const patterns = [
  { name: "状态机模式", desc: "每个 Worker 具有显式的生命周期状态" },
  { name: "策略模式", desc: "Provider trait 实现多 LLM 适配" },
  { name: "观察者模式", desc: "clawhip 事件路由器实现事件驱动" },
  { name: "模板方法模式", desc: "Hook 系统 pre/post 执行骨架" },
  { name: "Harness 模式", desc: "Mock Parity 行为一致性验证" },
  { name: "门面模式", desc: "API Client 统一接口隐藏复杂性" }
];

patterns.forEach((p, i) => {
  const row = Math.floor(i / 2);
  const col = i % 2;
  const x = 0.5 + col * 4.7;
  const y = 1.0 + row * 1.3;

  slide6.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 4.5, h: 1.1,
    fill: { color: colors.bgSecondary },
    line: { color: colors.border, width: 1 }
  });
  slide6.addText(p.name, {
    x: x + 0.15, y: y + 0.1, w: 4.2, h: 0.4,
    fontSize: 16, fontFace: "Arial", bold: true,
    color: colors.accentPrimary
  });
  slide6.addText(p.desc, {
    x: x + 0.15, y: y + 0.55, w: 4.2, h: 0.4,
    fontSize: 12, fontFace: "Arial",
    color: colors.textSecondary
  });
});

// Slide 7: Section 4 - Key Flows
let slide7 = pres.addSlide();
slide7.background = { color: colors.bgPrimary };

slide7.addText("4. 关键流程图", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

slide7.addText("会话启动与健康检查流程", {
  x: 0.5, y: 1.0, w: 9, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

const flowSteps = [
  "用户执行 claw",
  "检查已保存会话",
  "执行 /doctor 健康检查",
  "加载配置文件",
  "初始化权限系统",
  "进入交互式 REPL"
];

flowSteps.forEach((step, i) => {
  const y = 1.6 + i * 0.55;
  slide7.addShape(pres.shapes.OVAL, {
    x: 0.5, y: y, w: 0.4, h: 0.4,
    fill: { color: colors.accentSecondary }
  });
  slide7.addText(String(i + 1), {
    x: 0.5, y: y + 0.05, w: 0.4, h: 0.3,
    fontSize: 14, fontFace: "Arial", bold: true,
    color: colors.textPrimary, align: "center"
  });
  slide7.addText(step, {
    x: 1.1, y: y + 0.05, w: 8, h: 0.3,
    fontSize: 16, fontFace: "Arial",
    color: colors.textSecondary
  });
  if (i < flowSteps.length - 1) {
    slide7.addShape(pres.shapes.LINE, {
      x: 0.7, y: y + 0.4, w: 0, h: 0.15,
      line: { color: colors.accentPrimary, width: 2 }
    });
  }
});

// Slide 8: Section 5 - Core Components
let slide8 = pres.addSlide();
slide8.background = { color: colors.bgPrimary };

slide8.addText("5. 核心组件详解", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

slide8.addText("API 客户端层 (api crate)", {
  x: 0.5, y: 1.0, w: 9, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

slide8.addText([
  { text: "client.rs - 统一客户端接口", options: { breakLine: true } },
  { text: "http_client.rs - HTTP 传输层", options: { breakLine: true } },
  { text: "sse.rs - SSE 流式响应解析", options: { breakLine: true } },
  { text: "providers/ - Provider trait 实现", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 14, color: colors.textSecondary } })), {
  x: 0.5, y: 1.5, w: 4.5, h: 1.5
});

slide8.addText("运行时层 (runtime crate)", {
  x: 5, y: 1.0, w: 4.5, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

slide8.addText([
  { text: "approval_tokens.rs - 审批令牌", options: { breakLine: true } },
  { text: "bash.rs - Bash 命令执行", options: { breakLine: true } },
  { text: "compact.rs - 上下文压缩", options: { breakLine: true } },
  { text: "config.rs - 配置管理", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 14, color: colors.textSecondary } })), {
  x: 5, y: 1.5, w: 4.5, h: 1.5
});

slide8.addText("插件系统 (plugins crate)", {
  x: 0.5, y: 3.2, w: 4.5, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

slide8.addText([
  { text: "hooks.rs - Hook 执行引擎", options: { breakLine: true } },
  { text: "lib.rs - 插件注册与发现", options: { breakLine: true } },
  { text: "test_isolation.rs - 测试隔离", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 14, color: colors.textSecondary } })), {
  x: 0.5, y: 3.7, w: 4.5, h: 1.2
});

slide8.addText("Mock Parity 系统", {
  x: 5, y: 3.2, w: 4.5, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

slide8.addText([
  { text: "mock-anthropic-service", options: { breakLine: true } },
  { text: "compat-harness", options: { breakLine: true } },
  { text: "12 个脚本化测试场景", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 14, color: colors.textSecondary } })), {
  x: 5, y: 3.7, w: 4.5, h: 1.2
});

// Slide 9: Section 6 - Data Flow
let slide9 = pres.addSlide();
slide9.background = { color: colors.bgPrimary };

slide9.addText("6. 数据流分析", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

slide9.addText("请求流（用户/智能体 → LLM）", {
  x: 0.5, y: 1.0, w: 9, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

const requestFlow = [
  "用户输入 / 智能体生成",
  "Commands 层（命令解析）",
  "Runtime 层（上下文组装）",
  "API Client 层（Provider 选择）",
  "LLM Provider",
  "SSE 流式响应",
  "工具执行与循环"
];

requestFlow.forEach((step, i) => {
  const y = 1.5 + i * 0.5;
  slide9.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: y, w: 3.5, h: 0.4,
    fill: { color: colors.bgSecondary },
    line: { color: colors.border, width: 1 }
  });
  slide9.addText(step, {
    x: 0.6, y: y + 0.05, w: 3.3, h: 0.3,
    fontSize: 12, fontFace: "Arial",
    color: colors.textSecondary, align: "center"
  });
  if (i < requestFlow.length - 1) {
    slide9.addShape(pres.shapes.LINE, {
      x: 2.25, y: y + 0.4, w: 0, h: 0.1,
      line: { color: colors.accentPrimary, width: 2 }
    });
  }
});

slide9.addText("事件流（智能体 → 外部系统）", {
  x: 4.5, y: 1.0, w: 5, h: 0.5,
  fontSize: 20, fontFace: "Arial", bold: true,
  color: colors.textPrimary
});

const eventFlow = [
  "git commit 事件",
  "tmux 会话事件",
  "GitHub 事件",
  "clawhip 事件路由器",
  "Discord 通知",
  "状态面板"
];

eventFlow.forEach((step, i) => {
  const y = 1.5 + i * 0.5;
  slide9.addShape(pres.shapes.RECTANGLE, {
    x: 4.5, y: y, w: 3.5, h: 0.4,
    fill: { color: colors.bgSecondary },
    line: { color: colors.border, width: 1 }
  });
  slide9.addText(step, {
    x: 4.6, y: y + 0.05, w: 3.3, h: 0.3,
    fontSize: 12, fontFace: "Arial",
    color: colors.textSecondary, align: "center"
  });
  if (i < eventFlow.length - 1) {
    slide9.addShape(pres.shapes.LINE, {
      x: 6.25, y: y + 0.4, w: 0, h: 0.1,
      line: { color: colors.accentSuccess, width: 2 }
    });
  }
});

// Slide 10: Section 7 - Technical Highlights
let slide10 = pres.addSlide();
slide10.background = { color: colors.bgPrimary };

slide10.addText("7. 技术亮点与创新点", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

const highlights = [
  { title: '"Clawable" 设计哲学', desc: "面向智能体而非面向人类" },
  { title: "Mock Parity Harness", desc: "跨实现行为一致性验证" },
  { title: "三层分离架构", desc: "OmX + clawhip + Claw Code" },
  { title: "分支锁与自动恢复", desc: "防止多智能体冲突" },
  { title: "上下文自动压缩", desc: "长时间自主运行支持" },
  { title: "多 Provider 透明适配", desc: "Anthropic/OpenAI/代理" }
];

highlights.forEach((h, i) => {
  const row = Math.floor(i / 2);
  const col = i % 2;
  const x = 0.5 + col * 4.7;
  const y = 1.0 + row * 1.4;

  slide10.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 4.5, h: 1.2,
    fill: { color: colors.bgSecondary },
    line: { color: colors.accentPrimary, width: 2 }
  });
  slide10.addText(h.title, {
    x: x + 0.15, y: y + 0.15, w: 4.2, h: 0.4,
    fontSize: 16, fontFace: "Arial", bold: true,
    color: colors.accentPrimary
  });
  slide10.addText(h.desc, {
    x: x + 0.15, y: y + 0.6, w: 4.2, h: 0.4,
    fontSize: 14, fontFace: "Arial",
    color: colors.textSecondary
  });
});

// Slide 11: Security
let slide11 = pres.addSlide();
slide11.background = { color: colors.bgPrimary };

slide11.addText("安全纵深防御", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: colors.accentPrimary
});

const securityLayers = [
  { layer: "Bash 校验", desc: "bash_validation.rs 拦截危险命令" },
  { layer: "审批令牌", desc: "approval_tokens.rs 显式审批" },
  { layer: "分支锁", desc: "branch_lock.rs 防止并发冲突" },
  { layer: "沙箱隔离", desc: "文件操作受工作区限制" },
  { layer: "凭证保护", desc: "日志中自动脱敏 API Key" }
];

securityLayers.forEach((s, i) => {
  const y = 1.0 + i * 0.85;
  slide11.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: y, w: 0.15, h: 0.7,
    fill: { color: colors.accentSecondary }
  });
  slide11.addText(s.layer, {
    x: 0.8, y: y + 0.05, w: 3, h: 0.3,
    fontSize: 16, fontFace: "Arial", bold: true,
    color: colors.textPrimary
  });
  slide11.addText(s.desc, {
    x: 0.8, y: y + 0.35, w: 8, h: 0.3,
    fontSize: 14, fontFace: "Arial",
    color: colors.textSecondary
  });
});

// Slide 12: Conclusion
let slide12 = pres.addSlide();
slide12.background = { color: colors.bgSecondary };

slide12.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.08,
  fill: { color: colors.accentSecondary }
});

slide12.addText("总结", {
  x: 0.5, y: 1.5, w: 9, h: 0.8,
  fontSize: 40, fontFace: "Arial", bold: true,
  color: colors.textPrimary, align: "center"
});

slide12.addText([
  { text: "Claw Code 是面向自主编码智能体的 CLI Agent Harness", options: { breakLine: true } },
  { text: "采用三层架构 + 事件驱动设计", options: { breakLine: true } },
  { text: "独创 Mock Parity Harness 确保行为一致性", options: { breakLine: true } },
  { text: "支持长时间无人值守的自主运行", options: { breakLine: true } }
].map(t => ({ text: "• " + t.text, options: { breakLine: true, fontSize: 18, color: colors.textSecondary, align: "center" } })), {
  x: 0.5, y: 2.5, w: 9, h: 2
});

slide12.addText("生成时间: 2026-05-17 22:58:26", {
  x: 0.5, y: 4.8, w: 9, h: 0.4,
  fontSize: 12, fontFace: "Arial",
  color: colors.textSecondary, align: "center"
});

// Save the presentation
pres.writeFile({ fileName: "../github_projects/01-docs/claw-code-设计说明书-20260517.pptx" })
  .then(() => console.log("文件已生成：D:\\01-work\\06-claudecode\\02-agent\\02-clone_github_proj\\github_manager_web\\github_projects\\01-docs\\claw-code-设计说明书-20260517.pptx"))
  .catch(err => console.error("Error:", err));
