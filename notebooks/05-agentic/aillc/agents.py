# %% 
# Working with agents

import os
from .utils import merge_dicts, read_md_replace_links, convert_to_specific_dict, md_to_dicts, extract_json_from_md
import json



# %%


class Agent:

    def __init__(self, root_path, agent_name, default_parameters = {"model":"gpt-3.5-turbo"}):
        self.root_path = root_path
        self.agent_name = agent_name
        self.md_file    = os.path.join(root_path, f"{agent_name}.md")

        md_content = read_md_replace_links(self.md_file, self.root_path)
        md_dict = convert_to_specific_dict(md_to_dicts(md_content))

        self.description = md_dict['rest']
        self.memory = md_dict['memory'].strip()
        self.parameters = merge_dicts([default_parameters] + extract_json_from_md(md_dict['parameters']))

    def system_message(self):
        if self.memory is not None and self.memory != '':
            return f"{self.description}\n# Notes to self\n\n{self.memory}"
        return self.description
    
    def save_md(self, md_filename):
        mem = "# Memory\n\n" + self.memory.strip()
        par = "# Parameters\n\n```json\n" + json.dumps(self.parameters, indent = 4) + "\n```\n"
        with open(md_filename, 'w') as f:
            f.write(f"{self.description.strip()}\n\n{mem}\n\n{par}")