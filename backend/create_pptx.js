const pptxgen = require("pptxgenjs");

// Create presentation
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Claude Code";
pres.title = "claw-code Usage";

// Color palette (GitHub dark theme)
const colors = {
  bgPrimary: "0d1117",
  bgSecondary: "161b22",
  bgTertiary: "21262d",
  textPrimary: "c9d1d9",
  textSecondary: "8b949e",
  textMuted: "6e7681",
  accentPrimary: "58a6ff",
  accentSecondary: "1f6feb",
  accentSuccess: "3fb950",
  accentWarning: "d29922",
  accentDanger: "f85149",
  borderColor: "30363d"
};

// Helper function to add dark background
function addDarkBackground(slide) {
  slide.background = { color: colors.bgPrimary };
}

// Helper function to add section header slide
function addSectionSlide(title, subtitle) {
  const slide = pres.addSlide();
  addDarkBackground(slide);

  // Add gradient-like effect with shapes
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: colors.bgSecondary }
  });

  // Accent line at top
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.05,
    fill: { color: colors.accentPrimary }
  });

  // Title
  slide.addText(title, {
    x: 0.5, y: 2, w: 9, h: 1,
    fontSize: 44, fontFace: "Segoe UI", bold: true,
    color: colors.textPrimary, align: "center", valign: "middle"
  });

  // Subtitle
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 3.2, w: 9, h: 0.5,
      fontSize: 18, fontFace: "Segoe UI",
      color: colors.textSecondary, align: "center", valign: "middle"
    });
  }

  return slide;
}

// Helper function to add content slide
function addContentSlide(title, content) {
  const slide = pres.addSlide();
  addDarkBackground(slide);

  // Header bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8,
    fill: { color: colors.bgSecondary }
  });

  // Accent line under header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.8, w: 10, h: 0.02,
    fill: { color: colors.borderColor }
  });

  // Title in header
  slide.addText(title, {
    x: 0.5, y: 0.15, w: 9, h: 0.5,
    fontSize: 24, fontFace: "Segoe UI", bold: true,
    color: colors.textPrimary, valign: "middle"
  });

  return slide;
}

// Helper function to add bullet points
function addBullets(slide, items, x, y, w, h, options = {}) {
  const textItems = items.map((item, idx) => ({
    text: item,
    options: {
      bullet: true,
      breakLine: idx < items.length - 1,
      fontSize: options.fontSize || 16,
      color: options.color || colors.textPrimary,
      fontFace: options.fontFace || "Segoe UI"
    }
  }));

  slide.addText(textItems, {
    x, y, w, h,
    valign: "top"
  });
}

// Helper function to add code block
function addCodeBlock(slide, code, x, y, w, h) {
  // Code background
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: colors.bgTertiary },
    line: { color: colors.borderColor, width: 1 },
    rectRadius: 0.05
  });

  // Code text
  slide.addText(code, {
    x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2,
    fontSize: 11, fontFace: "Consolas",
    color: colors.textPrimary, valign: "top"
  });
}

// Helper function to add table
function addTable(slide, headers, rows, x, y, w) {
  const tableData = [
    headers.map(h => ({
      text: h,
      options: { fill: { color: colors.bgTertiary }, color: colors.textPrimary, bold: true, fontSize: 12 }
    })),
    ...rows.map((row, idx) => row.map(cell => ({
      text: cell,
      options: { fill: { color: idx % 2 === 0 ? colors.bgSecondary : colors.bgPrimary }, color: colors.textSecondary, fontSize: 11 }
    })))
  ];

  const rowH = 0.35;
  const h = rowH * (rows.length + 1);

  slide.addTable(tableData, {
    x, y, w, h,
    border: { pt: 0.5, color: colors.borderColor },
    colW: Array(headers.length).fill(w / headers.length)
  });
}

// ============================================
// SLIDE 1: Title Slide
// ============================================
const titleSlide = pres.addSlide();
addDarkBackground(titleSlide);

// Gradient background effect
titleSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: colors.bgSecondary }
});

// Accent decorations
titleSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 2.5, w: 10, h: 0.02,
  fill: { color: colors.accentPrimary }
});

