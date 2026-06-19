from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class ArquivoMidia(models.Model):
    """Armazena arquivos de mídia (imagens) diretamente no banco de dados."""
    nome = models.CharField(max_length=255, unique=True, db_index=True)
    conteudo = models.BinaryField()
    content_type = models.CharField(max_length=100, default='image/jpeg')
    tamanho = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'arquivos_midia'
        verbose_name = 'Arquivo de Mídia'
        verbose_name_plural = 'Arquivos de Mídia'

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=45)
    descricao = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'mainpage_categoria'

    def __str__(self):
        return self.nome


class Item(models.Model):
    STATUS_CHOICES = [
        ('achado', 'Achado'),
        ('perdido', 'Perdido'),
        ('devolvido', 'Devolvido'),
        ('pendente_confirmacao', 'Pendente de Confirmação'),
        ('confirmado', 'Confirmado no Balcão'),
    ]

    titulo = models.CharField(max_length=45)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    descricao = models.CharField(max_length=200)
    status = models.CharField(max_length=45, choices=STATUS_CHOICES)
    local = models.CharField(max_length=45)
    data = models.DateField()
    imagem = models.ImageField(upload_to='itens/', blank=True, null=True)
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itens')
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'mainpage_item'

    def save(self, *args, **kwargs):
        if not self.slug:
            import uuid
            base_slug = slugify(self.titulo)
            random_suffix = str(uuid.uuid4())[:6]
            self.slug = f"{base_slug}-{random_suffix}"
        super().save(*args, **kwargs)
        self._gerar_image_hash()
        self._gerar_qrcode()

    def _gerar_image_hash(self):
        """Gera pHash da imagem para busca visual (compatível com DatabaseStorage)."""
        if not self.imagem:
            return
        try:
            import imagehash
            from PIL import Image as PILImage

            self.imagem.open('rb')
            img = PILImage.open(self.imagem)
            img.load()  # força leitura completa (importante para storage remoto)
            self.imagem.close()

            phash = str(imagehash.phash(img, hash_size=16))

            if self.image_hash != phash:
                Item.objects.filter(pk=self.pk).update(image_hash=phash)
                self.image_hash = phash
        except Exception:
            try:
                self.imagem.close()
            except Exception:
                pass

    def _gerar_qrcode(self):
        """Gera o QR Code para o item se ainda não existir e salva no banco de dados."""
        if not self.slug:
            return
        
        nome_qr = f"qr_{self.slug}.png"
        if ArquivoMidia.objects.filter(nome=nome_qr).exists():
            return

        try:
            import qrcode
            from io import BytesIO

            url = f"https://find.ifrn.edu.br/item/{self.slug}/"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            conteudo_png = buffer.getvalue()

            ArquivoMidia.objects.update_or_create(
                nome=nome_qr,
                defaults={
                    'conteudo': conteudo_png,
                    'content_type': 'image/png',
                    'tamanho': len(conteudo_png),
                }
            )
        except Exception:
            pass

    @staticmethod
    def buscar_por_imagem(imagem_file, limite=20):
        """
        Busca itens visualmente similares a uma imagem enviada.
        Se GEMINI_API_KEY estiver configurado nas configurações do Django, utiliza a API do Gemini
        para fazer uma busca semântica de última geração. Caso contrário, utiliza o algoritmo
        híbrido local (pHash + Histograma HSV).
        """
        from django.conf import settings
        import requests
        import base64
        from django.db.models import Q

        api_key = getattr(settings, 'GEMINI_API_KEY', '')

        # Se houver chave API do Gemini, faz a busca semântica inteligente
        if api_key:
            try:
                # 1. Converter a imagem para base64
                imagem_file.seek(0)
                img_base64 = base64.b64encode(imagem_file.read()).decode('utf-8')

                # 2. Chamar a API do Gemini 2.5 Flash
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                prompt = (
                    "Identifique o objeto principal desta imagem. Retorne apenas uma descrição curta "
                    "com o nome do objeto, cor principal e material em português. Exemplo: 'mochila preta de nylon'."
                )
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inlineData": {"mimeType": "image/jpeg", "data": img_base64}}
                        ]
                    }]
                }

                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    res = response.json()
                    descricao_ia = res['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # 3. Fazer a busca de texto baseada nas palavras-chave retornadas pela IA
                    # Remove palavras curtas (de, com, em, um, uma, o, a)
                    palavras = [p.lower() for p in descricao_ia.split() if len(p) > 2]
                    
                    if palavras:
                        query = Q()
                        for palavra in palavras:
                            query &= (
                                Q(titulo__icontains=palavra) |
                                Q(descricao__icontains=palavra) |
                                Q(local__icontains=palavra)
                            )
                        
                        itens_encontrados = Item.objects.filter(query).select_related('usuario', 'categoria')[:limite]
                        
                        # Calcula a similaridade textual baseada em quantas palavras-chave deram match
                        resultados = []
                        for item in itens_encontrados:
                            texto_item = f"{item.titulo} {item.descricao} {item.local}".lower()
                            matches = sum(1 for palavra in palavras if palavra in texto_item)
                            sim_txt = (matches / len(palavras)) * 100 if palavras else 100.0
                            resultados.append((item, round(sim_txt, 1)))
                        
                        resultados.sort(key=lambda x: x[1], reverse=True)
                        return resultados
            except Exception:
                pass # Se falhar a API por qualquer motivo, cai no fallback local

        # Fallback Local: Algoritmo Híbrido pHash + Histograma de Cores HSV
        import imagehash
        import numpy as np
        from PIL import Image as PILImage

        try:
            img_query = PILImage.open(imagem_file)
            query_hash = imagehash.phash(img_query, hash_size=16)
            
            img_query_hsv = img_query.convert('HSV')
            hist_query = np.array(img_query_hsv.histogram(), dtype=np.float32)
            sum_query = hist_query.sum()
            if sum_query > 0:
                hist_query /= sum_query
        except Exception:
            return []

        itens_com_hash = Item.objects.exclude(
            image_hash__isnull=True
        ).exclude(image_hash='').select_related('usuario', 'categoria')

        resultados = []
        for item in itens_com_hash:
            try:
                # 2. Calcular similaridade estrutural via pHash
                item_hash = imagehash.hex_to_hash(item.image_hash)
                distancia = query_hash - item_hash
                sim_hash = max(0, 100 - (distancia / 256 * 100))
                
                # 3. Calcular similaridade de cores via Histograma HSV
                if item.imagem:
                    try:
                        item.imagem.open('rb')
                        img_item = PILImage.open(item.imagem)
                        img_item_hsv = img_item.convert('HSV')
                        hist_item = np.array(img_item_hsv.histogram(), dtype=np.float32)
                        item.imagem.close()
                        
                        sum_item = hist_item.sum()
                        if sum_item > 0:
                            hist_item /= sum_item
                            
                        # Intersecção de histograma normalizado (0 a 100%)
                        sim_cor = float(np.minimum(hist_query, hist_item).sum()) * 100
                    except Exception:
                        sim_cor = 50.0  # fallback neutro caso dê erro ao ler imagem
                else:
                    sim_cor = 50.0
                
                # 4. Similaridade final combinada: 50% formato + 50% cor
                similaridade_final = (sim_hash * 0.5) + (sim_cor * 0.5)
                
                if similaridade_final >= 30:
                    resultados.append((item, round(similaridade_final, 1)))
            except Exception:
                try:
                    item.imagem.close()
                except Exception:
                    pass
                continue

        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:limite]

    def __str__(self):
        return self.titulo


class AcaoLog(models.Model):
    ACAO_CHOICES = [
        ('confirmou', 'Confirmou item no balcão'),
        ('devolveu', 'Registrou devolução'),
        ('editou', 'Editou item'),
        ('status_alterado', 'Alterou status'),
    ]
    bolsista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='acoes_log')
    item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, related_name='logs')
    acao = models.CharField(max_length=30, choices=ACAO_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)
    ip_origem = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'find_acaolog'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.bolsista} → {self.acao} em {self.item} ({self.timestamp})"
