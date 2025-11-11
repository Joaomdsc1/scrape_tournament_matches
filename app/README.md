# 📊 Dashboard de Análise de Partidas e Classificações

Este é um dashboard interativo desenvolvido com Streamlit para análise de dados esportivos, especificamente focado em partidas de futebol e basquete.

## 🚀 Funcionalidades

### 🎯 Seleção de Dados
- **Esporte**: Escolha entre Football (Futebol) e Basketball (Basquete)
- **Liga**: Selecione a liga específica do esporte escolhido
- **Temporada**: Escolha a temporada desejada

### 🔍 Filtros Avançados
- **Período**: Filtre partidas por intervalo de datas
- **Time**: Filtre partidas por time específico (mandante ou visitante)

### 📊 Visualizações

#### 🏆 Classificação
- Tabela de classificação calculada automaticamente baseada nos resultados das partidas
- Inclui:
  - Posição na tabela
  - Número de jogos disputados
  - Vitórias, empates e derrotas
  - Gols marcados e sofridos
  - Saldo de gols
  - Pontos (3 por vitória, 1 por empate)

#### ⚽ Partidas
- Lista completa de todas as partidas da liga/temporada selecionada
- Informações incluídas:
  - Data da partida
  - Times (casa e fora)
  - Resultado
  - Odds (quando disponíveis)

### 📈 Métricas Principais
- Total de partidas
- Vitórias em casa
- Vitórias fora de casa
- Empates

### 📊 Gráfico de Distribuição
- **Gráfico de Pizza Interativo**: Visualização da distribuição de vitórias da casa, empates e vitórias fora
- **Cores Intuitivas**: 
  - Verde para vitórias da casa
  - Dourado para empates  
  - Azul para vitórias fora
- **Percentuais**: Exibição de estatísticas detalhadas com percentuais
- **Gráfico de Rosca**: Design moderno com espaço central

### 💾 Download de Dados
- Download da classificação em formato CSV
- Download das partidas em formato CSV

## 🛠️ Como Executar

1. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Executar o app**:
   ```bash
   cd app
   streamlit run app.py
   ```

3. **Acessar no navegador**:
   O app estará disponível em `http://localhost:8501`

## 📁 Estrutura de Dados

O app utiliza os seguintes arquivos de dados:
- `../data/formatted/football.csv` - Dados de partidas de futebol
- `../data/formatted/basketball.csv` - Dados de partidas de basquete

### Formato dos Dados
- **id**: Identificador único da liga/temporada
- **date**: Data da partida
- **home**: Time da casa
- **away**: Time visitante
- **result**: Resultado da partida (formato: "gols_casa:gols_fora")
- **winner**: Vencedor ('h' = casa, 'a' = fora, 'd' = empate)
- **odds home/away/tie**: Odds das casas de apostas

## 🎨 Interface

### Sidebar (Barra Lateral)
- Configurações principais
- Filtros avançados
- Seleção de esporte, liga e temporada

### Área Principal
- Métricas resumidas
- Gráfico de pizza com distribuição de resultados
- Tabela de classificação
- Lista de partidas
- Botões de download

## 🔧 Personalização

O app pode ser facilmente personalizado:

1. **Adicionar novos esportes**: Modifique a lista de esportes no código
2. **Novos filtros**: Adicione filtros na seção de sidebar
3. **Novas métricas**: Crie novas visualizações na área principal
4. **Estilo**: Personalize cores e layout usando CSS customizado

## 📝 Notas Técnicas

- **Cache de dados**: Utiliza `@st.cache_data` para melhor performance
- **Tratamento de erros**: Inclui validações e mensagens de erro informativas
- **Responsividade**: Interface adaptável para diferentes tamanhos de tela
- **Internacionalização**: Interface em português brasileiro

## 🤝 Contribuição

Para contribuir com melhorias:
1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Teste o app
5. Envie um pull request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 