import os
import glob
import yaml
import json
import re


class AlphaConvertAndGenerator:
    # default constructor
    def __init__(self, path):
        self.path = path
        self.file_name = "{0}-{1}-alpha"
        self.template = '''
resource "kubernetes_manifest" "{0}-{1}" {{
  provider = kubernetes-alpha

  manifest = {{
'''

    def run(self):
        self.looking_for_files()

    def looking_for_files(self):
        os.chdir(self.path)
        for file in glob.glob("*.y*ml"):
            open_file = open(file, "r")
            read_file = open_file.read()
            self.split_files(read_file)
            open_file.close()

    def split_files(self, file):
        splited = file.split("---")
        for separated in splited:
            if not separated:
                continue
            execution = self.transfer_yaml_to_hcl_with_terraform(separated)
            if not execution['name']:
                continue
            file_name = self.file_name.format(execution['kind'], execution['name'])
            template = self.template.format(execution['kind'], execution['name'])
            json_file = template + execution['file']
            data = self.json_file_processing_rewrites(json_file)
            self.write_file(file_name, data)

    def search_name_value_in_string(self, string, pattern):
        for matches in re.finditer(f'(?P<name>{pattern} = \")(?P<value>.*)\"', string):
            file_name = matches.group('value')
            rematched_name = re.sub(r'([\\/:.-])', r"-", file_name)
            return rematched_name

    def transfer_yaml_to_hcl_with_terraform(self, file):
        yaml_file = yaml.load(file, Loader=yaml.FullLoader)

        # Format json with double space limiting
        jsonned_file = json.dumps(yaml_file, indent=2, sort_keys=True)
        replace_double_dots = re.sub(r'(\":)', lambda m: format(m.group(1).replace(":", " =")), jsonned_file)
        replace_quotes = re.sub(r'(\")(\w+)(\")( =)', r"\2\4", replace_double_dots)
        remove_comas_at_the_end = re.sub(r',$', '', replace_quotes, flags=re.MULTILINE)
        name = self.search_name_value_in_string(remove_comas_at_the_end, 'name')
        kind = self.search_name_value_in_string(remove_comas_at_the_end, 'kind')

        # Makes double space indent at start of the string
        add_tabs = re.sub(r'(.*)', r"  \1", remove_comas_at_the_end)
        formated = add_tabs.split("\n", 1)[1]
        formated += "\n}\n"
        processing_list = {
            'file': formated,
            'name': name,
            'kind': kind.lower()
        }
        return processing_list

    def json_file_processing_rewrites(self, json_file):
        shielding_variables = re.sub(r'(\${.*})', '$\g<1>', json_file, flags=re.MULTILINE)
        remove_whitespaces_at_end = re.sub(r"[ \t]+$", '', shielding_variables, flags=re.MULTILINE)
        brackets_comma_parsed = re.sub(r'(?<=})(.*$\n\s*])', ',\g<0>', remove_whitespaces_at_end, flags=re.MULTILINE)
        bracers_comma_parsed = re.sub(r'(?<=})(.*$\n\s*{)', ',\g<0>', brackets_comma_parsed, flags=re.MULTILINE)
        looking_for_square_brackets = re.compile('(?s)= (\[\n\s+\".*?\s])(?=\s|$)', flags=re.MULTILINE)
        searching_data_in_square_brackets = re.compile(r'(?:.*\[)*(?:\s\s)([" *+-/\w=]+$)', flags=re.MULTILINE)
        found_bracers_parts = looking_for_square_brackets.findall(bracers_comma_parsed)

        # Empty array container
        subst_values_array = []
        found_values_array = []

        # Collecting data to be substituted
        for values in found_bracers_parts:
            found_values = searching_data_in_square_brackets.findall(values)
            if found_values:
                substituted = values
                for replace_value in found_values:
                    execute_subst = re.sub(replace_value, replace_value + ',', substituted, re.MULTILINE)
                    substituted = execute_subst
                subst_values_array.append(substituted)
                found_values_array.append('\\' + values)
        square_bracer_parced_file = bracers_comma_parsed
        subst_values_array = sorted(set(subst_values_array))
        found_values_array = sorted(set(found_values_array))

        # Precisely substituting the data inside square brackets
        for subst, found in zip(subst_values_array, found_values_array):
            parsed_file_bracers = re.sub(found, subst, square_bracer_parced_file, flags=re.MULTILINE)
            square_bracer_parced_file = parsed_file_bracers
        data = square_bracer_parced_file
        return data

    def write_file(self, file_name, data):
        with open(file_name + '.tf', 'w+') as the_file:
            the_file.write(data)


# Directory with yaml files
directory_path = '/files'

kubernetes_alpha_instance = AlphaConvertAndGenerator(directory_path)
kubernetes_alpha_instance.run()
