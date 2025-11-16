"""Web configuration interface for Ye Linghua personality and prompts

A FastAPI-based web application for editing personality and prompts configuration.

Usage:
    python -m ye_linghua.web_config
    # or
    ye-linghua-config

Then open http://localhost:8000 in your browser.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from ye_linghua.config import Config
from ye_linghua.personality_loader import PersonalityLoader

app = FastAPI(title="Ye Linghua Configuration", version="0.1.0")


class PersonalityUpdate(BaseModel):
    """Personality configuration update model"""

    data: dict[str, Any]


class PromptsUpdate(BaseModel):
    """Prompts configuration update model"""

    data: dict[str, Any]


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main configuration page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>叶灵华 (Ye Linghua) 配置界面</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }

            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }

            .tabs {
                display: flex;
                background: #f5f5f5;
                border-bottom: 2px solid #ddd;
            }

            .tab {
                flex: 1;
                padding: 20px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: bold;
                font-size: 1.1em;
            }

            .tab:hover {
                background: #e0e0e0;
            }

            .tab.active {
                background: white;
                border-bottom: 3px solid #667eea;
                color: #667eea;
            }

            .tab-content {
                display: none;
                padding: 30px;
            }

            .tab-content.active {
                display: block;
            }

            .editor-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 20px;
            }

            .editor-panel {
                background: #f9f9f9;
                border-radius: 10px;
                padding: 20px;
            }

            .editor-panel h3 {
                margin-bottom: 15px;
                color: #333;
                font-size: 1.3em;
            }

            textarea {
                width: 100%;
                height: 500px;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                resize: vertical;
                transition: border-color 0.3s;
            }

            textarea:focus {
                outline: none;
                border-color: #667eea;
            }

            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }

            button {
                flex: 1;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                font-size: 1em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }

            .btn-save {
                background: #4caf50;
                color: white;
            }

            .btn-save:hover {
                background: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            }

            .btn-preview {
                background: #2196F3;
                color: white;
            }

            .btn-preview:hover {
                background: #0b7dda;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
            }

            .btn-load {
                background: #ff9800;
                color: white;
            }

            .btn-load:hover {
                background: #fb8c00;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
            }

            .preview-box {
                background: #fff;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                max-height: 600px;
                overflow-y: auto;
                white-space: pre-wrap;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                line-height: 1.6;
            }

            .message {
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                font-weight: bold;
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }

            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }

            .info-box {
                background: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
            }

            .info-box h4 {
                margin-bottom: 10px;
                color: #1976d2;
            }

            .info-box ul {
                margin-left: 20px;
            }

            .info-box li {
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌸 叶灵华 (Ye Linghua)</h1>
                <p>AI助手 人设与提示词配置界面</p>
            </div>

            <div class="tabs">
                <div class="tab active" onclick="switchTab('personality')">人设配置</div>
                <div class="tab" onclick="switchTab('prompts')">提示词配置</div>
                <div class="tab" onclick="switchTab('preview')">预览生成</div>
            </div>

            <!-- 人设配置标签页 -->
            <div id="personality-tab" class="tab-content active">
                <div class="info-box">
                    <h4>📝 人设配置说明</h4>
                    <ul>
                        <li>配置叶灵华的基本信息、性格特点、专业能力等</li>
                        <li>支持完整的YAML格式配置</li>
                        <li>修改后点击"保存配置"按钮保存</li>
                    </ul>
                </div>

                <div class="editor-container">
                    <div class="editor-panel">
                        <h3>编辑器</h3>
                        <textarea id="personality-editor" placeholder="加载中..."></textarea>
                        <div class="button-group">
                            <button class="btn-load" onclick="loadPersonality()">重新加载</button>
                            <button class="btn-save" onclick="savePersonality()">保存配置</button>
                        </div>
                    </div>

                    <div class="editor-panel">
                        <h3>配置说明</h3>
                        <div style="line-height: 1.8; color: #555;">
                            <p><strong>主要配置项：</strong></p>
                            <ul style="margin-left: 20px; margin-top: 10px;">
                                <li><code>name</code>: AI助手的中文名</li>
                                <li><code>name_en</code>: AI助手的英文名</li>
                                <li><code>role</code>: 角色定位和描述</li>
                                <li><code>personality.traits</code>: 性格特点列表</li>
                                <li><code>personality.interests</code>: 兴趣爱好</li>
                                <li><code>skills</code>: 专业技能配置</li>
                                <li><code>behavior</code>: 交互行为模板</li>
                            </ul>
                            <p style="margin-top: 15px;"><strong>💡 小提示：</strong></p>
                            <ul style="margin-left: 20px; margin-top: 5px;">
                                <li>确保YAML格式正确（注意缩进）</li>
                                <li>可以添加新的字段和属性</li>
                                <li>保存前建议先预览效果</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div id="personality-message"></div>
            </div>

            <!-- 提示词配置标签页 -->
            <div id="prompts-tab" class="tab-content">
                <div class="info-box">
                    <h4>📝 提示词配置说明</h4>
                    <ul>
                        <li>配置系统提示词模板和各种场景的提示词</li>
                        <li>支持使用变量占位符（如 {name}, {role_description}）</li>
                        <li>修改后点击"保存配置"按钮保存</li>
                    </ul>
                </div>

                <div class="editor-container">
                    <div class="editor-panel">
                        <h3>编辑器</h3>
                        <textarea id="prompts-editor" placeholder="加载中..."></textarea>
                        <div class="button-group">
                            <button class="btn-load" onclick="loadPrompts()">重新加载</button>
                            <button class="btn-save" onclick="savePrompts()">保存配置</button>
                        </div>
                    </div>

                    <div class="editor-panel">
                        <h3>配置说明</h3>
                        <div style="line-height: 1.8; color: #555;">
                            <p><strong>主要配置项：</strong></p>
                            <ul style="margin-left: 20px; margin-top: 10px;">
                                <li><code>system_prompt</code>: 系统提示词结构</li>
                                <li><code>core_capabilities</code>: 核心能力描述</li>
                                <li><code>working_guidelines</code>: 工作指南</li>
                                <li><code>scenarios</code>: 特殊场景提示词</li>
                            </ul>
                            <p style="margin-top: 15px;"><strong>💡 支持的占位符：</strong></p>
                            <ul style="margin-left: 20px; margin-top: 5px;">
                                <li><code>{name}</code>: AI助手名称</li>
                                <li><code>{name_en}</code>: 英文名</li>
                                <li><code>{role_description}</code>: 角色描述</li>
                                <li><code>{SKILLS_METADATA}</code>: 技能元数据</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div id="prompts-message"></div>
            </div>

            <!-- 预览标签页 -->
            <div id="preview-tab" class="tab-content">
                <div class="info-box">
                    <h4>👀 系统提示词预览</h4>
                    <ul>
                        <li>查看根据当前人设和提示词配置生成的完整系统提示词</li>
                        <li>点击"生成预览"查看最新效果</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 20px 0;">
                    <button class="btn-preview" onclick="generatePreview()" style="width: 200px;">生成预览</button>
                </div>

                <div class="preview-box" id="preview-content">
                    点击"生成预览"按钮查看系统提示词...
                </div>
                <div id="preview-message"></div>
            </div>
        </div>

        <script>
            // Tab switching
            function switchTab(tabName) {
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

                event.target.classList.add('active');
                document.getElementById(tabName + '-tab').classList.add('active');

                // Auto-load content when switching tabs
                if (tabName === 'personality' && !document.getElementById('personality-editor').value) {
                    loadPersonality();
                } else if (tabName === 'prompts' && !document.getElementById('prompts-editor').value) {
                    loadPrompts();
                }
            }

            // Show message
            function showMessage(elementId, message, isSuccess) {
                const messageDiv = document.getElementById(elementId);
                messageDiv.innerHTML = `<div class="message ${isSuccess ? 'success' : 'error'}">${message}</div>`;
                setTimeout(() => {
                    messageDiv.innerHTML = '';
                }, 5000);
            }

            // Load personality configuration
            async function loadPersonality() {
                try {
                    const response = await fetch('/api/personality');
                    if (response.ok) {
                        const data = await response.text();
                        document.getElementById('personality-editor').value = data;
                        showMessage('personality-message', '✅ 人设配置加载成功', true);
                    } else {
                        showMessage('personality-message', '❌ 加载失败: ' + response.statusText, false);
                    }
                } catch (error) {
                    showMessage('personality-message', '❌ 加载错误: ' + error.message, false);
                }
            }

            // Save personality configuration
            async function savePersonality() {
                try {
                    const content = document.getElementById('personality-editor').value;
                    const response = await fetch('/api/personality', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({content: content})
                    });

                    const result = await response.json();
                    if (response.ok) {
                        showMessage('personality-message', '✅ 保存成功！', true);
                    } else {
                        showMessage('personality-message', '❌ 保存失败: ' + result.detail, false);
                    }
                } catch (error) {
                    showMessage('personality-message', '❌ 保存错误: ' + error.message, false);
                }
            }

            // Load prompts configuration
            async function loadPrompts() {
                try {
                    const response = await fetch('/api/prompts');
                    if (response.ok) {
                        const data = await response.text();
                        document.getElementById('prompts-editor').value = data;
                        showMessage('prompts-message', '✅ 提示词配置加载成功', true);
                    } else {
                        showMessage('prompts-message', '❌ 加载失败: ' + response.statusText, false);
                    }
                } catch (error) {
                    showMessage('prompts-message', '❌ 加载错误: ' + error.message, false);
                }
            }

            // Save prompts configuration
            async function savePrompts() {
                try {
                    const content = document.getElementById('prompts-editor').value;
                    const response = await fetch('/api/prompts', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({content: content})
                    });

                    const result = await response.json();
                    if (response.ok) {
                        showMessage('prompts-message', '✅ 保存成功！', true);
                    } else {
                        showMessage('prompts-message', '❌ 保存失败: ' + result.detail, false);
                    }
                } catch (error) {
                    showMessage('prompts-message', '❌ 保存错误: ' + error.message, false);
                }
            }

            // Generate preview
            async function generatePreview() {
                try {
                    const response = await fetch('/api/preview');
                    if (response.ok) {
                        const result = await response.json();
                        document.getElementById('preview-content').textContent = result.system_prompt;
                        showMessage('preview-message', '✅ 预览生成成功！', true);
                    } else {
                        const error = await response.json();
                        showMessage('preview-message', '❌ 生成失败: ' + error.detail, false);
                    }
                } catch (error) {
                    showMessage('preview-message', '❌ 生成错误: ' + error.message, false);
                }
            }

            // Auto-load personality on page load
            window.addEventListener('DOMContentLoaded', () => {
                loadPersonality();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/personality")
async def get_personality():
    """Get current personality configuration"""
    personality_path = Config.find_config_file("personality.yaml")
    if not personality_path or not personality_path.exists():
        raise HTTPException(status_code=404, detail="Personality configuration file not found")

    with open(personality_path, encoding="utf-8") as f:
        content = f.read()

    return content


@app.post("/api/personality")
async def save_personality(data: dict):
    """Save personality configuration"""
    try:
        content = data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="Empty content")

        # Validate YAML format
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")

        # Find config file path
        personality_path = Config.find_config_file("personality.yaml")
        if not personality_path:
            # Create in user config directory
            user_config_dir = Path.home() / ".ye-linghua" / "config"
            user_config_dir.mkdir(parents=True, exist_ok=True)
            personality_path = user_config_dir / "personality.yaml"

        # Save to file
        with open(personality_path, "w", encoding="utf-8") as f:
            f.write(content)

        return JSONResponse({"status": "success", "path": str(personality_path)})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@app.get("/api/prompts")
async def get_prompts():
    """Get current prompts configuration"""
    prompts_path = Config.find_config_file("prompts.yaml")
    if not prompts_path or not prompts_path.exists():
        raise HTTPException(status_code=404, detail="Prompts configuration file not found")

    with open(prompts_path, encoding="utf-8") as f:
        content = f.read()

    return content


@app.post("/api/prompts")
async def save_prompts(data: dict):
    """Save prompts configuration"""
    try:
        content = data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="Empty content")

        # Validate YAML format
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")

        # Find config file path
        prompts_path = Config.find_config_file("prompts.yaml")
        if not prompts_path:
            # Create in user config directory
            user_config_dir = Path.home() / ".ye-linghua" / "config"
            user_config_dir.mkdir(parents=True, exist_ok=True)
            prompts_path = user_config_dir / "prompts.yaml"

        # Save to file
        with open(prompts_path, "w", encoding="utf-8") as f:
            f.write(content)

        return JSONResponse({"status": "success", "path": str(prompts_path)})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@app.get("/api/preview")
async def preview_system_prompt():
    """Generate and preview system prompt"""
    try:
        personality_path = Config.find_config_file("personality.yaml")
        prompts_path = Config.find_config_file("prompts.yaml")

        if not personality_path or not prompts_path:
            raise HTTPException(
                status_code=404, detail="Configuration files not found. Please ensure personality.yaml and prompts.yaml exist."
            )

        loader = PersonalityLoader(personality_path=personality_path, prompts_path=prompts_path)

        system_prompt = loader.generate_system_prompt()

        return JSONResponse({"status": "success", "system_prompt": system_prompt})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


def main():
    """Main entry point for web config interface"""
    import uvicorn

    print("🌸 Starting Ye Linghua Configuration Interface...")
    print("📍 Open http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
