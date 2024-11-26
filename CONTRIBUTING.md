# Contribuindo com o Store App

Obrigado por considerar contribuir com o Store App! Este documento fornece diretrizes e informações importantes para contribuir com o projeto.

## 🌟 Como Contribuir

1. **Fork o Repositório**
   - Faça um fork do repositório para sua conta
   - Clone o fork localmente

2. **Configure o Ambiente**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Crie uma Branch**
   ```bash
   git checkout -b feature/sua-feature
   ```

4. **Desenvolva**
   - Implemente sua feature ou correção
   - Adicione testes quando aplicável
   - Siga os padrões de código do projeto

5. **Teste**
   ```bash
   pytest
   coverage run -m pytest
   coverage report
   ```

6. **Commit**
   ```bash
   git add .
   git commit -m "feat: descrição da sua feature"
   ```

7. **Push e Pull Request**
   ```bash
   git push origin feature/sua-feature
   ```
   - Abra um Pull Request com descrição clara das mudanças

## 📝 Padrões de Código

### Python
- Siga o PEP 8
- Use type hints quando possível
- Docstrings em classes e funções importantes
- Nomes de variáveis descritivos

### HTML/Templates
- Indentação de 2 espaços
- IDs e classes em kebab-case
- Comentários para seções importantes

### JavaScript
- Use ES6+ quando possível
- Semicolons obrigatórios
- camelCase para variáveis e funções

## 🧪 Testes

- Escreva testes para novas features
- Mantenha cobertura acima de 80%
- Use fixtures do pytest
- Mock chamadas externas

## 📚 Documentação

- Atualize o README.md se necessário
- Documente novas features
- Atualize a documentação da API
- Inclua exemplos de uso

## 🐛 Reportando Bugs

1. Verifique se o bug já foi reportado
2. Use o template de issue para bugs
3. Inclua:
   - Passos para reproduzir
   - Comportamento esperado
   - Comportamento atual
   - Screenshots se aplicável
   - Ambiente (OS, Browser, etc)

## 💡 Sugerindo Features

1. Verifique se já não foi sugerida
2. Use o template de feature request
3. Explique o problema que resolve
4. Descreva a solução proposta
5. Considere alternativas

## 🔄 Processo de Review

- Dois aprovadores necessários
- CI deve passar
- Documentação atualizada
- Testes passando
- Código limpo e legível

## 📋 Checklist PR

- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Changelog atualizado
- [ ] Versão bumped
- [ ] CI passing
- [ ] Código revisado

## 🤝 Código de Conduta

- Seja respeitoso
- Aceite feedback construtivo
- Foque no que é melhor para a comunidade
- Mostre empatia com outros contribuidores

## 📜 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença MIT do projeto.
