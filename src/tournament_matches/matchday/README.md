# Matchday Module

Este módulo fornece funcionalidades para organizar partidas de futebol em rodadas adequadas, garantindo que cada time jogue exatamente uma vez por rodada.

## Estrutura do Módulo

```
matchday/
├── __init__.py              # Exports principais do módulo
├── matchday_organizer.py    # Lógica principal de organização
├── quality_analyzer.py      # Análise de qualidade das rodadas
├── utils.py                 # Funções utilitárias
├── example.py              # Exemplos de uso
└── README.md               # Esta documentação
```

## Funcionalidades Principais

### 1. Organização de Rodadas

- **`organize_tournament_rounds(df, tournament_id)`**: Organiza as partidas de um torneio específico em rodadas
- **`process_all_tournaments(df)`**: Processa todos os torneios em um dataset

### 2. Análise de Qualidade

- **`analyze_round_quality(df, tournament_id)`**: Analisa a qualidade da organização de um torneio
- **`generate_quality_report(df, output_file)`**: Gera relatório completo de qualidade

### 3. Utilitários

- **`parse_date(date_str)`**: Converte strings de data para objetos datetime
- **`get_tournament_teams(df, tournament_id)`**: Obtém todos os times de um torneio
- **`calculate_expected_matches_per_round(n_teams)`**: Calcula número esperado de partidas por rodada

## Como Usar

### Uso Básico

```python
import pandas as pd
from tournament_matches.matchday import process_all_tournaments, generate_quality_report

# Carregar dados
df = pd.read_csv('football_matches.csv')

# Organizar em rodadas
organized_df = process_all_tournaments(df)

# Analisar qualidade
quality_report = generate_quality_report(organized_df, 'quality_report.md')

# Salvar resultado
organized_df.to_csv('matches_with_rounds.csv', index=False)
```

### Uso via Script Principal

```bash
# Executar o script principal
python src/5_matchdays.py data/football.csv output_with_rounds.csv

# Usar arquivos padrão
python src/5_matchdays.py
```

## Formato dos Dados

### Entrada Esperada

O DataFrame de entrada deve conter as seguintes colunas:

- **`id`**: Identificador do torneio (ex: "premier-league@/football/england/premier-league-2019-2020/")
- **`date`**: Data da partida (formato "dd.mm.yyyy" ou "yyyy-mm-dd")
- **`home`**: Time mandante
- **`away`**: Time visitante
- **`result`**: Resultado da partida (opcional)
- **`date number`**: Número sequencial da data (opcional)

### Saída Gerada

O DataFrame de saída inclui todas as colunas originais mais:

- **`round`**: Número da rodada (1, 2, 3, ... ou -1 para partidas não atribuídas)

## Algoritmo de Organização

1. **Agrupamento por Data**: As partidas são agrupadas por data
2. **Seleção Inteligente**: Para cada data, seleciona partidas sem conflito de times
3. **Formação de Rodadas**: Cria rodadas com o número ideal de partidas
4. **Tratamento de Conflitos**: Partidas que não podem ser atribuídas recebem `round = -1`

### Regras de Qualidade

- **Rodada Perfeita**: Tem o número esperado de partidas e nenhum conflito de times
- **Número Esperado de Partidas**:
  - N times pares: N/2 partidas por rodada
  - N times ímpares: (N-1)/2 partidas por rodada (1 time descansa)

## Métricas de Qualidade

- **Porcentagem de Rodadas Perfeitas**: % de rodadas que atendem aos critérios ideais
- **Partidas Não Atribuídas**: Número de partidas com `round = -1`
- **Torneios Perfeitos**: Torneios com 100% de rodadas perfeitas
- **Torneios Bons**: Torneios com 80%+ de rodadas perfeitas

## Exemplos

### Exemplo 1: Torneio com 4 Times

```
Times: A, B, C, D
Partidas por rodada: 2

Rodada 1: A vs B, C vs D
Rodada 2: A vs C, B vs D  
Rodada 3: A vs D, B vs C
```

### Exemplo 2: Torneio com 5 Times

```
Times: A, B, C, D, E
Partidas por rodada: 2 (1 time descansa)

Rodada 1: A vs B, C vs D (E descansa)
Rodada 2: A vs C, D vs E (B descansa)
Rodada 3: A vs D, B vs E (C descansa)
...
```

## Limitações

1. **Restrições Temporais**: Partidas são organizadas respeitando as datas originais
2. **Conflitos de Agenda**: Alguns jogos podem não ser atribuíveis devido a conflitos
3. **Dados Incompletos**: Torneios com dados inconsistentes podem ter qualidade reduzida

## Logs e Debugging

O módulo gera logs detalhados incluindo:

- Número de times e partidas por torneio
- Partidas não atribuídas
- Estatísticas de qualidade
- Erros de processamento

Logs são salvos em `matchday_organization.log` quando executado via script principal.

## Relatórios

O módulo gera relatórios em Markdown com:

- Estatísticas gerais
- Ranking de torneios por qualidade
- Análise detalhada de problemas
- Rodadas problemáticas específicas

## Desenvolvimento

### Executar Exemplos

```bash
python src/tournament_matches/matchday/example.py
```

### Estrutura de Testes

O módulo inclui exemplos que podem ser usados como testes básicos:

- Teste com dados sintéticos
- Teste com múltiplos torneios
- Teste com dados reais (se disponíveis)

### Extensões Futuras

- Algoritmos de otimização mais avançados
- Suporte a restrições customizadas
- Interface gráfica para visualização
- Integração com APIs de dados esportivos