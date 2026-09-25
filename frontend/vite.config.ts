import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
export default defineConfig({root:root+'frontend',publicDir:root+'public',plugins:[react()],resolve:{alias:{'@':root}},define:{'process.env.NEXT_PUBLIC_FLOWOPS_API':JSON.stringify('/api')},css:{postcss:root},build:{outDir:root+'frontend-dist',emptyOutDir:true},server:{host:'127.0.0.1',port:5173,strictPort:true,proxy:{'/api':{target:'http://127.0.0.1:8000',changeOrigin:true,ws:true,rewrite:p=>p.replace(/^\/api/,'')},'/ws':{target:'ws://127.0.0.1:8000',ws:true}}}});
