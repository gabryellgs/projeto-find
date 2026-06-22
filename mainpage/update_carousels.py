import re

with open('/home/gabryell/Find-sitema/projeto_find/mainpage/templates/mainpage/menu.html', 'r') as f:
    content = f.read()

# We want to extract the "Itens Devolvidos" section to use as a template
match = re.search(r'(<!-- Itens devolvidos -->.*?)</section>', content, re.DOTALL)
template_section = match.group(1) + '</section>'

# Create the perdidos section
perdidos_section = template_section.replace('Itens Devolvidos', 'Objetos Perdidos')
perdidos_section = perdidos_section.replace('Devolvidos', 'Objetos Perdidos')
perdidos_section = perdidos_section.replace('itens_devolvidos', 'itens_perdidos')
perdidos_section = perdidos_section.replace('devolvidosSwiper', 'perdidosSwiper')
perdidos_section = perdidos_section.replace('Casos solucionados', 'Comunidade procurando')
perdidos_section = perdidos_section.replace('color: #185FA5;', 'color: #B32E29;')
perdidos_section = perdidos_section.replace('d-none d-md-block', 'd-none') # completely hide desktop version
perdidos_section = perdidos_section.replace('d-block d-md-none', 'd-block')
perdidos_section = perdidos_section.replace('<section class="section-pad" style="margin-top: 10px;">', '<section class="section-pad d-block d-md-none" style="margin-top: 10px;">')
perdidos_section = perdidos_section.replace('<!-- Itens devolvidos -->', '<!-- Itens perdidos (Mobile Only) -->')

# Create the achados section
achados_section = template_section.replace('Itens Devolvidos', 'Objetos Encontrados')
achados_section = achados_section.replace('Devolvidos', 'Objetos Encontrados')
achados_section = achados_section.replace('itens_devolvidos', 'itens_achados')
achados_section = achados_section.replace('devolvidosSwiper', 'achadosSwiper')
achados_section = achados_section.replace('Casos solucionados', 'Aguardando o dono legítimo')
achados_section = achados_section.replace('color: #185FA5;', 'color: #1F7A51;')
achados_section = achados_section.replace('d-none d-md-block', 'd-none') # completely hide desktop version
achados_section = achados_section.replace('d-block d-md-none', 'd-block')
achados_section = achados_section.replace('<section class="section-pad" style="margin-top: 10px;">', '<section class="section-pad d-block d-md-none" style="margin-top: 10px;">')
achados_section = achados_section.replace('<!-- Itens devolvidos -->', '<!-- Itens achados (Mobile Only) -->')

# Insert before "Itens devolvidos"
new_content = content.replace('<!-- Itens devolvidos -->', perdidos_section + '\n\n' + achados_section + '\n\n' + '<!-- Itens devolvidos -->')

# Update swiper initializations
new_content = new_content.replace("initSwiper('.devolvidosSwiper');", "initSwiper('.devolvidosSwiper');\n  initSwiper('.perdidosSwiper');\n  initSwiper('.achadosSwiper');")

with open('/home/gabryell/Find-sitema/projeto_find/mainpage/templates/mainpage/menu.html', 'w') as f:
    f.write(new_content)
