# HOMI Compiler

A Python compiler for **HOMI**, a Portuguese-language DSL for writing Home Assistant automations. It turns `.homi` source files into YAML and includes a local web interface for inspecting the compilation process.

## What it implements

- Lexical analysis with PLY.
- Parsing and abstract syntax tree (AST) construction.
- Semantic analysis, a symbol table, errors and warnings.
- YAML generation for Home Assistant automations.
- A command-line interface and a browser interface showing tokens, the AST, diagnostics and generated YAML.

## Example

Turn on a living-room light when a motion sensor changes to `on`:

```text
automacao "Sala - ligar luz com movimento"
    quando binary_sensor.sala_motion mudar para "on"
    entao
        ligar light.luz_sala
    fim
```

Generated YAML, with the generated ID omitted:

```yaml
- alias: Sala - ligar luz com movimento
  description: ''
  triggers:
    - entity_id:
        - binary_sensor.sala_motion
      to: 'on'
      trigger: state
  conditions: []
  actions:
    - action: light.turn_on
      metadata: {}
      data: {}
      target:
        entity_id: light.luz_sala
  mode: single
```

The complete [source example](exemplos/exemplo1.homi) and [saved YAML output](exemplos/saida1.yaml) are included in the repository. The `exemplos/` directory also contains valid programs and syntax/semantic error cases.

## Getting started

Requires Python 3 and the `ply` and `PyYAML` packages.

```bash
git clone https://github.com/JoaoVtrxx/compilador-homi.git
cd compilador-homi
python -m venv .venv
```

Activate the virtual environment:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`

Install the dependencies:

```bash
python -m pip install ply PyYAML
```

### Command line

Run from the repository root:

```bash
python main.py exemplos/exemplo1.homi -o saida.yaml
```

Add `--verbose` to inspect tokens and semantic-analysis details. Omit `-o` to display the generated YAML in the terminal.

### Web interface

```bash
python web_gui/gui_server.py
```

Open **http://localhost:8000** to load an example or enter HOMI code and inspect the compiler's output. Stop the server with `Ctrl+C`.

## Project structure

| File or directory | Purpose |
| --- | --- |
| `A_GLC.txt` | Language grammar |
| `B_lexer.py` | Tokens and lexical analysis |
| `C_parser.py` | Parser |
| `D_semantic.py` | Semantic analysis and symbol table |
| `E_codegen.py` | Home Assistant YAML generation |
| `F_ast_nodes.py` | AST node definitions |
| `main.py` | Command-line entry point |
| `web_gui/` | Local HTTP server and browser interface |
| `exemplos/` | Sample HOMI programs and YAML outputs |

Built with Python, PLY, PyYAML and Python's standard-library HTTP server.
