# Geração de Rodadas para Dados de Futebol

Este diretório contém scripts para gerar e analisar números de rodada para dados de futebol, considerando temporadas específicas de cada campeonato.

## Problema

O arquivo original `football.csv` contém jogos de futebol com um `date number` sequencial, mas sem números de rodada adequados. O objetivo é agrupar os jogos em rodadas onde:

1. **Cada time joga apenas uma vez por rodada**
2. **Cada temporada de cada campeonato tem suas próprias rodadas**
3. **Os dados são organizados por campeonato-temporada e rodada**

## Estrutura dos Dados

Os dados contêm jogos de 4 campeonatos com múltiplas temporadas:

- **Bundesliga** (Alemanha): 2015-2016 a 2020-2021
- **Serie A** (Itália): 2015-2016 a 2020-2021  
- **Serie A Betano** (Brasil): 2015 a 2021
- **Serie B Superbet** (Brasil): 2015 a 2021

**Total**: 9.436 jogos em 26 temporadas diferentes

## Scripts Disponíveis

### 1. `generate_rodadas_v3.py`

**Script principal** para gerar números de rodada considerando temporadas específicas.

**Características:**
- Extrai campeonato e temporada do campo `id`
- Processa cada temporada separadamente
- Garante que cada time jogue apenas uma vez por rodada
- Ordena jogos por `date number` e `date`
- Gera estatísticas detalhadas por temporada

**Uso:**
```bash
python src/rodadas/generate_rodadas_v3.py
```

**Saída:** `data/5_matchdays/football_rodadas_v3.csv`

### 2. `analise_rodadas_v3.py`

**Script de análise** para verificar a qualidade das rodadas geradas.

**Verificações:**
- Consistência das rodadas (sem times duplicados)
- Análise cronológica por temporada
- Estatísticas de jogos por rodada
- Exemplos das primeiras rodadas

**Uso:**
```bash
python src/rodadas/analise_rodadas_v3.py
```

### 3. `organize_final.py`

**Script de organização final** que ordena os dados por ID e rodada.

**Organização:**
1. Campeonato (alfabético)
2. Temporada (cronológica)
3. Rodada (numérica)
4. Date number (cronológica dentro da rodada)

**Uso:**
```bash
python src/rodadas/organize_final.py
```

**Saída:** `data/5_matchdays/football_rodadas_final.csv`

## Resultados

### Arquivo Final: `data/5_matchdays/football_rodadas_final.csv`

**Estrutura:**
```csv
id,date number,result,date,odds home,odds tie,odds away,winner,home,away,rodada,campeonato,temporada
```

**Características:**
- ✅ **9.436 jogos** processados
- ✅ **26 temporadas** de 4 campeonatos
- ✅ **Todas as rodadas consistentes** (nenhum time joga mais de uma vez por rodada)
- ✅ **Dados organizados** por campeonato → temporada → rodada
- ✅ **Rodadas específicas por temporada**

### Estatísticas por Campeonato-Temporada

| Campeonato-Temporada | Jogos | Rodadas | Período |
|---------------------|-------|---------|----------|
| bundesliga_2015-2016 | 306 | 34 | 2015-2016 |
| bundesliga_2016-2017 | 306 | 34 | 2016-2017 |
| ... | ... | ... | ... |
| serie-b-superbet_2021 | 380 | 47 | 2021 |

**Total de rodadas geradas:** Varia de 34 a 51 por temporada

## Validação

### ✅ Consistência das Rodadas
- **100% das rodadas são consistentes**
- Nenhum time aparece mais de uma vez por rodada
- Verificação automática em todas as 26 temporadas

### ✅ Organização dos Dados
- Dados corretamente ordenados por campeonato → temporada → rodada
- Ordem cronológica mantida dentro de cada rodada
- Estrutura facilita consultas por temporada específica

### ✅ Integridade dos Dados
- Todos os 9.436 jogos preservados
- Nenhum dado perdido durante o processamento
- Colunas originais mantidas + novas colunas adicionadas

## Como Usar o Arquivo Final

### Exemplo 1: Consultar jogos de uma temporada específica
```python
import pandas as pd

df = pd.read_csv('data/5_matchdays/football_rodadas_final.csv')

# Jogos da Bundesliga 2020-2021
bundesliga_2021 = df[
    (df['campeonato'] == 'bundesliga') & 
    (df['temporada'] == '2020-2021')
]

print(f"Jogos: {len(bundesliga_2021)}")
print(f"Rodadas: {bundesliga_2021['rodada'].max()}")
```

### Exemplo 2: Analisar uma rodada específica
```python
# Rodada 1 da Serie A 2020-2021
rodada_1 = df[
    (df['campeonato'] == 'serie-a') & 
    (df['temporada'] == '2020-2021') &
    (df['rodada'] == 1)
]

print("Jogos da Rodada 1:")
for _, jogo in rodada_1.iterrows():
    print(f"{jogo['home']} vs {jogo['away']} ({jogo['date']})")
```

### Exemplo 3: Estatísticas por campeonato
```python
# Resumo por campeonato
resumo = df.groupby(['campeonato', 'temporada']).agg({
    'rodada': ['count', 'max'],
    'date': ['min', 'max']
})

print(resumo)
```

## Melhorias Futuras

1. **Otimização cronológica**: Melhorar algoritmo para minimizar dispersão temporal dentro das rodadas
2. **Validação de calendário**: Verificar se as rodadas respeitam calendários oficiais dos campeonatos
3. **Análise de padrões**: Identificar padrões específicos de cada campeonato
4. **Interface gráfica**: Criar visualizações das rodadas geradas

## Arquivos de Entrada e Saída

### Entrada
- `data/3_filtered/football.csv` - Arquivo original com jogos

### Saída
- `data/5_matchdays/football_rodadas_v3.csv` - Dados com rodadas geradas
- `data/5_matchdays/football_rodadas_final.csv` - **Arquivo final organizado** ⭐

## Dependências

```bash
pip install pandas numpy
```

## Execução Completa

Para executar todo o processo:

```bash
# 1. Gerar rodadas
python src/rodadas/generate_rodadas_v3.py

# 2. Analisar qualidade
python src/rodadas/analise_rodadas_v3.py

# 3. Organizar arquivo final
python src/rodadas/organize_final.py
```

**Resultado:** Arquivo `data/5_matchdays/football_rodadas_final.csv` pronto para uso! 🎯