import argparse
import functools
import os
import pathlib
import importlib.resources as pkg_resources

def on_button_recipe_clicked(b):
    # print(b)
    if b['new']:
        b.owner.icon = "check"
        b.owner.description = "Enabled"
        b.owner.button_style='success'
    else:
        b.owner.icon = ""
        b.owner.description = "Disabled"
        b.owner.button_style=''

def setup_ui(run_cmd):
    from ogscm.args import setup_args_parser
    from ogscm import recipes
    import ipywidgets as widgets

    parser = setup_args_parser()

    args_dict = {}
    for group in parser._action_groups:
        if group.title in ['positional arguments', 'optional arguments', 'Image deployment', 'Maintenance']:
            continue
        print(group.title)
        display(setup_args(group._group_actions, args_dict))

    dirname = pathlib.Path(__file__).parent.parent / "ogscm" / "recipes"
    tab = widgets.Tab()
    tabs = []
    tab_names = []
    for filename in sorted(os.listdir(dirname)):
        if filename.endswith(".py") and not filename.startswith("_"):
            parser = argparse.ArgumentParser(add_help=False)
            ldict = {"filename": filename}
            execute = False
            recipe_builtin = pkg_resources.read_text(recipes, filename)
            exec(compile(recipe_builtin, filename, "exec"), locals(), ldict)

            if filename == "compiler.py":
                button = widgets.ToggleButton(
                    value=True,
                    description='Enabled',
                    button_style='success',
                    icon = "check"
                )
            else:
                button = widgets.ToggleButton(
                    value=False,
                    description='Disabled',
                )
            button.observe(on_button_recipe_clicked, 'value')
            args_dict[filename] = button
            grid = setup_args(parser._actions, args_dict)
            tabs.append(widgets.VBox(children=[button, grid]))
            tab_names.append(filename)

    tab.children = tabs
    for idx, val in enumerate(tab_names):
        tab.set_title(idx, val)
    display(tab)

    button = widgets.Button(description="CREATE CONTAINER", button_style="primary", layout=widgets.Layout(width='100%', height='35px'))
    global out
    out = widgets.Output(layout={'border': '1px solid black'})
    display(button, out)

    button.on_click(functools.partial(on_button_clicked, out=out, args_dict=args_dict, run_cmd=run_cmd))

    return out

def setup_args(actions, args_dict):
    import ipywidgets as widgets
    items = []
    for arg in actions:
        name = arg.option_strings[0]
        help = arg.help or ""
        if arg.type == None:
            value = False
            if name in ["--build", "--convert"]:
                value = True
            widget = widgets.Checkbox(description=help, value=value)
        else:
            default_value = ""
            if name == "--build_args":
                default_value = "\"'--progress=plain'\""
            widget = widgets.Text(value=default_value , placeholder=f"{arg.default}", description="(?)", description_tooltip=help)
        items.append(widgets.Label(value=name))
        items.append(widget)
        args_dict[name] = widget
    gridbox = widgets.GridBox(
        children = items,
        layout = widgets.Layout(
            grid_template_columns='150px auto 150px auto',
            grid_template_rows='auto',
            grid_gap='10px 10px'))

    return gridbox

def create_cli(items):
    cli_string = ""
    recipes = ""
    for (k, v) in items:
        value = v.value
        if value == False:
            continue
        if k.endswith(".py"):
            recipes += f" {k}"
            continue
        if value != "":
            cli_string += f" {k}"
            if isinstance(value, str):
                cli_string += f" {value}"

    return f"{recipes}{cli_string}"

def on_button_clicked(b, out, args_dict, run_cmd):
    with out:
        out.clear_output()
        cli_string = create_cli(args_dict.items())
        cmd = f"ogscm {cli_string}"
        run_cmd(cmd)

from IPython.display import FileLink
import os
class DownloadFileLink(FileLink):
    html_link_str = "<a href='{link}' download={file_name}>{link_text}</a>"

    def __init__(self, path, file_name=None, link_text=None, *args, **kwargs):
        super(DownloadFileLink, self).__init__(path, *args, **kwargs)

        self.file_name = file_name or os.path.split(path)[1]
        self.link_text = link_text or self.file_name

    def _format_path(self):
        from html import escape
        fp = ''.join([self.url_prefix, escape(self.path)])
        return ''.join([self.result_html_prefix,
                        self.html_link_str.format(link=fp, file_name=self.file_name, link_text=self.link_text),
                        self.result_html_suffix])

def display_download_link(output):
    from pygments import highlight
    from pygments.lexers import DockerLexer
    from pygments.formatters import HtmlFormatter
    import IPython
    import re

    # Sif
    p = re.compile('.*Build.*: (.*\.sif)')
    m = p.search(output)
    print("Download container:")
    if m:
        sif_file = m.group(1)
        from ogscm.jupyter import DownloadFileLink
        import os
        display(DownloadFileLink(os.path.relpath(sif_file)))

    # Dockerfile
    p = re.compile('Created definition (.*)')
    m = p.search(output)
    dockerfile = m.group(1)

    with open(dockerfile) as f:
        code = f.read()

    formatter = HtmlFormatter()
    IPython.display.HTML('<style type="text/css">{}</style>{}'.format(
        formatter.get_style_defs('.highlight'),
        highlight(code, DockerLexer(), formatter)))
