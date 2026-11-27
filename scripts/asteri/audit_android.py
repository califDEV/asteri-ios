"""Reproducible source inventory. Discovery is deliberately not marked as implementation."""
import argparse
import ast
import collections
import json
import re
import subprocess
from pathlib import Path

CONFIG = 'TMessagesProj/src/main/java/com/exteragram/messenger/ExteraConfig.kt'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, encoding='utf-8')


def tree(root):
    result = {}
    for line in git(root, 'ls-tree', '-r', 'HEAD').splitlines():
        metadata, path = line.split('\t', 1)
        mode, kind, sha = metadata.split()
        result[path] = {'mode': mode, 'kind': kind, 'sha': sha}
    return result


def inventory(android, official):
    android_tree, official_tree = tree(android), tree(official)
    prefs = []
    sources = sorted(path for path in android_tree if '/com/exteragram/messenger/' in path
                     and path.endswith('Config.kt'))
    for source in sources:
        group = Path(source).stem
        for number, line in enumerate((android / source).read_text(encoding='utf-8').splitlines(), 1):
            if line.startswith('// '):
                group = line[3:].strip()
            match = re.match(r'\s*(?:private\s+)?var\s+(\w+)\s+by\s+(\w+Pref)\((.*)', line)
            if match:
                name, kind, initial = match.groups()
                prefs.append({'name': name, 'type': kind, 'declaration_start': initial,
                              'group': group, 'line': number, 'source': source,
                              'references': [], 'reference_count': 0})
    by_token = {}
    for pref in prefs:
        name = pref['name']
        title = name[0].upper() + name[1:]
        for token in (name, 'get' + title, 'set' + title, 'is' + title):
            by_token.setdefault(token, []).append(pref)
    matcher = re.compile(r'\b(?:' + '|'.join(map(re.escape, by_token)) + r')\b')
    custom_files, python_modules = [], []
    for path in android_tree:
        if '/com/exteragram/messenger/' in path and path.endswith(('.kt', '.java')):
            custom_files.append(path)
        if path.startswith('TMessagesProj/src/') and '/java/' in path and path.endswith(('.kt', '.java')):
            text = (android / path).read_text(encoding='utf-8', errors='replace')
            if path != CONFIG:
                for number, line in enumerate(text.splitlines(), 1):
                    for token in set(matcher.findall(line)):
                        for pref in by_token[token]:
                            if path == pref['source']:
                                continue
                            pref['reference_count'] += 1
                            if len(pref['references']) < 8:
                                pref['references'].append({'path': path, 'line': number})
        if path.startswith('plugins-pysdk/src/') and path.endswith('.py'):
            parsed = ast.parse((android / path).read_text(encoding='utf-8'), filename=path)
            imports = sorted({node.module for node in ast.walk(parsed)
                              if isinstance(node, ast.ImportFrom) and node.module})
            python_modules.append({'path': path, 'imports': imports})
    base = ast.parse((android / 'plugins-pysdk/src/base_plugin.py').read_text(encoding='utf-8'))
    api = next(node for node in base.body if isinstance(node, ast.ClassDef) and node.name == 'BasePlugin')
    changes = []
    for path in sorted(android_tree.keys() | official_tree.keys()):
        left, right = official_tree.get(path), android_tree.get(path)
        if left != right:
            changes.append({'path': path, 'change': 'added' if left is None else 'deleted' if right is None else 'modified',
                            'official': left, 'extera': right})
    return {
        'android_commit': git(android, 'rev-parse', 'HEAD').strip(),
        'official_commit': git(official, 'rev-parse', 'HEAD').strip(),
        'comparison': 'Git tree/blob SHA comparison; matching release 13.2.2 (7303). Not a semantic diff.',
        'changes_by_type': dict(collections.Counter(x['change'] for x in changes)),
        'custom_source_files': custom_files, 'preferences': prefs, 'sdk_modules': python_modules,
        'preferences_by_source': dict(collections.Counter(p['source'] for p in prefs)),
        'base_plugin_methods': [{'name': n.name, 'line': n.lineno} for n in api.body
                                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
        'android_upstream_changes': changes,
    }


def source_link(commit, path, line=None):
    return f'https://github.com/exteraSquad/exteraGram/blob/{commit}/{path}' + (f'#L{line}' if line else '')


def matrix(data, statuses=None):
    statuses = statuses or {}
    lines = ['# Feature matrix — source discovery and native integration', '',
             f'Android pin: `{data["android_commit"]}`. Official comparison: `{data["official_commit"]}`.', '',
             'This reproducible inventory covers delegated preferences in ExteraConfig, AiConfig, DebugConfig',
             'and PillStackConfig. A source reference',
             'may be an import, UI binding or behavior; it is not proof that the behavior was audited end to end.',
             'Additional subsystems and non-preference functions are tracked in ANDROID_ANALYSIS.md.',
             'Phase 2 remains in progress. Native utility tests, app integration and device evidence are tracked separately.',
             'No row is claimed as a completed, device-tested iOS feature port.', '',
             '| Feature / key | Description | Android source | Dependencies / source references | Telegram-iOS analog | Port plan | Implementation | Testing | iOS limitations |',
             '|---|---|---|---|---|---|---|---|---|']
    candidates = {
        'General': 'SettingsUI / TelegramStringFormatting / PeerInfo',
        'Appearance': 'SettingsUI/Themes / TelegramUIPreferences / TelegramUI',
        'Chats': 'TelegramUI chat components / TelegramCore',
        'Blur Preferences': 'Display / ContextUI / NavigationBar',
        'Icon Packs': 'PresentationResources / native asset catalogs',
        'Data export': 'TelegramCore / Files import-export',
        'Other': 'SettingsUI / BrowserUI',
    }
    for pref in data['preferences']:
        refs = '; '.join(f'[{r["path"].split("/")[-1]}:{r["line"]}]({source_link(data["android_commit"], r["path"], r["line"])})'
                         for r in pref['references'][:3]) or 'No external lexical reference found'
        desc = f'{pref["group"]}; persisted {pref["type"]}'
        analog = candidates.get(pref['group'], 'Requires per-feature iOS mapping') + ' (candidate, unverified)'
        status = statuses.get(pref['name'], {})
        desc = status.get('description', desc)
        analog = status.get('analog', analog)
        plan = status.get('plan', 'Audit consumer logic, implement native behavior after baseline, add behavior tests')
        implementation = status.get('implementation', 'Discovered; not ported')
        testing = status.get('testing', 'Not run on iOS')
        limitations = status.get('limitations', 'Requires individual platform assessment')
        label = Path(pref['source']).name
        lines.append(f'| `{pref["name"]}` | {desc} | [{label}:{pref["line"]}]({source_link(data["android_commit"], pref["source"], pref["line"])}) | {refs} | {analog} | {plan} | {implementation} | {testing} | {limitations} |')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--android', required=True, type=Path)
    parser.add_argument('--official', required=True, type=Path)
    parser.add_argument('--docs', required=True, type=Path)
    args = parser.parse_args()
    data = inventory(args.android, args.official)
    directory = args.docs / 'audit'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'android-inventory.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    status_path = args.docs / 'audit/port-status.json'
    statuses = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
    (args.docs / 'FEATURE_MATRIX.md').write_text(matrix(data, statuses), encoding='utf-8')
    print(json.dumps({'preferences': len(data['preferences']), 'custom_source_files': len(data['custom_source_files']),
                      'sdk_modules': len(data['sdk_modules']), 'preferences_by_source': data['preferences_by_source'],
                      'changes': data['changes_by_type']}, indent=2))
