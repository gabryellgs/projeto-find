from mainpage.views import _calcular_match_score

# Os mesmos status que o FIND usa para buscar candidatos (confira na view que você leu).
STATUS_CANDIDATOS = ["achado", "pendente_confirmacao", "confirmado"]


class Estrategia:
    """Forma comum de todas as estratégias."""

    nome = ""

    def preparar(self, candidatos):
        """Recebe todos os candidatos uma única vez (ex.: montar a matriz do TF-IDF)."""
        self.candidatos = list(candidatos)

    def pontuar(self, perdido):
        """Devolve {id_do_candidato: pontuação de 0 a 1}."""
        raise NotImplementedError


class B0(Estrategia):
    nome = "B0"

    def pontuar(self, perdido):
        # A pontuação do FIND vai de 0 a 100; aqui ela é dividida por 100.
        return {c.id: _calcular_match_score(perdido, c) / 100 for c in self.candidatos}