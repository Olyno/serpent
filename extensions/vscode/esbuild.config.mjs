/**
 * Configuration esbuild pour l'extension Serpent VSCode.
 * Génère deux bundles : desktop (Node) et web (browser).
 */

import { context, build } from 'esbuild';
import { readFileSync } from 'node:fs';

const isWatch = process.argv.includes('--watch');
const isProduction = process.argv.includes('--production');

/** Options de base partagées entre desktop et web */
const baseOptions = {
    bundle: true,
    minify: isProduction,
    sourcemap: !isProduction,
    external: ['vscode'],
    platform: 'node',
    target: 'ES2022',
    tsconfig: 'tsconfig.json',
    loader: { '.node': 'copy' },
};

/** Bundle desktop (Node.js, extension principale) */
const desktopConfig = {
    ...baseOptions,
    entryPoints: ['src/extension.ts'],
    outfile: 'dist/extension.js',
    format: 'cjs',
    platform: 'node',
    external: ['vscode', 'vscode-languageclient/node'],
};

/** Bundle web (navigateur, vscode.dev) */
const webConfig = {
    ...baseOptions,
    entryPoints: ['src/extension.web.ts'],
    outfile: 'dist/web/extension.js',
    format: 'cjs',
    platform: 'browser',
    mainFields: ['browser', 'module', 'main'],
    conditions: ['browser'],
    external: ['vscode'],
    alias: {
        'vscode-languageclient/node': 'vscode-languageclient',
    },
};

if (isWatch) {
    // Mode watch : reconstruit automatiquement
    const desktopCtx = await context(desktopConfig);
    const webCtx = await context(webConfig);
    await desktopCtx.watch();
    await webCtx.watch();
    console.log('[esbuild] Mode watch actif — surveillance des fichiers src/');
} else {
    // Build unique
    try {
        await build(desktopConfig);
        console.log('[esbuild] Bundle desktop construit → dist/extension.js');
        await build(webConfig);
        console.log('[esbuild] Bundle web construit → dist/web/extension.js');
    } catch (err) {
        console.error('[esbuild] Erreur de compilation :', err);
        process.exit(1);
    }
}
