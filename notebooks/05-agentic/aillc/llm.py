# %%
# Reading data

import json
from openai import OpenAI
from openai import BadRequestError
import anthropic
from json import JSONDecodeError

# %%

openai_client = None
anthropic_client = None

level_3_openai_model = {
    'vendor': 'OpenAI',
    'level' : 3
}
level_4_openai_model = {
    'vendor': 'OpenAI',
    'level' : 4
}
human_model = {
    'vendor' : 'human',
    'level' : 5
}
claude_haiku = {
    'vendor' : 'Anthropic',
    'level' : 3,
    'name'  : 'claude-3-haiku-20240307',
    'max_tokens' : 4096
}
claude_sonnet = {
    'vendor' : 'Anthropic',
    'level' : 3,
    'name'  : 'claude-sonnet-4-6',
    'max_tokens' : 4096
}
claude_opus = {
    'vendor' : 'Anthropic',
    'level' : 4,
    'name'  : 'claude-opus-4-6',
    'max_tokens' : 4096
}


models = {
    'gpt-4-turbo-preview': level_4_openai_model.copy(),
    'gpt-4-turbo': level_4_openai_model.copy(), 
    'gpt-4o': level_4_openai_model.copy(),
    'gpt-3.5-turbo': level_3_openai_model.copy(),
    'gpt-5.2': level_4_openai_model.copy(),

    'claude-haiku' : claude_haiku.copy(),
    'claude-sonnet' : claude_sonnet.copy(),
    'claude-opus' : claude_opus.copy(),
    'claude-3-5-sonnet-20240620' : claude_sonnet.copy(),
    'claude-sonnet-4-6' : claude_sonnet.copy(),

    'human' : human_model.copy()
}

for model in models:
    if 'name' not in models[model]:
        models[model]['name'] = model




# %%

class ModelResponseError(Exception):
    pass

class LLM:


    @staticmethod
    def init_openai(config_file = '.env/openai.json'):
        global openai_client
        if openai_client is None:
            with open(config_file, 'r') as file:
                openai_client = OpenAI(api_key = json.load(file)['key'])
    
    @staticmethod
    def init_anthropic(config_file = '.env/anthropic.json'):
        global anthropic_client
        if anthropic_client is None:
            with open(config_file, 'r') as file:
                anthropic_client = anthropic.Anthropic(api_key=json.load(file)['key'])
    
    
    @staticmethod
    def convert_openai_to_anthropic_format(messages:list):
        """OpenAI and Anthropic have different message formats. For Anthropic, system message should be 
        set expliticly. For OpenAI it's part of all messages. The LLM class works with OpenAI format
        """


        system_output = "\n".join(d.get("content", "") for d in messages if d.get("role") == "system")
        non_system_output = [{"role": d.get("role"), "content":d.get("content")} for d in messages if d.get("role") != "system"]
        return (system_output, non_system_output)



    @staticmethod
    def get_response(messages, model_name, json_output = False):

        model = models[model_name]
        
        if model['vendor'] == 'OpenAI':
            LLM.init_openai()
            
            if json_output:
                # TODO: some of the moels do not support json output
                try:
                    response = openai_client.chat.completions.create(
                        model = model['name'],
                        messages = messages,
                        response_format = {'type':'json_object'}
                    )
                except BadRequestError as e:
                    raise ModelResponseError(e)
                
                try:
                    return json.loads(response.choices[0].message.content)
                except JSONDecodeError as e:
                    print("json decoding error!")
                    print(response)
                    print(response.choices[0].message.content)
                    raise e

            else:
                response = openai_client.chat.completions.create(
                    model = model['name'],
                    messages = messages
                )
                return response.choices[0].message.content
        
        elif model['vendor'] == 'Anthropic':
            LLM.init_anthropic()
            msg = LLM. convert_openai_to_anthropic_format(messages)
            response = anthropic_client.messages.create(
                model = model['name'],
                max_tokens= model['max_tokens'],
                messages = msg[1],
                system = msg[0]
            )
            text = response.content[0].text
            if json_output:
                # Extract JSON from response text
                import re
                # Try to find JSON in code blocks first
                pattern = r"```(?:json)?\s*([\s\S]*?)```"
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        return json.loads(match.strip())
                    except JSONDecodeError:
                        continue
                # Try parsing the whole response as JSON
                try:
                    return json.loads(text.strip())
                except JSONDecodeError:
                    raise ModelResponseError(f"Failed to extract JSON from Anthropic response: {text[:500]}")
            return text

                
        elif model['vendor'] == 'human':
            response = input("Your answer:")
            return response
        else:
            raise Exception(f"Model {model_name} is not implemented")


    @staticmethod
    def get_model_level(model_name):
        return models[model_name]['level']

    