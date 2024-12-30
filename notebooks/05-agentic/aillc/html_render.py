# %%
# Rendering html code

import re

html_template = """
<html>
<head>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/styles/default.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/highlight.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', (event) => {{ hljs.highlightAll(); }});
function copyCode(button) {{
    var code = button.parentNode.nextElementSibling.querySelector('code').innerText;
    navigator.clipboard.writeText(code);
    button.innerText = 'Copied!';
    setTimeout(() => {{ button.innerText = 'Copy'; }}, 2000);
}}
</script>
<style>
    .code-block {{ margin-bottom: 20px; border-radius: 5px; background-color: #f8f8f8; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
    .code-header {{ font-size: 0.85em; color: #888; padding: 5px 10px; display: flex; justify-content: space-between; align-items: center; border-top-left-radius: 5px; border-top-right-radius: 5px; }}
    pre {{ margin: 0; border-top: none; border-radius: 0 0 5px 5px; background-color: transparent; }}
    button {{ cursor: pointer; border: none; background-color: #eee; padding: 3px 8px; border-radius: 5px; }}
    button:hover {{ background-color: #ddd; }}
    .system {{ background-color: #CCCCCC; padding: 20px; margin: 10px; border-radius: 8px; }}
    .user {{ background-color: #D2E9FF; padding: 20px; margin: 10px; border-radius: 8px; }}
    .assistant {{ background-color: #F1D4D4; padding: 20px; margin: 10px; border-radius: 8px; }}
    .roleheader {{ padding-bottom: 10px; }}
    .role {{ font-weight: bold; padding-bottom: 10px; }}
    .tags {{ display: inline-block;
			background-color: #088F8F;
			border-radius: 4px;
			padding: 2px 10px;
			color: white;
			font-size: 0.8em; }}   

</style>
</head>
<body>
    {messages}
</body>
</html>
"""


def render_tags(msg):
    if 'tags' in msg and len(msg['tags']) > 0:
        tags = "&nbsp;".join([f'<span class="tags">{t}</span>' for t in msg['tags']])
    else:
        tags = ""
    return tags


def process_content(text):
    # Split the text into segments of code blocks and other text
    parts = re.split(r'```(.*?)```', text, flags=re.DOTALL)
    html_content = []
    is_code = False  # Toggle to keep track if the current part is code or not

    for part in parts:
        if is_code:  # This part is a code block
            if '\n' in part:  # Check if there's a language specified
                lang, code = part.split('\n', 1)
                lang = lang.strip()
            else:
                lang, code = None, part
            language_class = f' class="language-{lang}"' if lang else ' class="language-unknown"'
            lang_header = lang if lang else 'Unknown'
            html_content.append(f'<div class="code-block"><div class="code-header">{lang_header} <button onclick="copyCode(this)">Copy</button></div><pre><code{language_class} class="hljs">{code.strip()}</code></pre></div>')
        else:  # This part is regular text
            regular_content = part.strip().replace("\n", "<br>")
            #html_content.append(f'<p>{regular_content}</p>')
            html_content.append(f'{regular_content}')
        is_code = not is_code  # Toggle the is_code for the next part

    return ''.join(html_content)


def render_html_messages(names, messages, full):

    html_messages = ""
    for msg in messages:
        role = msg["role"]

        if role == 'system' and not full:
            continue
        content = msg["content"]

        html_messages += f'''
            <div class="{role}">
                <div class="roleheader"><div class="role">{names[role]}</div>{render_tags(msg)}</div>
                {process_content(content)}
            </div>'''

    result = html_template.format(messages=html_messages)
    return result


def render_html_chat(asker_name, responder_name, asker_messages, responder_messages, full=False):
    res = {}
    
    name = {
        'user': asker_name,
        'assistant': responder_name,
        'system':"system"
    }
    res['direct'] = render_html_messages(name, responder_messages, full)

    name = {
        'user':responder_name,
        'assistant':asker_name,
        'system':"system"
    }          
    res['invert'] = render_html_messages(name, asker_messages, full)
    
    return res




# %%

