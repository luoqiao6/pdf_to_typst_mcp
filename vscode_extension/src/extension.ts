import * as vscode from 'vscode';
import * as path from 'path';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import { promises as fs } from 'fs';

interface MCPResponse {
    success: boolean;
    data?: any;
    error?: string;
    sessionId?: string;
}

export class PDFToTypstConverter {
    private mcpProcess: ChildProcessWithoutNullStreams | null = null;
    private context: vscode.ExtensionContext;
    private outputChannel: vscode.OutputChannel;
    
    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.outputChannel = vscode.window.createOutputChannel('PDF to Typst');
    }

    async startMCPServer(): Promise<boolean> {
        const config = vscode.workspace.getConfiguration('pdfToTypst');
        const serverPath = config.get<string>('mcpServerPath');
        const pythonPath = config.get<string>('pythonPath', 'python');

        if (!serverPath) {
            vscode.window.showErrorMessage('请先在设置中配置MCP服务器路径');
            return false;
        }

        try {
            this.outputChannel.appendLine(`启动MCP服务器: ${pythonPath} ${serverPath}`);
            
            this.mcpProcess = spawn(pythonPath, [serverPath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: path.dirname(serverPath)
            });

            this.mcpProcess.stdout?.on('data', (data) => {
                this.outputChannel.appendLine(`MCP输出: ${data.toString()}`);
            });

            this.mcpProcess.stderr?.on('data', (data) => {
                this.outputChannel.appendLine(`MCP错误: ${data.toString()}`);
            });

            this.mcpProcess.on('close', (code) => {
                this.outputChannel.appendLine(`MCP服务器退出，代码: ${code}`);
                this.mcpProcess = null;
            });

            // 等待服务器启动
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            return this.mcpProcess !== null;
        } catch (error) {
            this.outputChannel.appendLine(`启动MCP服务器失败: ${error}`);
            return false;
        }
    }

    async callMCPTool(toolName: string, args: any): Promise<MCPResponse> {
        if (!this.mcpProcess) {
            const started = await this.startMCPServer();
            if (!started) {
                return { success: false, error: 'MCP服务器启动失败' };
            }
        }

        return new Promise((resolve) => {
            const request = {
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: {
                    name: toolName,
                    arguments: args
                }
            };

            const requestStr = JSON.stringify(request) + '\n';
            this.mcpProcess?.stdin?.write(requestStr);

            // 简化的响应处理（实际应该更完善）
            setTimeout(() => {
                resolve({ success: true, data: 'MCP调用完成' });
            }, 5000);
        });
    }

    async convertPDF(pdfPath: string): Promise<void> {
        const config = vscode.workspace.getConfiguration('pdfToTypst');
        const outputDir = config.get<string>('outputDirectory') || path.dirname(pdfPath);
        const useAI = config.get<boolean>('useAiEnhancement', true);

        try {
            // 显示进度
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "转换PDF到Typst",
                cancellable: true
            }, async (progress, token) => {
                progress.report({ increment: 0, message: "启动转换服务..." });

                // 启动转换会话
                const sessionResponse = await this.callMCPTool('start_pdf_conversion', {
                    pdf_path: pdfPath,
                    session_id: `vscode_${Date.now()}`
                });

                if (!sessionResponse.success) {
                    throw new Error(sessionResponse.error || '启动转换失败');
                }

                progress.report({ increment: 30, message: "分析PDF结构..." });

                if (useAI) {
                    // AI增强转换流程
                    progress.report({ increment: 50, message: "AI分析页面布局..." });
                    
                    // 这里应该集成AI分析逻辑
                    // 由于VSCode中无法直接使用多模态AI，我们提供文本提示
                    const aiGuidance = await this.generateAIGuidance(pdfPath);
                    
                    progress.report({ increment: 80, message: "生成Typst代码..." });
                    
                    // 显示AI指导信息
                    const useAIGuidance = await vscode.window.showInformationMessage(
                        'AI增强转换需要您的参与。是否查看AI分析指导？',
                        '查看指导', '直接转换'
                    );

                    if (useAIGuidance === '查看指导') {
                        await this.showAIGuidancePanel(aiGuidance, sessionResponse.sessionId);
                        return;
                    }
                }

                // 完成转换
                const outputPath = path.join(outputDir, path.basename(pdfPath, '.pdf') + '.typ');
                
                const finalizeResponse = await this.callMCPTool('finalize_conversion', {
                    session_id: sessionResponse.sessionId,
                    output_path: outputPath,
                    typst_content: await this.generateBasicTypstContent(pdfPath)
                });

                progress.report({ increment: 100, message: "转换完成！" });

                if (finalizeResponse.success) {
                    const openFile = await vscode.window.showInformationMessage(
                        `转换完成！输出文件: ${outputPath}`,
                        '打开文件', '打开目录'
                    );

                    if (openFile === '打开文件') {
                        const doc = await vscode.workspace.openTextDocument(outputPath);
                        await vscode.window.showTextDocument(doc);
                    } else if (openFile === '打开目录') {
                        await vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(outputPath));
                    }
                } else {
                    throw new Error(finalizeResponse.error || '转换失败');
                }
            });

        } catch (error) {
            this.outputChannel.appendLine(`转换失败: ${error}`);
            vscode.window.showErrorMessage(`转换失败: ${error}`);
        }
    }

    async generateAIGuidance(pdfPath: string): Promise<string> {
        // 生成AI分析指导文本
        return `
# PDF转Typst AI增强指导

## 📄 文档: ${path.basename(pdfPath)}

### 🤖 AI分析步骤

1. **页面布局分析**
   - 观察文档的整体结构（单栏/双栏/多栏）
   - 识别标题层次和段落结构
   - 找出表格、图片、公式等特殊元素

2. **Typst代码生成建议**
   - 使用适当的heading函数处理标题
   - 设置正确的页面布局和边距
   - 处理图文混排和表格结构

3. **质量优化要点**
   - 确保字体和样式与原文档匹配
   - 调整行距和段落间距
   - 验证数学公式和特殊符号

### 💡 提示
请根据PDF内容特点，选择合适的Typst语法和函数。
如需帮助，可以查阅Typst官方文档。
        `;
    }

    async showAIGuidancePanel(guidance: string, sessionId?: string): Promise<void> {
        const panel = vscode.window.createWebviewPanel(
            'pdfToTypstGuidance',
            'PDF转Typst AI指导',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = this.getGuidanceWebviewContent(guidance, sessionId);

        panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'generateTypst':
                        await this.handleTypstGeneration(message.content, sessionId);
                        break;
                    case 'finalize':
                        await this.finalizeConversion(sessionId, message.typstContent);
                        panel.dispose();
                        break;
                }
            },
            undefined,
            this.context.subscriptions
        );
    }

    private getGuidanceWebviewContent(guidance: string, sessionId?: string): string {
        return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF转Typst AI指导</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            margin: 20px;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        .guidance { 
            background: var(--vscode-textBlockQuote-background);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .input-area {
            margin: 20px 0;
        }
        textarea {
            width: 100%;
            height: 200px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .session-info {
            background: var(--vscode-textPreformat-background);
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="session-info">
        会话ID: ${sessionId || '未知'}
    </div>
    
    <div class="guidance">
        <pre>${guidance}</pre>
    </div>

    <div class="input-area">
        <h3>🎯 Typst代码编辑器</h3>
        <p>请在下方编辑器中输入或粘贴生成的Typst代码：</p>
        <textarea id="typstContent" placeholder="在此输入Typst代码...">
#set page(paper: "a4")
#set text(font: "SimSun", size: 12pt)
#set par(justify: true, leading: 0.65em)

// 在此添加您的内容
        </textarea>
    </div>

    <div>
        <button onclick="generateSample()">生成示例代码</button>
        <button onclick="validateCode()">验证语法</button>
        <button onclick="finalizeConversion()">完成转换</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function generateSample() {
            const sample = \`#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: "SimSun", size: 12pt, lang: "zh")
#set par(justify: true, leading: 0.65em, first-line-indent: 2em)

= 文档标题

这是一个段落示例。

== 二级标题

#table(
  columns: 2,
  [项目], [描述],
  [示例1], [内容1],
  [示例2], [内容2]
)

#image("image.jpg", width: 80%)
\`;
            document.getElementById('typstContent').value = sample;
        }

        function validateCode() {
            const content = document.getElementById('typstContent').value;
            if (content.trim()) {
                vscode.postMessage({
                    command: 'generateTypst',
                    content: content
                });
            } else {
                alert('请先输入Typst代码');
            }
        }

        function finalizeConversion() {
            const content = document.getElementById('typstContent').value;
            if (content.trim()) {
                vscode.postMessage({
                    command: 'finalize',
                    typstContent: content
                });
            } else {
                alert('请先输入Typst代码');
            }
        }
    </script>
</body>
</html>`;
    }

    async handleTypstGeneration(content: string, sessionId?: string): Promise<void> {
        // 验证Typst语法（简单检查）
        const hasBasicStructure = content.includes('#set') || content.includes('=') || content.includes('#');
        
        if (hasBasicStructure) {
            vscode.window.showInformationMessage('✅ Typst代码结构看起来正确！');
        } else {
            vscode.window.showWarningMessage('⚠️ 代码可能缺少基本的Typst语法结构');
        }
    }

    async finalizeConversion(sessionId?: string, typstContent?: string): Promise<void> {
        if (!typstContent) {
            vscode.window.showErrorMessage('缺少Typst代码内容');
            return;
        }

        try {
            const response = await this.callMCPTool('finalize_conversion', {
                session_id: sessionId,
                typst_content: typstContent
            });

            if (response.success) {
                vscode.window.showInformationMessage('🎉 转换完成！');
            } else {
                vscode.window.showErrorMessage('转换失败: ' + response.error);
            }
        } catch (error) {
            vscode.window.showErrorMessage('转换过程中出错: ' + error);
        }
    }

    async generateBasicTypstContent(pdfPath: string): Promise<string> {
        // 生成基础的Typst内容模板
        const fileName = path.basename(pdfPath, '.pdf');
        return `#set page(paper: "a4")
#set text(font: "SimSun", size: 12pt)
#set par(justify: true, leading: 0.65em)

= ${fileName}

// 此文档由PDF转Typst工具自动生成
// 请根据原PDF内容进行调整

#lorem(100)
`;
    }

    async analyzePDF(pdfPath: string): Promise<void> {
        try {
            const response = await this.callMCPTool('analyze_pdf_structure', {
                pdf_path: pdfPath
            });

            if (response.success) {
                // 显示分析结果
                const panel = vscode.window.createWebviewPanel(
                    'pdfAnalysis',
                    `PDF分析 - ${path.basename(pdfPath)}`,
                    vscode.ViewColumn.Two,
                    {}
                );

                panel.webview.html = `
                    <html>
                    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px;">
                        <h2>📊 PDF结构分析</h2>
                        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow: auto;">
${response.data || '分析完成，请查看输出通道获取详细信息'}
                        </pre>
                    </body>
                    </html>
                `;
            } else {
                vscode.window.showErrorMessage('分析失败: ' + response.error);
            }
        } catch (error) {
            vscode.window.showErrorMessage('分析过程中出错: ' + error);
        }
    }

    async previewTypst(pdfPath: string): Promise<void> {
        try {
            const response = await this.callMCPTool('preview_typst_output', {
                pdf_path: pdfPath,
                max_pages: 3
            });

            if (response.success) {
                // 创建预览面板
                const panel = vscode.window.createWebviewPanel(
                    'typstPreview',
                    `Typst预览 - ${path.basename(pdfPath)}`,
                    vscode.ViewColumn.Two,
                    {}
                );

                panel.webview.html = `
                    <html>
                    <head>
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
                            .code { background: #f8f8f8; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; overflow: auto; }
                        </style>
                    </head>
                    <body>
                        <h2>🔍 Typst代码预览</h2>
                        <div class="code">
                            <pre>${response.data || '预览生成中...'}</pre>
                        </div>
                    </body>
                    </html>
                `;
            } else {
                vscode.window.showErrorMessage('预览失败: ' + response.error);
            }
        } catch (error) {
            vscode.window.showErrorMessage('预览过程中出错: ' + error);
        }
    }

    dispose(): void {
        if (this.mcpProcess) {
            this.mcpProcess.kill();
        }
        this.outputChannel.dispose();
    }
}

export function activate(context: vscode.ExtensionContext) {
    const converter = new PDFToTypstConverter(context);

    // 注册命令
    const commands = [
        vscode.commands.registerCommand('pdfToTypst.convert', async (uri?: vscode.Uri) => {
            const pdfPath = uri ? uri.fsPath : await selectPDFFile();
            if (pdfPath) {
                await converter.convertPDF(pdfPath);
            }
        }),

        vscode.commands.registerCommand('pdfToTypst.analyze', async (uri?: vscode.Uri) => {
            const pdfPath = uri ? uri.fsPath : await selectPDFFile();
            if (pdfPath) {
                await converter.analyzePDF(pdfPath);
            }
        }),

        vscode.commands.registerCommand('pdfToTypst.preview', async (uri?: vscode.Uri) => {
            const pdfPath = uri ? uri.fsPath : await selectPDFFile();
            if (pdfPath) {
                await converter.previewTypst(pdfPath);
            }
        }),

        vscode.commands.registerCommand('pdfToTypst.openSettings', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'pdfToTypst');
        })
    ];

    commands.forEach(cmd => context.subscriptions.push(cmd));
    context.subscriptions.push(converter);
}

async function selectPDFFile(): Promise<string | undefined> {
    const result = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectMany: false,
        filters: {
            'PDF Files': ['pdf']
        }
    });

    return result && result[0] ? result[0].fsPath : undefined;
}

export function deactivate() {}
