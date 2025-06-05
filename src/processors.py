from .interfaces import IContentProcessor
from bs4 import BeautifulSoup
import re
import html

class CodeProcessor(IContentProcessor):
    def process(self, content: str) -> str:
        if "<code>" not in content:
            return content
        return re.sub(
            r'(<code>)(.*?)(</code>)',
            lambda m: f"<code>{html.escape(m.group(2))}</code>",
            content
        )

class ListProcessor(IContentProcessor):
    def process(self, content: str) -> str:
        if not any(tag in content for tag in ['<ul>', '<ol>']):
            return content
        content = re.sub(
            r'\{(.*?)\}',
            lambda m: f"<li>{'</li><li>'.join(m.group(1).split(','))}</li>",
            content
        )
        return f"<ul>{content}</ul>" if not ("<ul>" in content or "<ol>" in content) else content

class TableProcessor(IContentProcessor):
    def process(self, content: str) -> str:
        if "<table>" not in content:
            return content

        content = content.replace('<table>', '').replace('</table>', '').strip()
        lines = [line.strip() for line in content.split('\n') if line.strip()]

        html_parts = ['<table class="content-table">']
        tbody_open = False

        for line in lines:
            if line.startswith('<thead>'):
                html_parts.append(self._process_header(line))
                tbody_open = True  # _process_header opens <tbody>
            elif line.startswith('<tbody>') or line.startswith('</tbody>'):
                # Skip explicit tbody tags from the input
                continue
            elif '[[' in line and ']]' in line:
                if not tbody_open:
                    html_parts.append('<tbody>')
                    tbody_open = True
                html_parts.append(self._process_row(line))

        if tbody_open:
            html_parts.extend(['</tbody>'])
        html_parts.append('</table>')
        table_html = '\n'.join(html_parts)
        # Envelopper le tableau dans un div responsive
        return f'<div class="table-responsive">\n{table_html}\n</div>'

    def _process_header(self, line: str) -> str:
        header_content = line.replace('<thead>', '').replace('</thead>', '')
        if '[[' in header_content:
            cells = [cell.strip() for cell in header_content.strip('[]').split('|')]
            return '<thead><tr>' + ''.join(f'<th scope="col">{cell}</th>' for cell in cells) + '</tr></thead><tbody>'
        return ''

    def _process_row(self, line: str) -> str:
        cells = [cell.strip() for cell in line.strip('[]').split('|')]
        first_cell = f'<td class="row-header">{cells[0]}</td>'
        other_cells = ''.join(f'<td>{cell}</td>' for cell in cells[1:])
        return f'<tr>{first_cell}{other_cells}</tr>'

