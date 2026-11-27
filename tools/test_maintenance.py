"""Регрессия области maintenance; HTTP-проверка реального сервера выполняется отдельно."""
from pathlib import Path
import re

text = (Path(__file__).resolve().parents[1] / '.deploy/htaccess').read_text(encoding='utf-8')
MARKER = '# ---------- режим «сайт временно закрыт» ----------'
if MARKER not in text:   # режим снят 24.11.2026: регрессия проверяется, только когда блок есть
    print('maintenance host/path regression: SKIPPED (блок 503 не включён в .deploy/htaccess)')
    raise SystemExit(0)
block = text.split(MARKER, 1)[1].split(
    '# ---------- редиректы ----------', 1)[0]
host_match = re.search(r'^  RewriteCond %\{HTTP_HOST\} (\S+) \[NC\]$', block, re.M)
uri_match = re.search(r'^  RewriteCond %\{REQUEST_URI\} !(\S+) \[NC\]$', block, re.M)
header_match = re.search(r'^  SetEnvIfNoCase Host (\S+) (\w+)$', block, re.M)
assert host_match and uri_match and header_match, 'нет ограничений maintenance по хосту/пути'
host, uri = host_match.group(1), uri_match.group(1)
header_host, env = header_match.groups()
assert host == header_host, '503 и Retry-After должны иметь одну область хостов'
assert 'ErrorDocument 503 /maintenance.html' in block
assert 'RewriteRule .* - [R=503,L]' in block
assert f'Header always set Retry-After "3600" env={env}' in block
# Внутренний ErrorDocument на www не должен подменять 503 каноническим 301.
redirects = text.split('# ---------- редиректы ----------', 1)[1]
assert re.search(r'RewriteCond %\{ENV:REDIRECT_STATUS\} !\^503\$\s+'
                 r'RewriteCond %\{HTTP_HOST\} \^www', redirects)

cases = 0
for name, production in [
    ('test.blazhevich.tech', False), ('test.blazhevich.tech:443', False),
    ('blazhevich.tech', True), ('www.blazhevich.tech', True),
    ('BLAZHEVICH.TECH:443', True), ('WWW.BLAZHEVICH.TECH:80', True),
    ('blazhevich.tech.example.org', False), ('other.example.org', False),
]:
    for path, maintenance in [('/', False), ('/works.html', False),
                              ('/en/moscow.html', False), ('/missing', False),
                              ('/maintenance.html', True), ('/MAINTENANCE.HTML', True)]:
        matched = bool(re.search(host, name, re.I))
        blocked = matched and not re.search(uri, path, re.I)
        assert bool(blocked) == (production and not maintenance), (name, path)
        assert bool(re.search(header_host, name, re.I)) == production, name
        cases += 1
print(f'maintenance host/path regression: {cases} cases passed (not an HTTP test)')
