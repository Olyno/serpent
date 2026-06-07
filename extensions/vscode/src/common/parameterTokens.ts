import {
    type DocumentSemanticTokensProvider,
    type ProviderResult,
    type SemanticTokens,
    SemanticTokensBuilder,
    SemanticTokensLegend,
    type TextDocument,
} from 'vscode';

const PARAMETER_LEGEND = new SemanticTokensLegend(['parameter'], ['declaration']);
const FUNCTION_RE = /^(\s*)def\s+[A-Za-z_]\w*\s*\(([^)]*)\)\s*(?:->\s*[^:]+)?\s*:/gm;
const PARAMETER_RE = /\b([A-Za-z_]\w*)\s*:/g;

export const VYPER_PARAMETER_LEGEND = PARAMETER_LEGEND;

function isBodyLine(line: string, functionIndent: number): boolean {
    if (line.trim() === '' || line.trimStart().startsWith('#')) {
        return true;
    }

    return line.search(/\S/) > functionIndent;
}

function addParameterToken(
    builder: SemanticTokensBuilder,
    line: number,
    char: number,
    length: number,
    declaration = false,
): void {
    builder.push(line, char, length, 0, declaration ? 1 : 0);
}

export function createParameterSemanticTokensProvider(): DocumentSemanticTokensProvider {
    return {
        provideDocumentSemanticTokens(document: TextDocument): ProviderResult<SemanticTokens> {
            const builder = new SemanticTokensBuilder(PARAMETER_LEGEND);
            const text = document.getText();
            const lines = text.split(/\r?\n/);

            for (const match of text.matchAll(FUNCTION_RE)) {
                const functionStart = match.index ?? 0;
                const functionLine = text.slice(0, functionStart).split(/\r?\n/).length - 1;
                const functionIndent = match[1].length;
                const paramsSource = match[2];
                const paramsStartColumn = match[0].indexOf('(') + 1;
                const names = new Set<string>();

                for (const param of paramsSource.matchAll(PARAMETER_RE)) {
                    const name = param[1];
                    const offset = param.index ?? 0;
                    names.add(name);
                    addParameterToken(builder, functionLine, paramsStartColumn + offset, name.length, true);
                }

                if (names.size === 0) {
                    continue;
                }

                for (let line = functionLine + 1; line < lines.length; line++) {
                    const sourceLine = lines[line];
                    if (!isBodyLine(sourceLine, functionIndent)) {
                        break;
                    }

                    for (const name of names) {
                        const usageRe = new RegExp(`\\b${name}\\b`, 'g');
                        for (const usage of sourceLine.matchAll(usageRe)) {
                            addParameterToken(builder, line, usage.index ?? 0, name.length);
                        }
                    }
                }
            }

            return builder.build();
        },
    };
}