titleSlide.addShape(pres.shapes.OVAL, {
  x: 4.5, y: 1.2, w: 1, h: 1,
  fill: { color: colors.accentPrimary, transparency: 80 }
});

// Title
titleSlide.addText("claw-code Usage", {
  x: 0.5, y: 1.8, w: 9, h: 1,
  fontSize: 48, fontFace: "Segoe UI", bold: true,
  color: colors.textPrimary, align: "center", valign: "middle"
});

// Subtitle
titleSlide.addText("使用说明书", {
  x: 0.5, y: 2.9, w: 9, h: 0.5,
  fontSize: 24, fontFace: "Segoe UI",
  color: colors.textSecondary, align: "center", valign: "middle"
});

// Date
titleSlide.addText("生成时间: 2026-05-17 22:58:26", {
  x: 0.5, y: 4.8, w: 9, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI",
  color: colors.textMuted, align: "center", valign: "middle"
});

// ============================================
// SLIDE 2: Table of Contents
// ============================================
const tocSlide = addContentSlide("目录");

const tocItems = [
  { num: "1", title: "快速开始", sub: ["安装", "配置", "运行"] },
  { num: "2", title: "功能说明", sub: [] },
  { num: "3", title: "配置详解", sub: [] },
  { num: "4", title: "使用示例", sub: [] },
  { num: "5", title: "常见问题", sub: [] },
  { num: "6", title: "最佳实践", sub: [] },
  { num: "7", title: "注意事项", sub: [] }
];

tocItems.forEach((item, idx) => {
  const yPos = 1.1 + idx * 0.6;

  // Number circle
  tocSlide.addShape(pres.shapes.OVAL, {
    x: 0.5, y: yPos, w: 0.35, h: 0.35,
    fill: { color: colors.accentPrimary }
  });

  tocSlide.addText(item.num, {
    x: 0.5, y: yPos, w: 0.35, h: 0.35,
    fontSize: 14, fontFace: "Segoe UI", bold: true,
    color: colors.bgPrimary, align: "center", valign: "middle"
  });

  // Title
  tocSlide.addText(item.title, {
    x: 1, y: yPos, w: 3, h: 0.35,
    fontSize: 16, fontFace: "Segoe UI", bold: true,
    color: colors.textPrimary, valign: "middle"
  });

  // Sub-items
  if (item.sub.length > 0) {
    tocSlide.addText(item.sub.join(" | "), {
      x: 4.2, y: yPos, w: 5, h: 0.35,
      fontSize: 12, fontFace: "Segoe UI",
      color: colors.textSecondary, valign: "middle"
    });
  }
});

// ============================================
// SLIDE 3: Section - 快速开始
// ============================================
addSectionSlide("1. 快速开始", "安装 · 配置 · 运行");

// ============================================
// SLIDE 4: 安装
// ============================================
const installSlide = addContentSlide("1.1 安装 - 系统要求");

// System requirements
addBullets(installSlide, [
  "操作系统: Windows 11 Pro、Linux 或 macOS",
  "开发工具: Rust 工具链（包含 cargo）",
  "运行环境: Bash 或 PowerShell 终端"
], 0.5, 1.2, 4, 1.5);

// Installation methods
installSlide.addText("安装方式", {
  x: 5, y: 1.0, w: 4.5, h: 0.4,
  fontSize: 16, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

const methods = [
  "方式一：从源码构建",
  "方式二：使用安装脚本",
  "方式三：使用容器"
];

methods.forEach((method, idx) => {
  installSlide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5, y: 1.5 + idx * 0.7, w: 4.5, h: 0.55,
    fill: { color: colors.bgTertiary },
    line: { color: colors.borderColor, width: 1 },
    rectRadius: 0.05
  });

  installSlide.addText(method, {
    x: 5.2, y: 1.55 + idx * 0.7, w: 4.1, h: 0.45,
    fontSize: 14, fontFace: "Segoe UI",
    color: colors.textPrimary, valign: "middle"
  });
});

// Code example
addCodeBlock(installSlide,
  "# 克隆项目仓库\ngit clone https://github.com/ultraworkers/claw-code\ncd claw-code/rust\n\n# 构建工作空间\ncargo build --workspace\n\n# 运行测试验证构建\ncargo test --workspace",
  0.5, 3.0, 9, 2.3);

