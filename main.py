#!/usr/bin/env python3
# main.py
# Pipeline unificado do compilador Homi.
# Uso: python3 main.py <arquivo.homi> [-o <saida.yaml>] [--verbose]

import sys
import argparse

from lexer import lexer
from parser import parse
from semantic import AnalisadorSemantico
from codegen import GeradorYAML


def main():
    # ============================================================
    # 1. Argumentos de linha de comando
    # ============================================================
    arg_parser = argparse.ArgumentParser(
        description='Compilador Homi — Traduz scripts .homi para YAML do Home Assistant.',
        epilog='Exemplo: python3 main.py exemplo.homi -o automacao.yaml --verbose',
    )
    arg_parser.add_argument('arquivo', help='Arquivo de entrada .homi')
    arg_parser.add_argument('-o', '--output', help='Arquivo de saída .yaml (padrão: stdout)')
    arg_parser.add_argument('--verbose', action='store_true', help='Mostra detalhes de cada fase')
    args = arg_parser.parse_args()

    # ============================================================
    # 2. Leitura do arquivo de entrada
    # ============================================================
    try:
        with open(args.arquivo, 'r', encoding='utf-8') as f:
            codigo_fonte = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{args.arquivo}' não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        sys.exit(1)

    print("=" * 65)
    print("  COMPILADOR HOMI — Pipeline de Compilação")
    print("=" * 65)
    print(f"  Arquivo: {args.arquivo}")
    print()

    # ============================================================
    # FASE 1: Análise Léxica (Scanner)
    # ============================================================
    print("─── FASE 1: Análise Léxica ──────────────────────────────────────")

    if args.verbose:
        # Mostra tokens
        lexer.input(codigo_fonte)
        lexer.lineno = 1
        tokens_list = []
        print(f"  {'Linha':>5s} | {'Token':<17s} | Valor")
        print("  " + "-" * 50)
        for tok in lexer:
            tokens_list.append(tok)
            print(f"  {tok.lineno:5d} | {tok.type:<17s} | {tok.value!r}")
        print(f"\n  Total: {len(tokens_list)} tokens reconhecidos.")
    else:
        print("  [OK] Tokens processados (use --verbose para detalhes).")

    print()

    # ============================================================
    # FASE 2: Análise Sintática (Parser SLR)
    # ============================================================
    print("─── FASE 2: Análise Sintática (SLR) ─────────────────────────────")

    ast, erros_sintaticos = parse(codigo_fonte)

    if erros_sintaticos:
        print(f"\n  ✗ {len(erros_sintaticos)} erro(s) sintático(s) encontrado(s).")
        for e in erros_sintaticos:
            print(f"    {e}")
        print("\n  Compilação interrompida devido a erros sintáticos.")
        sys.exit(1)

    if ast is None:
        print("  ✗ Falha na análise sintática (AST nula).")
        sys.exit(1)

    print(f"  ✓ AST construída com sucesso.")
    print(f"    Automações encontradas: {len(ast.automacoes)}")
    for i, auto in enumerate(ast.automacoes, 1):
        cond_str = "com condição" if auto.condicao else "sem condição"
        print(f"    [{i}] \"{auto.alias}\" — "
              f"{len(auto.gatilhos)} gatilho(s), "
              f"{len(auto.acoes)} ação(ões), {cond_str}")

    print()

    # ============================================================
    # FASE 3: Análise Semântica
    # ============================================================
    print("─── FASE 3: Análise Semântica ───────────────────────────────────")

    analisador = AnalisadorSemantico()
    erros_semanticos, avisos = analisador.analisar(ast)

    if args.verbose:
        analisador.imprimir_tabela_simbolos()

    if avisos:
        print(f"\n  ⚠ {len(avisos)} aviso(s):")
        for a in avisos:
            print(f"    {a}")

    if erros_semanticos:
        print(f"\n  ✗ {len(erros_semanticos)} erro(s) semântico(s):")
        for e in erros_semanticos:
            print(f"    {e}")
        print("\n  Compilação interrompida devido a erros semânticos.")
        sys.exit(1)

    print(f"  ✓ Análise semântica concluída sem erros.")
    print()

    # ============================================================
    # FASE 4: Geração de Código YAML
    # ============================================================
    print("─── FASE 4: Geração de Código YAML ──────────────────────────────")

    gerador = GeradorYAML()
    yaml_saida = gerador.gerar(ast)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(yaml_saida)
        print(f"  ✓ YAML gerado e salvo em: {args.output}")
    else:
        print(f"  ✓ YAML gerado (saída abaixo):")
        print()
        print("─── INÍCIO DO YAML ──────────────────────────────────────────────")
        print(yaml_saida)
        print("─── FIM DO YAML ─────────────────────────────────────────────────")

    print()
    print("=" * 65)
    print("  ✓ COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 65)


if __name__ == '__main__':
    main()
