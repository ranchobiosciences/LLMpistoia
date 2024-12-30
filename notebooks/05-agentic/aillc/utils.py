# %%

import os
import re
import json


# %% Various utils to work with md files etc


def merge_dicts(dict_list):
    merged_dict = {}
    for d in dict_list:
        merged_dict.update(d)
    return merged_dict



def read_md_replace_links(md_path, root_path):
    def md_file_content(match):
        md_path = os.path.join(root_path, match.group(1))
        if os.path.isfile(md_path):
            with open(md_path, 'r') as f:
                return f.read()
        return ''
    with open(md_path, 'r') as file:
        content = file.read()
    content = re.sub(r'\[.*?\]\((.*?\.md)\)', md_file_content, content)
    return content



def convert_to_specific_dict(sections):
    output = {'rest': '', 'memory': '', 'parameters': ''}

    for section in sections:
        header = section['header']
        content = section['content']

        if header == 'Memory':
            output['memory'] += content
        elif header == 'Parameters':
            output['parameters'] += content
        else:
            output['rest'] += (f"# {header}\n" if header else '') + content

    return output



def md_to_dicts(content):
    sections = []
    current_section = {'header': None, 'content': ''}

    for line in content.split('\n'):
        if line.startswith('# '):
            if current_section['header'] is not None or current_section['content']:
                sections.append(current_section)
            current_section = {'header': line[2:].strip(), 'content': ''}
        else:
            current_section['content'] += line + '\n'

    if current_section['header'] is not None or current_section['content']:
        sections.append(current_section)

    return sections



def extract_json_from_md(content):
    json_fragments = []
    in_json_block = False
    json_buffer = ''

    for line in content.split('\n'):
        if line.strip() == '```json':
            in_json_block = True
            json_buffer = ''
        elif line.strip() == '```' and in_json_block:
            in_json_block = False
            try:
                json_fragments.append(json.loads(json_buffer))
            except json.JSONDecodeError:
                pass  # handle or log invalid JSON
        elif in_json_block:
            json_buffer += line + '\n'

    return json_fragments