// ============================================
// SLIDE 5: 配置
// ============================================
const configSlide = addContentSlide("1.2 配置 - 环境变量");

// Environment variables table
addTable(configSlide,
  ["环境变量", "说明", "使用场景"],
  [
    ["ANTHROPIC_API_KEY", "Anthropic API 密钥", "直接 API 访问"],
    ["ANTHROPIC_AUTH_TOKEN", "Bearer Token 认证", "Token 认证方式"],
    ["ANTHROPIC_BASE_URL", "API 基础 URL", "代理或本地服务"]
  ],
  0.5, 1.2, 9);

// Configuration example
configSlide.addText("配置示例", {
  x: 0.5, y: 3.0, w: 9, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

addCodeBlock(configSlide,
  "# Linux/macOS\nexport ANTHROPIC_API_KEY=\"sk-ant-...\"\nexport ANTHROPIC_BASE_URL=\"https://api.anthropic.com\"\n\n# Windows PowerShell\n$env:ANTHROPIC_API_KEY=\"sk-ant-...\"\n$env:ANTHROPIC_BASE_URL=\"https://api.anthropic.com\"",
  0.5, 3.4, 9, 1.9);

// ============================================
// SLIDE 6: 运行
// ============================================
const runSlide = addContentSlide("1.3 运行 - 基本命令");

// Basic commands
addCodeBlock(runSlide,
  "# 进入交互式 REPL\ncd rust\n./target/debug/claw\n\n# Windows\n.\\target\\debug\\claw.exe\n\n# 健康检查（首次运行必做）\n/doctor\n\n# 或直接运行\n./target/debug/claw doctor --output-format json",
  0.5, 1.2, 5.5, 3.5);

// Doctor checks
runSlide.addText("/doctor 检查项", {
  x: 6.3, y: 1.0, w: 3.2, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

const doctorChecks = [
  "API 连接状态",
  "环境变量配置",
  "工具链完整性",
  "权限设置"
];

doctorChecks.forEach((check, idx) => {
  runSlide.addShape(pres.shapes.OVAL, {
    x: 6.3, y: 1.6 + idx * 0.55, w: 0.15, h: 0.15,
    fill: { color: colors.accentSuccess }
  });

  runSlide.addText(check, {
    x: 6.6, y: 1.55 + idx * 0.55, w: 2.9, h: 0.25,
    fontSize: 13, fontFace: "Segoe UI",
    color: colors.textPrimary, valign: "middle"
  });
});

// ============================================
// SLIDE 7: Section - 功能说明
// ============================================
addSectionSlide("2. 功能说明", "核心功能 · 工具能力 · 插件系统");

// ============================================
// SLIDE 8: 核心功能
// ============================================
const featuresSlide = addContentSlide("2.1 核心功能");

// Feature modules table
addTable(featuresSlide,
  ["功能模块", "说明"],
  [
    ["API 层", "Anthropic/OpenAI 兼容 API 客户端"],
    ["命令系统", "REPL 命令解析与执行"],
    ["运行时", "会话管理、文件操作、Bash 执行"],
    ["插件系统", "钩子脚本、扩展机制"],
    ["兼容性测试", "Mock 服务、Parity Harness"]
  ],
  0.5, 1.1, 5, 2.5);

// Main commands
featuresSlide.addText("主要命令", {
  x: 5.8, y: 1.0, w: 3.7, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

const commands = [
  { cmd: "/doctor", desc: "健康检查" },
  { cmd: "/init", desc: "项目初始化" },
  { cmd: "/status", desc: "状态查询" },
  { cmd: "/sandbox", desc: "沙箱检查" },
  { cmd: "/version", desc: "版本信息" }
];

commands.forEach((item, idx) => {
  featuresSlide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.8, y: 1.5 + idx * 0.55, w: 3.7, h: 0.45,
    fill: { color: colors.bgTertiary },
    line: { color: colors.borderColor, width: 1 },
    rectRadius: 0.03
  });

  featuresSlide.addText(item.cmd, {
    x: 6, y: 1.55 + idx * 0.55, w: 1.2, h: 0.35,
    fontSize: 12, fontFace: "Consolas", bold: true,
    color: colors.accentPrimary, valign: "middle"
  });

  featuresSlide.addText(item.desc, {
    x: 7.3, y: 1.55 + idx * 0.55, w: 2, h: 0.35,
    fontSize: 12, fontFace: "Segoe UI",
    color: colors.textSecondary, valign: "middle"
  });
});

// Tool capabilities
featuresSlide.addText("工具能力", {
  x: 0.5, y: 4.0, w: 9, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

const tools = [
  { title: "文件操作", items: ["读取", "写入", "搜索", "导航"] },
  { title: "Bash 执行", items: ["命令执行", "输出捕获", "后台任务"] },
  { title: "提示缓存", items: ["减少重复请求开销"] }
];

tools.forEach((tool, idx) => {
  const xPos = 0.5 + idx * 3.1;

  featuresSlide.addText(tool.title, {
    x: xPos, y: 4.4, w: 2.9, h: 0.3,
    fontSize: 12, fontFace: "Segoe UI", bold: true,
    color: colors.textPrimary
  });

  featuresSlide.addText(tool.items.join(" · "), {
    x: xPos, y: 4.75, w: 2.9, h: 0.5,
    fontSize: 10, fontFace: "Segoe UI",
    color: colors.textSecondary
  });
});

// ============================================
// SLIDE 9: Section - 配置详解
// ============================================
addSectionSlide("3. 配置详解", "项目配置 · 环境变量 · 权限");

// ============================================
// SLIDE 10: 配置文件
// ============================================
const configFileSlide = addContentSlide("3.1 项目配置文件");

// Config layers
const configs = [
  { file: ".claw.json", desc: "项目级共享配置", color: colors.accentPrimary },
  { file: ".claude/settings.local.json", desc: "机器本地覆盖配置", color: colors.accentSuccess },
  { file: "CLAUDE.md", desc: "项目指导文件", color: colors.accentWarning }
];

configs.forEach((cfg, idx) => {
  configFileSlide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.1 + idx * 0.8, w: 4, h: 0.65,
    fill: { color: colors.bgTertiary },
    line: { color: cfg.color, width: 2 },
    rectRadius: 0.05
  });

  configFileSlide.addText(cfg.file, {
    x: 0.7, y: 1.15 + idx * 0.8, w: 3.6, h: 0.3,
    fontSize: 13, fontFace: "Consolas", bold: true,
    color: cfg.color
  });

  configFileSlide.addText(cfg.desc, {
    x: 0.7, y: 1.45 + idx * 0.8, w: 3.6, h: 0.25,
    fontSize: 11, fontFace: "Segoe UI",
    color: colors.textSecondary
  });
});

// Config example
configFileSlide.addText("配置示例", {
  x: 5, y: 1.0, w: 4.5, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

addCodeBlock(configFileSlide,
  '{\n  "version": "1.0",\n  "defaults": {\n    "model": "claude-sonnet-4-6",\n    "output_format": "text"\n  },\n  "permissions": {\n    "read": ["*"],\n    "write": ["src/**", "tests/**"],\n    "bash": ["cargo", "git"]\n  }\n}',
  5, 1.5, 4.5, 2.5);

// ============================================
// SLIDE 11: Section - 使用示例
// ============================================
addSectionSlide("4. 使用示例", "基本流程 · 文件操作 · Bash 命令");

// ============================================
// SLIDE 12: 使用流程
// ============================================
const usageSlide = addContentSlide("4.1 基本使用流程");

const steps = [
  { num: "1", title: "构建项目", cmd: "cargo build --workspace" },
  { num: "2", title: "启动 REPL", cmd: "./target/debug/claw" },
  { num: "3", title: "健康检查", cmd: "/doctor" },
  { num: "4", title: "初始化项目", cmd: "/init" },
  { num: "5", title: "开始交互", cmd: "输入自然语言指令" }
];

steps.forEach((step, idx) => {
  const yPos = 1.1 + idx * 0.85;

  // Step number
  usageSlide.addShape(pres.shapes.OVAL, {
    x: 0.5, y: yPos, w: 0.45, h: 0.45,
    fill: { color: colors.accentPrimary }
  });

  usageSlide.addText(step.num, {
    x: 0.5, y: yPos, w: 0.45, h: 0.45,
    fontSize: 16, fontFace: "Segoe UI", bold: true,
    color: colors.bgPrimary, align: "center", valign: "middle"
  });

  // Title
  usageSlide.addText(step.title, {
    x: 1.1, y: yPos, w: 2, h: 0.45,
    fontSize: 14, fontFace: "Segoe UI", bold: true,
    color: colors.textPrimary, valign: "middle"
  });

  // Command
  usageSlide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 3.2, y: yPos + 0.05, w: 6.3, h: 0.35,
    fill: { color: colors.bgTertiary },
    rectRadius: 0.03
  });

  usageSlide.addText(step.cmd, {
    x: 3.4, y: yPos + 0.05, w: 6, h: 0.35,
    fontSize: 12, fontFace: "Consolas",
    color: colors.accentSuccess, valign: "middle"
  });
});

// ============================================
// SLIDE 13: Section - 常见问题
// ============================================
addSectionSlide("5. 常见问题解答", "构建 · API · 权限 · 会话");

// ============================================
// SLIDE 14: FAQ
// ============================================
const faqSlide = addContentSlide("5. 常见问题解答");

const faqs = [
  { q: "Q1: 构建失败怎么办？", a: "检查 Rust 版本 → 更新依赖 → cargo clean → 重新构建" },
  { q: "Q2: API 连接失败？", a: "验证环境变量 → 检查网络 → 确认 API 密钥格式" },
  { q: "Q3: 权限被拒绝？", a: "检查 .claw.json → 更新权限设置 → 使用 /sandbox 检查" },
  { q: "Q4: 会话恢复失败？", a: "检查会话目录 → 使用特定会话 ID → 启动新会话" },
  { q: "Q5: Windows 路径问题？", a: "使用反斜杠 → 添加 .exe 后缀 → 参考文档" },
  { q: "Q6: 插件加载失败？", a: "检查脚本权限 → 验证路径 → 检查 MCP 配置" }
];

faqs.forEach((faq, idx) => {
  const yPos = 1.1 + idx * 0.72;

  faqSlide.addText(faq.q, {
    x: 0.5, y: yPos, w: 9, h: 0.3,
    fontSize: 13, fontFace: "Segoe UI", bold: true,
    color: colors.accentPrimary
  });

  faqSlide.addText(faq.a, {
    x: 0.5, y: yPos + 0.32, w: 9, h: 0.35,
    fontSize: 12, fontFace: "Segoe UI",
    color: colors.textSecondary
  });
});

// ============================================
// SLIDE 15: Section - 最佳实践
// ============================================
addSectionSlide("6. 最佳实践建议", "开发流程 · 配置管理 · 测试策略");

// ============================================
// SLIDE 16: 最佳实践
// ============================================
const bestPracticesSlide = addContentSlide("6. 最佳实践建议");

// Development workflow
bestPracticesSlide.addText("开发流程", {
  x: 0.5, y: 1.1, w: 4.5, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

addBullets(bestPracticesSlide, [
  "变更前运行 cargo fmt --check",
  "执行 cargo test --workspace",
  "运行 cargo clippy 检查",
  "保持变更小且可审查"
], 0.5, 1.5, 4.5, 1.8, { fontSize: 12 });

// Configuration management
bestPracticesSlide.addText("配置管理", {
  x: 5.2, y: 1.1, w: 4.3, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentSuccess
});

addBullets(bestPracticesSlide, [
  "项目共享配置提交到版本控制",
  "本地覆盖配置不提交",
  "敏感信息使用环境变量",
  "定期检查权限设置"
], 5.2, 1.5, 4.3, 1.8, { fontSize: 12 });

// Testing strategy
bestPracticesSlide.addText("测试策略", {
  x: 0.5, y: 3.5, w: 4.5, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentWarning
});

addBullets(bestPracticesSlide, [
  "运行单元测试验证功能",
  "使用 Parity Harness 检查行为",
  "定期运行行为差异检查",
  "保持测试覆盖率"
], 0.5, 3.9, 4.5, 1.5, { fontSize: 12 });

// PR checklist
bestPracticesSlide.addText("PR 检查清单", {
  x: 5.2, y: 3.5, w: 4.3, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentDanger
});

addBullets(bestPracticesSlide, [
  "描述用户可见的变更原因",
  "列出执行的命令和已知差距",
  "说明兼容性风险",
  "不包含无关清理"
], 5.2, 3.9, 4.3, 1.5, { fontSize: 12 });

// ============================================
// SLIDE 17: Section - 注意事项
// ============================================
addSectionSlide("7. 注意事项与限制", "安全 · 平台 · API · 功能");

// ============================================
// SLIDE 18: 注意事项
// ============================================
const notesSlide = addContentSlide("7. 注意事项与限制");

// Security
notesSlide.addText("安全注意事项", {
  x: 0.5, y: 1.1, w: 4.5, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentDanger
});

addBullets(notesSlide, [
  "不要提交 API 密钥和 Token",
  "不要提交会话转录中的凭证",
  "使用 GitHub 私有漏洞报告",
  "配置 deny 规则保护敏感路径"
], 0.5, 1.5, 4.5, 1.5, { fontSize: 12 });

// Platform
notesSlide.addText("平台限制", {
  x: 5.2, y: 1.1, w: 4.3, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentWarning
});

addBullets(notesSlide, [
  "Windows 使用反斜杠路径",
  "可执行文件需要 .exe 后缀",
  "WSL 参考 windows-install 文档",
  "环境变量设置方式不同"
], 5.2, 1.5, 4.3, 1.5, { fontSize: 12 });

// API limits
notesSlide.addText("API 限制", {
  x: 0.5, y: 3.3, w: 4.5, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

addBullets(notesSlide, [
  "需要有效的 API 密钥或 Token",
  "速率限制取决于 API 计划",
  "OpenAI 兼容提供者功能有限",
  "支持提示缓存优化"
], 0.5, 3.7, 4.5, 1.5, { fontSize: 12 });

// Version support
notesSlide.addText("版本支持", {
  x: 5.2, y: 3.3, w: 4.3, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentSuccess
});

addBullets(notesSlide, [
  "支持当前 main 分支",
  "支持最新发布的版本",
  "不支持旧实验分支",
  "参考 ROADMAP.md 了解计划"
], 5.2, 3.7, 4.3, 1.5, { fontSize: 12 });

// ============================================
// SLIDE 19: 附录 - 项目统计
// ============================================
const statsSlide = addContentSlide("附录 - 项目统计");

addTable(statsSlide,
  ["指标", "数值"],
  [
    ["Main 分支提交数", "292"],
    ["Crate 数量", "9"],
    ["Rust LOC", "48,599"],
    ["测试 LOC", "2,568"],
    ["作者数", "3"],
    ["Mock 场景数", "12"]
  ],
  0.5, 1.2, 4.5);

// Crate structure
statsSlide.addText("Crate 结构", {
  x: 5.3, y: 1.0, w: 4.2, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

const crates = [
  { name: "api", desc: "API 客户端、HTTP、SSE" },
  { name: "commands", desc: "命令解析与执行" },
  { name: "runtime", desc: "会话、配置、文件操作" },
  { name: "plugins", desc: "钩子、插件、测试隔离" }
];

crates.forEach((crate, idx) => {
  statsSlide.addText(crate.name, {
    x: 5.3, y: 1.5 + idx * 0.5, w: 1.5, h: 0.4,
    fontSize: 12, fontFace: "Consolas", bold: true,
    color: colors.accentSuccess
  });

  statsSlide.addText(crate.desc, {
    x: 6.9, y: 1.5 + idx * 0.5, w: 2.6, h: 0.4,
    fontSize: 11, fontFace: "Segoe UI",
    color: colors.textSecondary, valign: "middle"
  });
});

// ============================================
// SLIDE 20: 社区资源
// ============================================
const communitySlide = addContentSlide("社区资源");

// GitHub
communitySlide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 1.2,
  fill: { color: colors.bgTertiary },
  line: { color: colors.accentPrimary, width: 2 },
  rectRadius: 0.08
});

communitySlide.addText("GitHub", {
  x: 0.7, y: 1.35, w: 3.9, h: 0.35,
  fontSize: 16, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

communitySlide.addText("github.com/ultraworkers/claw-code", {
  x: 0.7, y: 1.75, w: 3.9, h: 0.5,
  fontSize: 12, fontFace: "Segoe UI",
  color: colors.textSecondary
});

// Discord
communitySlide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 1.2,
  fill: { color: colors.bgTertiary },
  line: { color: colors.accentSuccess, width: 2 },
  rectRadius: 0.08
});

communitySlide.addText("Discord", {
  x: 5.4, y: 1.35, w: 3.9, h: 0.35,
  fontSize: 16, fontFace: "Segoe UI", bold: true,
  color: colors.accentSuccess
});

communitySlide.addText("discord.gg/5TUQKqFWd", {
  x: 5.4, y: 1.75, w: 3.9, h: 0.5,
  fontSize: 12, fontFace: "Segoe UI",
  color: colors.textSecondary
});

// Related projects
communitySlide.addText("相关项目", {
  x: 0.5, y: 2.8, w: 9, h: 0.4,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentWarning
});

const relatedProjects = [
  { name: "oh-my-codex", url: "github.com/Yeachan-Heo/oh-my-codex" },
  { name: "clawhip", url: "github.com/Yeachan-Heo/clawhip" }
];

relatedProjects.forEach((proj, idx) => {
  communitySlide.addText(proj.name, {
    x: 0.5 + idx * 4.5, y: 3.3, w: 4, h: 0.35,
    fontSize: 13, fontFace: "Segoe UI", bold: true,
    color: colors.textPrimary
  });

  communitySlide.addText(proj.url, {
    x: 0.5 + idx * 4.5, y: 3.65, w: 4, h: 0.35,
    fontSize: 11, fontFace: "Segoe UI",
    color: colors.textSecondary
  });
});

// Reference sources
communitySlide.addText("参考来源", {
  x: 0.5, y: 4.2, w: 9, h: 0.35,
  fontSize: 14, fontFace: "Segoe UI", bold: true,
  color: colors.accentPrimary
});

communitySlide.addText("README.md · CLAUDE.md · USAGE.md · PARITY.md · ROADMAP.md · CONTRIBUTING.md · SECURITY.md", {
  x: 0.5, y: 4.6, w: 9, h: 0.5,
  fontSize: 11, fontFace: "Segoe UI",
  color: colors.textSecondary
});

// ============================================
// SLIDE 21: Thank You
// ============================================
const thankYouSlide = pres.addSlide();
addDarkBackground(thankYouSlide);

thankYouSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: colors.bgSecondary }
});

thankYouSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 2.5, w: 10, h: 0.02,
  fill: { color: colors.accentPrimary }
});

thankYouSlide.addText("Thank You", {
  x: 0.5, y: 1.8, w: 9, h: 0.8,
  fontSize: 48, fontFace: "Segoe UI", bold: true,
  color: colors.textPrimary, align: "center", valign: "middle"
});

thankYouSlide.addText("本说明书由 Claude Code 自动生成", {
  x: 0.5, y: 2.8, w: 9, h: 0.5,
  fontSize: 16, fontFace: "Segoe UI", italic: true,
  color: colors.textSecondary, align: "center", valign: "middle"
});

thankYouSlide.addText("生成时间: 2026-05-17 22:58:26", {
  x: 0.5, y: 4.8, w: 9, h: 0.4,
  fontSize: 12, fontFace: "Segoe UI",
  color: colors.textMuted, align: "center", valign: "middle"
});

// Save the presentation
pres.writeFile({ fileName: "D:\\01-work\\06-claudecode\\02-agent\\02-clone_github_proj\\github_manager_web\\github_projects\\01-docs\\claw-code-使用说明书-20260517.pptx" })
  .then(() => {
    console.log("文件已生成：D:\\01-work\\06-claudecode\\02-agent\\02-clone_github_proj\\github_manager_web\\github_projects\\01-docs\\claw-code-使用说明书-20260517.pptx");
  })
  .catch(err => {
    console.error("Error:", err);
  });
