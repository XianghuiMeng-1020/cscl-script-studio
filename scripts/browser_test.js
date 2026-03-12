#!/usr/bin/env node

/**
 * 临时脚本用于测试浏览器MCP工具
 * 这个脚本将在测试完成后删除
 */

const { spawn } = require('child_process');
const path = require('path');

async function callMcpTool(toolName, args) {
  return new Promise((resolve, reject) => {
    const request = {
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      }
    };

    console.log('Calling MCP tool:', toolName, 'with args:', JSON.stringify(args));
    
    // 由于我们无法直接调用MCP服务器,让我们输出请求
    console.log('Request:', JSON.stringify(request));
    resolve({ success: true });
  });
}

async function main() {
  const toolName = process.argv[2] || 'browser_lock';
  const viewId = process.argv[3] || 'fc8157';
  
  await callMcpTool(toolName, { viewId });
}

main().catch(console.error);
