import fs from 'fs';
import { getProviders, getModels } from '@mariozechner/pi-coding-agent/node_modules/@mariozechner/pi-ai/index.js';

const providers = getProviders();
console.log('Built-in providers count:', providers.length);
console.log('Ollama in built-in:', providers.includes('ollama'));

// Check what happens with openai-completions
console.log('\nOpenAI-completions models:', getModels('openai-completions')?.length || 0);
