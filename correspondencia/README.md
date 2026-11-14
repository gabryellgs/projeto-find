# Correspondência Automática entre Itens Perdidos e Encontrados

Experimento do TCC de Gabryell que avalia técnicas clássicas para sugerir, a partir de um item cadastrado como **perdido** no FIND, quais itens **encontrados** têm maior chance de ser o mesmo objeto.

## Instalação

```powershell
git clone https://github.com/gabryellgs/projeto-find.git
cd projeto-find
git checkout tcc-correspondencia
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install python-magic-bin
pip install -r correspondencia/requirements-tcc.txt
python -c "import nltk; nltk.download('stopwords')"
```

Crie o arquivo `.env` na raiz do projeto:

```
SECRET_KEY=chave-local-qualquer
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Dados

```powershell
python manage.py migrate
python manage.py criar_categorias
python manage.py gerar_dados --semente 42
```

As fotos tratadas já estão no repositório (`correspondencia/dados/fotos/`). O comando `gerar_dados` cria os itens perdidos, achados e o gabarito no banco.

## Avaliação

```powershell
python manage.py avaliar
python manage.py avaliar --tempo
```

Os resultados ficam em `correspondencia/resultados/`:

| Arquivo | Conteúdo |
|---|---|
| `metricas.csv` | Tabela principal: Recall@1, Recall@6 e MRR de cada estratégia |
| `posicoes.csv` | Posição do achado correto para cada par e cada estratégia |
| `robustez_variacao.csv` | Métricas separadas por grupo de variação (nenhuma, sinônimo, erro, sem acento) |
| `robustez_parecido.csv` | Métricas separadas por presença de objeto parecido no catálogo |
| `tempos.csv` | Tempo de preparação e consulta com ~1.000 candidatos |
| `graficos/metricas.png` | Gráfico de barras com as métricas de cada estratégia |
| `graficos/robustez.png` | Gráfico de barras com Recall@6 por variação |

## Sugestões

Para ver as 6 sugestões da estratégia F para um item perdido:

```powershell
python manage.py sugerir <id_do_perdido>
```

O `id` pode ser descoberto no `/admin/` ou em `posicoes.csv`.

## Testes

```powershell
pytest correspondencia
```

## Estratégias comparadas

| Código | Estratégia | O que compara |
|---|---|---|
| **B0** | Heurística atual do FIND (linha de base) | Categoria + palavras em comum |
| **T1** | TF-IDF com similaridade do cosseno (n-gramas de 3 a 5 letras) | Texto |
| **V** | pHash + histograma de cor HSV (50/50) | Foto |
| **F** | Combinação: 0,6 × T1 + 0,3 × V + 0,1 × categoria | Tudo |
| **F (sem foto)** | Combinação sem foto: (0,6 × T1 + 0,1 × categoria) / 0,7 | Texto + categoria |

## Computador usado

*(Preencha com o processador e a memória do computador em que os tempos foram medidos.)*

